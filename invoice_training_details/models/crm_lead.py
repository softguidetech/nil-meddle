# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class Lead(models.Model):
    _inherit = 'crm.lead'

    training_name = fields.Char(string='Training Name')
    total_training_price = fields.Float(string='Total Training Price', compute="_compute_training_price", store=True)
    half_advance_payment_before = fields.Float(string='Advance payment amount 50% (paid)')
    half_payment_after = fields.Float(string='50% Amount after Training Delivery (Not Yet Paid)')
    training_course_ids = fields.One2many('training.course', 'lead_id', string='Training Courses')

    # extra information tab
    clcs_qty = fields.Float(string='CLCs Qty')
    so_no = fields.Char(string='SO#')
    tr_expiry_date = fields.Date(string='Expiry Date')

    # logistics tab
    instructor_logistics = fields.Char(string='Instructor Logistics')
    catering = fields.Char(string='Catering')

    @api.depends('training_course_ids.price')
    def _compute_training_price(self):
        for rec in self:
            rec.total_training_price = sum(rec.training_course_ids.mapped('price'))

    def _prepare_opportunity_quotation_context(self):
        quotation_context = super()._prepare_opportunity_quotation_context()
        quotation_context.update({
            'default_training_name': self.training_name,
            'default_half_advance_payment_before': self.half_advance_payment_before,
            'default_half_payment_after': self.half_payment_after,
            'default_training_course_ids': [(6, 0, self.training_course_ids.ids)],
            'default_clcs_qty': self.clcs_qty,
            'default_so_no': self.so_no,
            'default_tr_expiry_date': self.tr_expiry_date,
            'default_instructor_logistics': self.instructor_logistics,
            'default_catering': self.catering,
        })
        return quotation_context
