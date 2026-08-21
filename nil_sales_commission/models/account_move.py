from odoo import models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _nil_related_commission_leads(self):
        """CRM leads linked to these invoices through their Sale Order lines."""
        invoices = self.filtered(lambda move: move.move_type == 'out_invoice')
        sale_orders = invoices.mapped('invoice_line_ids.sale_line_ids.order_id')
        return sale_orders.mapped('opportunity_id')

    def action_post(self):
        result = super().action_post()

        # Commission becomes due only when a customer invoice is actually POSTED.
        leads = self._nil_related_commission_leads()
        if leads:
            leads._sync_sales_commission()

        return result

    def button_draft(self):
        leads = self._nil_related_commission_leads()
        result = super().button_draft()

        # If this was the last posted invoice for the lead, its pending
        # commission is cancelled automatically.
        if leads:
            leads._sync_sales_commission()

        return result

    def button_cancel(self):
        leads = self._nil_related_commission_leads()
        result = super().button_cancel()

        if leads:
            leads._sync_sales_commission()

        return result
