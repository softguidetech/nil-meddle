# -*- coding: utf-8 -*-

from odoo import api, models


class SalesCommission(models.Model):
    _inherit = 'nil.sales.commission'

    @api.model
    def _nil_get_fixed_salesperson_rate(self, salesperson):
        """Return the fixed automatic rate for the actual Odoo salesperson name."""
        if not salesperson:
            return 0.0

        name = self._nil_normalize_name(salesperson.name)

        # Loudy is stored in Odoo as "Loudy Al Abdo". Keep common spelling
        # variants so an existing user-name variation does not silently drop
        # the salesperson commission row.
        if name.startswith('loudy ') or name.startswith('lody '):
            return 5.0

        # Baraa keeps the fixed 2% rate regardless of the surname spelling
        # used on the Odoo user record.
        if name == 'baraa' or name.startswith('baraa '):
            return 2.0

        return 0.0


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _nil_get_deal_salesperson(self):
        """
        Commission owner priority:
        1. Invoice Salesperson
        2. CRM Lead Salesperson
        3. Sale Order Salesperson

        The posted invoice is the authoritative commission document, so its
        Salesperson must not be overridden by a stale CRM Lead assignment.
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
