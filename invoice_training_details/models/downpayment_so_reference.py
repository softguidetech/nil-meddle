# -*- coding: utf-8 -*-
"""Original order details for Professional Services down-payment PDFs.

All lookups are read-only. No extra accounting or billable invoice lines.
"""

from odoo import models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _nil_downpayment_source_sale_orders(self):
        """Identify the originating SO only for a pure down-payment invoice."""
        self.ensure_one()
        empty = self.env['sale.order']

        if self.move_type != 'out_invoice':
            return empty

        # The Odoo 17 advance-payment wizard marks its accounting invoice
        # product lines as is_downpayment=True, independent of PDF layout.
        billed_lines = self.invoice_line_ids.sudo().filtered(
            lambda line: line.display_type == 'product'
        )
        if not billed_lines or any(not line.is_downpayment for line in billed_lines):
            return empty

        # Prefer the actual invoice-line -> SO-line relation.
        linked_so_lines = billed_lines.mapped('sale_line_ids')
        if linked_so_lines and any(not line.is_downpayment for line in linked_so_lines):
            return empty
        orders = linked_so_lines.mapped('order_id')

        # Fallback when older invoices lack the M2M relation. The invoice
        # must explicitly name ONE sales order of the same company/customer.
        if not orders and self.invoice_origin:
            origin = self.invoice_origin.strip()
            if ',' not in origin:
                orders = self.env['sale.order'].sudo().search([
                    ('name', '=', origin),
                    ('company_id', '=', self.company_id.id),
                    ('partner_id.commercial_partner_id', '=',
                     self.partner_id.commercial_partner_id.id),
                ], limit=1)

        if not orders or any(
            order.company_id != self.company_id
            or order.partner_id.commercial_partner_id != self.partner_id.commercial_partner_id
            for order in orders
        ):
            return empty

        return orders

    def _nil_downpayment_source_sale_lines(self):
        """Return standard SO item lines; exclude down-payment lines."""
        self.ensure_one()
        return self._nil_downpayment_source_sale_orders().mapped('order_line').filtered(
            lambda line: not line.display_type and not line.is_downpayment
        ).sorted(key=lambda line: (line.order_id.id, line.sequence, line.id))

    def _nil_downpayment_source_pro_services(self):
        """Return professional-service items from the ORIGINAL sale order."""
        self.ensure_one()
        return self._nil_downpayment_source_sale_orders().mapped('pro_service_ids').sorted(
            key=lambda service: service.id
        )
