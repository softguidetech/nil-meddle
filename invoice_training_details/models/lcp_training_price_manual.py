# -*- coding: utf-8 -*-

from odoo import api, models


class TrainingCourse(models.Model):
    _inherit = 'training.course'

    def _lcp_sync_clc_price_to_rate_card(self):
        """Fill CLC Training Price from Total Rate Card only when Price is blank."""
        for line in self.filtered(
            lambda rec: rec.payment_method == 'clc' and not rec.price
        ):
            total_rate_card = (
                (line.lcp_rate_card_per_seat or 0.0)
                * max(line.no_of_student or 0, 0)
            )
            if total_rate_card:
                line.with_context(skip_lcp_clc_price_sync=True).write({
                    'price': total_rate_card,
                })

    @api.onchange('payment_method', 'no_of_student', 'lcp_rate_card_per_seat')
    def _onchange_lcp_clc_price_to_rate_card(self):
        for line in self:
            if line.payment_method == 'clc' and not line.price:
                line.price = (
                    (line.lcp_rate_card_per_seat or 0.0)
                    * max(line.no_of_student or 0, 0)
                )
