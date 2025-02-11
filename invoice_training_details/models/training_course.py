# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from datetime import datetime

class TrainingCourse(models.Model):
    _name = "training.course"

    name = fields.Char(string='Training Name')
    no_of_student = fields.Integer(string='No of Student')
    duration = fields.Char(string='Duration', compute='_compute_date')
    training_date_start = fields.Date(string='Training Date Start')
    training_date_end = fields.Date(string='Training Date End')
    price = fields.Float(string='Training Price')
    move_id = fields.Many2one('account.move', string='Move')
    lead_id = fields.Many2one('crm.lead', string='Lead')
    sale_id = fields.Many2one('sale.order', string='Sale Order')
    instructor_id = fields.Many2one('hr.employee', string="Instructor")
    training_id = fields.Many2one('product.product', string='Training Name')
    train_language = fields.Char(string='Training Language')
    where_location2 = fields.Char(string='Where?')
    location = fields.Selection([('CISCO U', 'CISCO U'), ('ILT', 'ILT'), ('VILT', 'VILT')])
    payment_method = fields.Selection([('cash', 'Cash'), ('clc', 'CLC')], default='cash')
    clcs_qty = fields.Float(string='CLCs Qty')
    default_item_code = fields.Char(related='training_id.default_code', string='Internal Ref')
    cost_clc = fields.Char(related='training_id.product_tmpl_id.cost_clc', string="Cost CLC")
    hyperlink = fields.Char(related='training_id.product_tmpl_id.hyperlink', string="Hyper Link")

    @api.depends('training_date_start', 'training_date_end')
    def _compute_date(self):
        for rec in self:
            if rec.training_date_start and rec.training_date_end:
                rec.duration = (rec.training_date_end - rec.training_date_start).days
            else:
                rec.duration = ''

    @api.onchange('lead_id')
    def _onchange_lead_id(self):
        if self.lead_id:
            self.training_date_start = False
            self.training_date_end = False
            self.instructor_id = False
