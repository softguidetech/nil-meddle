# -*- coding: utf-8 -*-
"""Original sales-order details for Professional Services down-payment PDFs.

Read-only: these source items must never become billable invoice lines.
"""

from odoo import models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _nil_downpayment_source_sale_lines(self):
        """Show SO items for a pure down-payment invoice, without billing them."""
        self.ensure_one()
        empty = self.env['sale.order.line']

        if self.move_type != 'out_invoice':
            return empty

        # Odoo 17's advance-payment wizard marks invoice rows as down payments.
        # Do not add a reference for normal/final invoices or mixed invoices.
        billed_lines = self.invoice_line_ids.sudo().filtered(
            lambda line: line.display_type == 'product'
        )
        if not billed_lines or any(not line.is_downpayment for line in billed_lines):
            return empty

        # Preferred: exact accounting line -> sale order line relationship.
        sale_lines = billed_lines.mapped('sale_line_ids')
        if sale_lines and any(not line.is_downpayment for line in sale_lines):
            return empty
        orders = sale_lines.mapped('order_id')

        # Safe fallback for legacy/custom invoices with missing sale_line_ids:
        # match a single explicit SO origin, same company and customer.
        if not orders and self.invoice_origin:
            origin = self.invoice_origin.strip()
            if ',' not in origin:
                orders = self.env['sale.order'].sudo().search([
                    ('name', '=', origin),
                    ('company_id', '=', self.company_id.id),
                    ('partner_id.commercial_partner_id', '=',
                     self.partner_id.commercial_partner_id.id),
                ], limit=1)

        if not orders:
            return empty

        # Avoid showing the content of a different commercial customer's order.
        if any(
            order.company_id != self.company_id
            or order.partner_id.commercial_partner_id != self.partner_id.commercial_partner_id
            for order in orders
        ):
            return empty

        return orders.mapped('order_line').filtered(
            lambda line: not line.display_type and not line.is_downpayment
        ).sorted(key=lambda line: (line.order_id.id, line.sequence, line.id))
