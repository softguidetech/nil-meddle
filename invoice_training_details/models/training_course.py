# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools


class TrainingCourse(models.Model):
    _name = "training.course"
    _description = 'Training Course'

    name = fields.Char(string='Training Name', required=True)
    no_of_student = fields.Integer(string='No of Student')
    duration = fields.Char(string='Duration')
    training_date_start = fields.Date(string='Training Date start')
    training_date_end = fields.Date(string='Training Date end')
    price = fields.Float(string='Training Price')
    move_id = fields.Many2one('account.move', string='Move')
    lead_id = fields.Many2one('crm.lead', string='Lead')
    sale_id = fields.Many2one('sale.order', string='Sale Order')
    
    instructor_id = fields.Many2one('res.employee',string="Instructor")
    training_id = fields.Many2one('product.template',string='Training Name')
    train_language = fields.Char(string='Training Language')
    location = fields.Char(string='Location')
    payment_method = fields.Selection([('cash','Cash'),('clc','CLC')],default='cash')
    
