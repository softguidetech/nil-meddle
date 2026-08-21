from datetime import date

from odoo import api, models


COMMISSION_CUTOFF_DATE = date(2026, 5, 31)


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _nil_get_commission_sale_orders(self):
        self.ensure_one()
        return self.invoice_line_ids.sale_line_ids.order_id

    def _nil_get_commission_lead(self):
        self.ensure_one()
        leads = self._nil_get_commission_sale_orders().mapped('opportunity_id')
        return leads[:1]

    def _nil_get_commission_salesperson(self):
        """
        If the invoice is linked to a CRM Lead, the CURRENT salesperson
        on the Lead is always the source of truth.

        The invoice salesperson is used only when there is no linked Lead.

        This means changing the salesperson on the Lead updates the
        commission without changing the invoice itself.
        """
        self.ensure_one()

        lead = self._nil_get_commission_lead()

        if lead:
            return lead.user_id or self.env['res.users']

        if self.invoice_user_id:
            return self.invoice_user_id

        sale_orders = self._nil_get_commission_sale_orders()
        if sale_orders and sale_orders[0].user_id:
            return sale_orders[0].user_id

        return self.env['res.users']

    def _nil_is_allowed_commission_salesperson(self):
        self.ensure_one()

        salesperson = self._nil_get_commission_salesperson()
        if not salesperson:
            return False

        Commission = self.env['nil.sales.commission']
        return Commission._nil_is_allowed_salesperson(salesperson)

    def _nil_is_commission_eligible(self):
        self.ensure_one()

        return bool(
            self.move_type == 'out_invoice'
            and self.state == 'posted'
            and self.invoice_date
            and self.invoice_date > COMMISSION_CUTOFF_DATE
            and self.amount_untaxed > 0
            and self._nil_get_commission_salesperson()
            and self._nil_is_allowed_commission_salesperson()
        )

    def _nil_sync_sales_commission(self):
        """
        Create/update one commission row per eligible posted customer invoice.

        Invoice fields stay fixed:
        - Invoice
        - Invoice Date
        - Invoice Value
        - Currency

        Lead-driven fields stay dynamic:
        - Salesperson
        - Customer
        - Commission %
        - Commission Amount

        Approved rates:
        - Ruba Khattam = 1.5%
        - Loudy Abdo = 5%
        - Baraa Abo Saleh = 2%

        If the linked Lead salesperson changes, the commission row is
        recalculated using the SAME invoice value.

        Paid commissions remain locked because they already have a posted
        accounting entry.
        """
        Commission = self.env['nil.sales.commission'].sudo()

        for invoice in self:
            if invoice.move_type != 'out_invoice':
                continue

            commission = Commission.search([
                ('invoice_id', '=', invoice.id),
            ], limit=1)

            if not invoice._nil_is_commission_eligible():
                # Keep paid historical records untouched.
                # Remove unpaid rows if the current Lead salesperson is no
                # longer one of the approved commission salespeople.
                if commission and commission.state != 'paid':
                    commission.unlink()
                continue

            salesperson = invoice._nil_get_commission_salesperson()
            lead = invoice._nil_get_commission_lead()
            invoice_value = float(invoice.amount_untaxed or 0.0)

            commission_rate = Commission._nil_get_commission_rate(
                salesperson
            )

            values = {
                'invoice_id': invoice.id,
                'lead_id': lead.id if lead else False,
                'salesperson_id': salesperson.id,
                'customer_id': (
                    lead.partner_id.id
                    if lead and lead.partner_id
                    else invoice.partner_id.id
                    if invoice.partner_id
                    else False
                ),
                'company_id': invoice.company_id.id,
                'currency_id': invoice.currency_id.id,
                'training_value': invoice_value,
                'commission_rate': commission_rate,
                'commission_amount': (
                    invoice_value * (commission_rate / 100.0)
                ),
                'commission_date': invoice.invoice_date,
            }

            if commission:
                if commission.state == 'paid':
                    continue

                if commission.state == 'cancelled':
                    values['state'] = 'pending'

                commission.write(values)

            else:
                values['state'] = 'pending'
                Commission.create(values)

        return True

    @api.model
    def _nil_backfill_sales_commissions(self):
        """
        Backfill all eligible posted customer invoices dated after 31-May-2026.

        The CURRENT salesperson on the related CRM Lead is used, so upgrading
        the module also refreshes existing pending commission rows.
        """
        Commission = self.env['nil.sales.commission'].sudo()
        Commission._nil_prepare_invoice_commission_migration()

        # Remove unpaid rows currently assigned to people outside the
        # approved commission list.
        non_paid_commissions = Commission.search([
            ('state', '!=', 'paid'),
        ])

        disallowed = non_paid_commissions.filtered(
            lambda rec: not Commission._nil_is_allowed_salesperson(
                rec.salesperson_id
            )
        )

        if disallowed:
            disallowed.unlink()

        invoices = self.sudo().search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('invoice_date', '>', COMMISSION_CUTOFF_DATE),
            ('amount_untaxed', '>', 0),
        ])

        invoices._nil_sync_sales_commission()
        return True

    def action_post(self):
        result = super().action_post()
        self._nil_sync_sales_commission()
        return result

    def write(self, vals):
        result = super().write(vals)

        tracked_fields = {
            'state',
            'invoice_date',
            'invoice_user_id',
            'partner_id',
            'currency_id',
        }

        if tracked_fields.intersection(vals):
            self.filtered(
                lambda move: move.move_type == 'out_invoice'
            )._nil_sync_sales_commission()

        return result

    def button_draft(self):
        result = super().button_draft()
        self.filtered(
            lambda move: move.move_type == 'out_invoice'
        )._nil_sync_sales_commission()
        return result

    def button_cancel(self):
        result = super().button_cancel()
        self.filtered(
            lambda move: move.move_type == 'out_invoice'
        )._nil_sync_sales_commission()
        return result
