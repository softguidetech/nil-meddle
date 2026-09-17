# -*- coding: utf-8 -*-

from odoo import fields, models


class TrainingCourse(models.Model):
    _inherit = 'training.course'

    snapshot_lcp_learning_partner = fields.Char(
        string='Snapshot Learning Partner',
        copy=False,
        readonly=True,
    )
    snapshot_lcp_revenue = fields.Float(
        string='Snapshot Training Revenue',
        copy=False,
        readonly=True,
    )
    snapshot_lcp_rate_card = fields.Float(
        string='Snapshot Rate Card',
        copy=False,
        readonly=True,
    )
    snapshot_lcp_partner_share = fields.Float(
        string='Snapshot Partner Share',
        copy=False,
        readonly=True,
    )
    snapshot_lcp_logistics = fields.Float(
        string='Snapshot Logistics',
        copy=False,
        readonly=True,
    )
    snapshot_lcp_total_costs = fields.Float(
        string='Snapshot Total Costs',
        copy=False,
        readonly=True,
    )
    snapshot_lcp_profit = fields.Float(
        string='Snapshot NIL ME Profit',
        copy=False,
        readonly=True,
    )

    def _nil_snapshot_vals(self):
        values = super()._nil_snapshot_vals()
        self.ensure_one()

        # Always freeze the commercial result from the original CRM training,
        # not from an intermediate SO/PO snapshot whose lead relation is empty.
        source = self.source_training_course_id or self

        values.update({
            'snapshot_lcp_learning_partner': (
                source.lcp_cost_learning_partner or ''
            ),
            'snapshot_lcp_revenue': source.price or 0.0,
            'snapshot_lcp_rate_card': source.lcp_total_rate_card or 0.0,
            'snapshot_lcp_partner_share': source.lcp_partner_share or 0.0,
            'snapshot_lcp_logistics': source.lcp_total_logistics or 0.0,
            'snapshot_lcp_total_costs': source.lcp_total_costs or 0.0,
            'snapshot_lcp_profit': source.lcp_nilme_profit or 0.0,
        })
        return values
