from datetime import date

from odoo import api, models


COMMISSION_CUTOFF_DATE = date(2026, 5, 31)


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _nil_get_commission_sale_orders(self):
        """
        Find every Sale Order related to the invoice.

        Primary link:
            invoice line -> sale line -> sale order

        Fallback:
            invoice_origin -> sale.order.name

        The fallback is important for older/custom invoices where the
        invoice was created from a quotation/order but the sale_line_ids
        relation is missing.
        """
        self.ensure_one()

        SaleOrder = self.env['sale.order'].sudo()

        orders = self.invoice_line_ids.sale_line_ids.order_id

        origin = (self.invoice_origin or '').strip()

        if origin:
            # Typical Odoo invoice_origin values are:
            # S00001
            # S00001, S00002
            origin_names = [
                value.strip()
                for value in origin.split(',')
                if value.strip()
            ]

            if origin_names:
                orders |= SaleOrder.search([
                    ('name', 'in', origin_names),
                ])

            # Extra fallback for custom origin formatting.
            # Search only when the exact-name lookup did not find anything.
            if not orders:
                orders |= SaleOrder.search([
                    ('name', '=', origin),
                ])

        return orders

    def _nil_get_commission_lead(self):
        """
        Return the CRM Lead linked to the invoice through its Sale Order.

        If a commission row already exists and already knows its Lead,
        preserve that link as a fallback.
        """
        self.ensure_one()

        leads = self._nil_get_commission_sale_orders().mapped(
            'opportunity_id'
        )

        if leads:
            return leads[:1]

        existing_commission = self.env[
            'nil.sales.commission'
        ].sudo().search([
            ('invoice_id', '=', self.id),
            ('lead_id', '!=', False),
        ], limit=1)

        return existing_commission.lead_id if existing_commission else self.env['crm.lead']

    def _nil_get_commission_salesperson(self):
        """
        Salesperson priority:

        1. CURRENT salesperson on the linked CRM Lead.
        2. Invoice Salesperson.
        3. Sale Order Salesperson.

        This keeps the invoice itself fixed while allowing Lead salesperson
        changes to update pending commission rows.
        """
        self.ensure_one()

        lead = self._nil_get_commission_lead()

        if lead and lead.user_id:
            return lead.user_id

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

        return self.env[
            'nil.sales.commission'
        ]._nil_is_allowed_salesperson(
            salesperson
        )

    def _nil_is_commission_eligible(self):
        """
        Eligible invoices:

        - Customer Invoice only
        - Draft OR Posted (only Cancelled invoices are excluded)
        - Invoice Date from 01-Jun-2026 onward
        - Positive untaxed amount
        - Salesperson is one of the approved commission users
        """
        self.ensure_one()

        return bool(
            self.move_type == 'out_invoice'
            and self.state != 'cancel'
            and self.invoice_date
            and self.invoice_date > COMMISSION_CUTOFF_DATE
            and self.amount_untaxed > 0
            and self._nil_get_commission_salesperson()
            and self._nil_is_allowed_commission_salesperson()
        )

    def _nil_sync_sales_commission(self):
        """
        Create/update one commission row per eligible customer invoice.

        Fixed from Invoice:
        - Invoice reference
        - Invoice Date
        - Invoice Value excluding tax
        - Currency

        Dynamic from current Lead:
        - Salesperson
        - Customer
        - Commission %
        - Commission Amount

        Rates:
        - Ruba Khattam = 1.5%
        - Loudy Abdo = 5%
        - Baraa Abo Saleh = 2%
        """
        Commission = self.env[
            'nil.sales.commission'
        ].sudo()

        for invoice in self:

            if invoice.move_type != 'out_invoice':
                continue

            commission = Commission.search([
                ('invoice_id', '=', invoice.id),
            ], limit=1)

            if not invoice._nil_is_commission_eligible():

                if commission and commission.state != 'paid':
                    commission.unlink()

                continue

            salesperson = (
                invoice._nil_get_commission_salesperson()
            )

            lead = invoice._nil_get_commission_lead()

            invoice_value = float(
                invoice.amount_untaxed or 0.0
            )

            commission_rate = (
                Commission._nil_get_commission_rate(
                    salesperson
                )
            )

            values = {
                'invoice_id': invoice.id,
                'lead_id': (
                    lead.id
                    if lead
                    else False
                ),
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
                    invoice_value
                    * (commission_rate / 100.0)
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
        Re-scan ALL non-cancelled customer invoices from 01-Jun-2026 onward.

        This is deliberately invoice-first. It does not require a commission
        row to already exist.

        For each invoice, the code tries:
        1. Sale-line link to Sale Order
        2. invoice_origin to Sale Order
        3. Lead salesperson
        4. Invoice salesperson
        5. Sale Order salesperson
        """
        Commission = self.env[
            'nil.sales.commission'
        ].sudo()

        Commission._nil_prepare_invoice_commission_migration()

        invoices = self.sudo().search([
            ('move_type', '=', 'out_invoice'),
            ('state', '!=', 'cancel'),
            ('invoice_date', '>', COMMISSION_CUTOFF_DATE),
            ('amount_untaxed', '>', 0),
        ])

        invoices._nil_sync_sales_commission()

        # Clean unpaid commissions that no longer qualify after the full scan.
        non_paid_commissions = Commission.search([
            ('state', '!=', 'paid'),
            ('invoice_id', '!=', False),
        ])

        for commission in non_paid_commissions:
            if not commission.invoice_id._nil_is_commission_eligible():
                commission.unlink()

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
            'invoice_origin',
        }

        if tracked_fields.intersection(vals):

            self.filtered(
                lambda move:
                    move.move_type == 'out_invoice'
            )._nil_sync_sales_commission()

        return result

    def button_draft(self):
        result = super().button_draft()

        self.filtered(
            lambda move:
                move.move_type == 'out_invoice'
        )._nil_sync_sales_commission()

        return result

    def button_cancel(self):
        result = super().button_cancel()

        self.filtered(
            lambda move:
                move.move_type == 'out_invoice'
        )._nil_sync_sales_commission()

        return result
