# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools
from datetime import datetime
from odoo.exceptions import ValidationError

class TrainingCourse(models.Model):
    _name = "training.course"
    _description = 'Training Course'

    name = fields.Char(string='Training Name',)
    no_of_student = fields.Integer(string='No of Student')
    duration = fields.Integer(string='Duration',compute='_compute_date')
    training_date_start = fields.Date(string='Training Date start')
    training_date_end = fields.Date(string='Training Date end')
    price = fields.Float(string='Training Price')
    move_id = fields.Many2one('account.move', string='Move')
    lead_id = fields.Many2one('crm.lead', string='Lead')
    sale_id = fields.Many2one('sale.order', string='Sale Order')
    
    instructor_id = fields.Many2one('hr.employee',string="Instructor")
    descriptions = fields.Char(string='Description')
    training_id = fields.Many2one('product.template',string='Training Name')
    train_language = fields.Char(string='Training Language')
    location = fields.Selection([('DXB','DXB'),('KSA','KSA'),('Venue','Venue'),('Customer Choice','Customer Choice')])
    where_location = fields.Char(string='Where?')
    payment_method = fields.Selection([('cash','Cash'),('clc','CLC')],default='cash')
    clcs_qty = fields.Float(string='CLCs Qty')
    
    
    def _compute_date(self):
        # if self.training_date_start and self.training_date_end:
        #     # date2 = str(self.training_date_end)
        #     # date1 = str(self.training_date_start)
        #     # d1 = datetime.strptime(date1, "%Y-%m-%d")
        #     # d2 = datetime.strptime(date2, "%Y-%m-%d")
    
        #     # difference between dates in timedelta
        #     delta = self.training_date_end - self.training_date_start
        #     # raise ValidationError(delta.day())
        #     # if int(delta) >= 0:
            
        #     self.duration = delta.days
        #     # else:
        #     #     self.duration = 0
        # else:
        duration = 0
        for rec in self:
            duration = rec.training_date_end - rec.training_date_start
            if duration >0:
                rec.duration = duration
            else:
                rec.duration = 0
