# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools
from datetime import datetime
from odoo.exceptions import ValidationError

class TrainingCourse(models.Model):
    _name = "training.course"
    _description = 'Training Course'

    name = fields.Char(string='Training Name',)
    no_of_student = fields.Integer(string='# of Student')
    duration = fields.Integer(string='Duration (days)', compute='_compute_date')
    training_date_start = fields.Date(string='Start Date')
    training_date_end = fields.Date(string='End Date')
    price = fields.Float(string='Selling Price')
    move_id = fields.Many2one('account.move', string='Move')
    lead_id = fields.Many2one('crm.lead', string='Lead')
    sale_id = fields.Many2one('sale.order', string='Sale Order')
    
    instructor_id = fields.Many2one('hr.employee', string='Instructor')
    descriptions = fields.Char(string='Description')
    training_id = fields.Many2one('product.product', string='Training Name')
    train_language = fields.Char(string='Language')

    stage_id = fields.Many2one(
        'crm.stage', 
        string='Stage', 
        compute='_compute_stage',
        store=False
    )

    @api.depends('lead_id.stage_id')
    def _compute_stage(self):
        for rec in self:
            rec.stage_id = rec.lead_id.stage_id

    where_location2 = fields.Char(string='Where?')
    location = fields.Selection([('ILT','ILT'),('VILT','VILT')])
    payment_method = fields.Selection([('cash','Cash'),('clc','CLC')], default='cash')
    clcs_qty = fields.Float(string='CLCs Qty')
    default_item_code = fields.Char(related='training_id.default_code', string='Internal Ref')
    cost_clc = fields.Char(related='training_id.product_tmpl_id.cost_clc', string="CLC Cost")
    hyperlink = fields.Char(related='training_id.product_tmpl_id.hyperlink', string="Link")

    def _compute_date(self):
        for rec in self:
            if rec.training_date_start and rec.training_date_end:
                duration = rec.training_date_end - rec.training_date_start
                rec.duration = duration.days
            else:
                rec.duration = 0
