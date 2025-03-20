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
    duration = fields.Char(string='Duration',)
    training_date_start = fields.Date(string='Training Date start')
    training_date_end = fields.Date(string='Delivery Date')
    price = fields.Float(string='Price')
    pro_move_id = fields.Many2one('account.move', string='Move')
    pro_lead_id = fields.Many2one('crm.lead', string='Lead')
    pro_sale_id = fields.Many2one('sale.order', string='Sale Order')
    
    # instructor_id = fields.Many2one('hr.employee',string="Instructor")
    descriptions = fields.Char(string='Description')
    wor_hour_number = fields.Float(string='Working Hour Number')
    hourly_rate = fields.Float(string='Hourly Rate')
    training_id = fields.Many2one('product.product',string='Service Name')
    train_language = fields.Char(string='Language')
    location = fields.Selection([('DXB','NIL DXB'),('KSA','NIL KSA'),('Venue','Venue'),('Customer Choice','Customer Choice')])
    where_location = fields.Char(string='Project Location',default='Webex')
    payment_method = fields.Selection([('cash','Cash'),('clc','CLC')],default='cash')
    clcs_qty = fields.Float(string='CLCs Qty')
    default_item_code = fields.Char(related='training_id.default_code',string='Internal Ref')
    requester = fields.Char(string='Requester')
    end_customer = fields.Char(string='End Client')
    cisco_am = fields.Char(string='Cisco Account Manager')
    cost_clc = fields.Char(related='training_id.product_tmpl_id.cost_clc',string="Cost Clc")
    hyperlink = fields.Char(related='training_id.product_tmpl_id.hyperlink',string="Hyper Link")
    
    # def _compute_date(self):
        
    #     duration = 0
    #     for rec in self:
    #         duration = rec.training_date_end - rec.training_date_start
    #         days = str(duration).replace(', 0:00:00','')
    #         rec.duration = days
           
