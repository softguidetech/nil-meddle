# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools
from datetime import datetime

class TrainingCourse(models.Model):
    _name = "training.course"
    _description = 'Training Course'

    name = fields.Char(string='Training Name', required=True)
    no_of_student = fields.Integer(string='No of Student')
    duration = fields.Date(string='Duration',compute='_compute_date')
    training_date_start = fields.Date(string='Training Date start')
    training_date_end = fields.Date(string='Training Date end')
    price = fields.Float(string='Training Price')
    move_id = fields.Many2one('account.move', string='Move')
    lead_id = fields.Many2one('crm.lead', string='Lead')
    sale_id = fields.Many2one('sale.order', string='Sale Order')
    
    instructor_id = fields.Many2one('hr.employee',string="Instructor")
    training_id = fields.Many2one('product.template',string='Training Name')
    train_language = fields.Char(string='Training Language')
    location = fields.Char(string='Location')
    payment_method = fields.Selection([('cash','Cash'),('clc','CLC')],default='cash')
    clcs_qty = fields.Float(string='CLCs Qty')
    
    
    def _compute_date(self):
        
        d1 = datetime.strptime(self.training_date_start, "%Y/%m/%d")
        d2 = datetime.strptime(self.training_date_end, "%Y/%m/%d")

        # difference between dates in timedelta
        delta = d2 - d1
        self.duration = delta
