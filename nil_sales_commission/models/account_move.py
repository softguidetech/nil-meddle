from datetime import date

from odoo import api, models


COMMISSION_CUTOFF_DATE = date(2026, 5, 31)
COMMISSION_RATE = 5.0

# Commission is created ONLY for these salespeople.
# Matching is case-insensitive and ignores extra spaces.
ALLOWED_COMMISSION_SALESPERSONS = {
    'ruba khattam',
    'loudy abdo',
    'baraa',
}


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
        """
        Commission is allowed ONLY for:
        - Ruba Khattam
        - Loudy Al Abdo
        - Baraa Abo Saleh
        """
        self.ensure_one()

        salesperson = self._nil_get_commission_salesperson()
        if not salesperson:
            return False

        salesperson_name = (salesperson.name or '').strip().lower()
        return salesperson_name in ALLOWED_COMMISSION_SALESPERSONS

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

        Eligibility:
        - Customer Invoice only (out_invoice)
        - Posted
        - Invoice Date strictly after 31-May-2026
        - Positive untaxed invoice value
        - Salesperson must be one of:
            Ruba Khattam
            Loudy Abdo
            Baraa

        Commission:
        - 5% of invoice amount excluding VAT/tax
        - Pending until manually marked Paid
        """
        Commission = self.env['nil.sales.commission'].sudo()

        for invoice in self:
            if invoice.move_type != 'out_invoice':
                continue

            commission = Commission.search([
                ('invoice_id', '=', invoice.id),
            ], limit=1)

            if not invoice._nil_is_commission_eligible():
                # Remove non-paid commission rows that are no longer eligible.
                # Paid rows are preserved because they may already have posted
                # accounting entries and must remain as historical records.
                if commission and commission.state != 'paid':
                    commission.unlink()
                continue

            salesperson = invoice._nil_get_commission_salesperson()
            lead = invoice._nil_get_commission_lead()
            invoice_value = float(invoice.amount_untaxed or 0.0)

            values = {
                'invoice_id': invoice.id,
                'lead_id': lead.id if lead else False,
                'salesperson_id': salesperson.id,
                'customer_id': invoice.partner_id.id if invoice.partner_id else False,
                'company_id': invoice.company_id.id,
                'currency_id': invoice.currency_id.id,
                'training_value': invoice_value,
                'commission_rate': COMMISSION_RATE,
                'commission_amount': invoice_value * (COMMISSION_RATE / 100.0),
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
        Backfill existing posted customer invoices dated after 31-May-2026,
        but ONLY for the three approved salespeople.

        Also removes any non-paid commission rows belonging to other
        salespeople so the commission ledger stays clean.
        """
        Commission = self.env['nil.sales.commission'].sudo()
        Commission._nil_prepare_invoice_commission_migration()

        # Clean up previously generated non-paid commissions for people
        # outside the approved list.
        non_paid_commissions = Commission.search([
            ('state', '!=', 'paid'),
        ])

        disallowed_commissions = non_paid_commissions.filtered(
            lambda rec: (rec.salesperson_id.name or '').strip().lower()
            not in ALLOWED_COMMISSION_SALESPERSONS
        )

        if disallowed_commissions:
            disallowed_commissions.unlink()

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
