# -*- coding: utf-8 -*-

from odoo import api, models


class SalesCommission(models.Model):
    _inherit = 'nil.sales.commission'

    @api.model
    def _nil_get_fixed_salesperson_rate(self, salesperson):
        """
        Every invoice salesperson gets an automatic commission row.

        Eligibility is NOT name-based. The salesperson comes from the invoice.
        Baraa keeps the previously agreed 2% exception; every other salesperson
        gets the standard 5% rate.
        """
        if not salesperson:
            return 0.0

        name = self._nil_normalize_name(salesperson.name)
        if name == 'baraa' or name.startswith('baraa '):
            return 2.0

        return 5.0


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _nil_get_deal_salesperson(self):
        """
        Commission owner priority:
        1. Invoice Salesperson
        2. CRM Lead Salesperson only as a fallback
        3. Sale Order Salesperson only as a fallback

        No salesperson name controls whether an invoice receives commission.
        """
        self.ensure_one()

        invoice = self.sudo()

        if invoice.invoice_user_id:
            return invoice.invoice_user_id.sudo()

        lead = invoice._nil_get_commission_lead().sudo()
        if lead and lead.user_id:
            return lead.user_id.sudo()

        orders = invoice._nil_get_commission_sale_orders().sudo()
        if orders and orders[0].user_id:
            return orders[0].user_id.sudo()

        return self.env['res.users']
