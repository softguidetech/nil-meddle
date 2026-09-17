# -*- coding: utf-8 -*-

from odoo import api, models


class SalesCommission(models.Model):
    _inherit = 'nil.sales.commission'

    @api.depends(
        'invoice_id',
        'invoice_id.training_course_ids',
        'invoice_id.training_course_ids.source_training_course_id',
        'invoice_id.training_course_ids.snapshot_lcp_learning_partner',
        'invoice_id.training_course_ids.snapshot_lcp_revenue',
        'invoice_id.training_course_ids.snapshot_lcp_total_costs',
        'invoice_id.training_course_ids.snapshot_lcp_profit',
        'lead_id',
        'lead_id.training_course_ids',
        'lead_id.training_course_ids.lcp_cost_learning_partner',
        'lead_id.training_course_ids.lcp_total_costs',
        'lead_id.training_course_ids.lcp_nilme_profit',
        'lead_id.training_course_ids.price',
    )
    def _compute_profit_margin_summary(self):
        """
        Use frozen invoice LCP values when an independent snapshot exists.
        Old invoices without snapshots still fall back to the live CRM LCP.
        """
        for rec in self:
            invoice_courses = (
                rec.invoice_id.sudo().training_course_ids
                if rec.invoice_id
                else self.env['training.course']
            )

            snapshot_courses = invoice_courses.filtered(
                'source_training_course_id'
            )

            if snapshot_courses:
                partners = sorted(
                    set(snapshot_courses.mapped(
                        'snapshot_lcp_learning_partner'
                    )) - {False, ''}
                )
                revenue = sum(snapshot_courses.mapped(
                    'snapshot_lcp_revenue'
                ))
                costs = sum(snapshot_courses.mapped(
                    'snapshot_lcp_total_costs'
                ))
                profit = sum(snapshot_courses.mapped(
                    'snapshot_lcp_profit'
                ))
            else:
                courses = (
                    invoice_courses
                    or rec.lead_id.sudo().training_course_ids
                )
                partners = sorted(
                    set(courses.mapped('lcp_cost_learning_partner'))
                    - {False, ''}
                )
                revenue = sum(courses.mapped('price'))
                costs = sum(courses.mapped('lcp_total_costs'))
                profit = sum(courses.mapped('lcp_nilme_profit'))

            rec.profit_learning_partner = ', '.join(partners)
            rec.profit_total_costs = costs
            rec.profit_nilme_share = profit
            rec.profit_margin_pct = (
                profit / revenue
                if revenue
                else 0.0
            )
