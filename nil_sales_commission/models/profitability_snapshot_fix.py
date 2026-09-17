# -*- coding: utf-8 -*-

from odoo import api, models


class SalesCommission(models.Model):
    _inherit = 'nil.sales.commission'

    @api.depends(
        'invoice_id',
        'invoice_id.training_course_ids',
        'invoice_id.training_course_ids.lcp_cost_learning_partner',
        'invoice_id.training_course_ids.lcp_total_costs',
        'invoice_id.training_course_ids.lcp_nilme_profit',
        'invoice_id.training_course_ids.price',
        'lead_id',
        'lead_id.training_course_ids',
        'lead_id.training_course_ids.lcp_cost_learning_partner',
        'lead_id.training_course_ids.lcp_total_costs',
        'lead_id.training_course_ids.lcp_nilme_profit',
        'lead_id.training_course_ids.price',
    )
    def _compute_profit_margin_summary(self):
        """
        Prefer the invoice's independent training snapshot.

        Older invoices without snapshots fall back to the CRM training rows.
        Posted invoice snapshots are locked, so historical profitability no
        longer changes when somebody edits the CRM training later.
        """
        for rec in self:
            invoice_courses = (
                rec.invoice_id.sudo().training_course_ids
                if rec.invoice_id
                else self.env['training.course']
            )
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
