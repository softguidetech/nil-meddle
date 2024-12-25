# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools
from datetime import datetime
from odoo.exceptions import ValidationError

class ProService(models.Model):
    _name = "pro.service"
    _description = 'Propfessional Services'

    name = fields.Char(string='Service Name',)
    no_of_student = fields.Integer(string='No of Student')
    duration = fields.Char(string='Duration',compute='_compute_date')
    training_date_start = fields.Date(string='Training Date start')
    training_date_end = fields.Date(string='Training Date end')
    price = fields.Float(string='Training Price')
    pro_move_id = fields.Many2one('account.move', string='Move')
    pro_lead_id = fields.Many2one('crm.lead', string='Lead')
    pro_sale_id = fields.Many2one('sale.order', string='Sale Order')
    
    # instructor_id = fields.Many2one('hr.employee',string="Instructor")
    descriptions = fields.Char(string='Description')
    training_id = fields.Many2one('product.template',string='Service Name')
    train_language = fields.Char(string='Language')
    location = fields.Selection([('DXB','DXB'),('KSA','KSA'),('Venue','Venue'),('Customer Choice','Customer Choice')])
    where_location = fields.Char(string='Where?')
    payment_method = fields.Selection([('cash','Cash'),('clc','CLC')],default='cash')
    clcs_qty = fields.Float(string='CLCs Qty')
    
    
    def _compute_date(self):
        
        duration = 0
        for rec in self:
            duration = rec.training_date_end - rec.training_date_start
            days = str(duration).replace('0:00:00','')
            rec.duration = days
           