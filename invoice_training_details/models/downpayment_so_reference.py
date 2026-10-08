# -*- coding: utf-8 -*-
"""Read-only original order lines for down-payment invoice PDF references."""

from odoo import models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _nil_downpayment_source_sale_lines(self):
        """Return original SO items only for a *pure* down-payment invoice.

        Never generate invoice/account.move.line records from these items:
        they are informational and must not alter the invoiced balance or tax.
        """
        self.ensure_one()
        empty = self.env['sale.order.line']
        if self.move_type != 'out_invoice':
            return empty

        # The core sale.advance.payment.inv wizard creates invoice lines
        # linked to sale.order.line records with is_downpayment=True.
        billed_lines = self.invoice_line_ids.filtered(
            lambda line: line.display_type == 'product'
        )
        if not billed_lines:
            return empty

        linked_lines = billed_lines.sudo().mapped('sale_line_ids')
        if (
            not linked_lines
            or any(
                not line.sale_line_ids
                or any(not so_line.is_downpayment for so_line in line.sale_line_ids)
                for line in billed_lines
            )
        ):
            return empty

        orders = linked_lines.mapped('order_id')
        original_lines = orders.mapped('order_line').filtered(
            lambda line: not line.display_type and not line.is_downpayment
        )
        return original_lines.sorted(
            key=lambda line: (line.order_id.id, line.sequence, line.id)
        )
