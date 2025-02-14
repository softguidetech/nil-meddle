# -*- coding: utf-8 -*-
from odoo import api, fields, models

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    # Fields related to training courses
    training_ids = fields.One2many(
        'purchase.order.training',  # The related model
        'purchase_order_id',        # The field in the related model
        string='Training Courses'
    )


class PurchaseOrderTraining(models.Model):
    _name = 'purchase.order.training'
    _description = 'Purchase Order Training'
    
    # Link back to purchase order
    purchase_order_id = fields.Many2one(
        'purchase.order', 
        string='Purchase Order',
        required=True
    )
    
    # Fields for the training course model
    name = fields.Char(string='Training Name')
    no_of_student = fields.Integer(string='Number of Students')
    duration = fields.Char(string='Duration', compute='_compute_date', store=True)
    training_date_start = fields.Date(string='Training Start Date')
    training_date_end = fields.Date(string='Training End Date')
    price = fields.Float(string='Training Price')
    move_id = fields.Many2one('account.move', string='Move')
    lead_id = fields.Many2one('crm.lead', string='Lead')
    sale_id = fields.Many2one('sale.order', string='Sale Order')
    
    instructor_id = fields.Many2one('hr.employee', string='Instructor')
    descriptions = fields.Char(string='Description')
    training_id = fields.Many2one('product.product', string='Training Product')
    train_language = fields.Char(string='Training Language')
    
    where_location2 = fields.Char(string='Where?')
    location = fields.Selection([('CISCO U', 'CISCO U'), ('ILT', 'ILT'), ('VILT', 'VILT')], string='Location')
    payment_method = fields.Selection([('cash', 'Cash'), ('clc', 'CLC')], default='cash')
    clcs_qty = fields.Float(string='CLC Quantity')
    
    default_item_code = fields.Char(related='training_id.default_code', string='Internal Ref')
    cost_clc = fields.Char(related='training_id.product_tmpl_id.cost_clc', string='Cost CLC')
    hyperlink = fields.Char(related='training_id.product_tmpl_id.hyperlink', string='Hyperlink')
    
    # Compute the duration between training start and end dates
    @api.depends('training_date_start', 'training_date_end')
    def _compute_date(self):
        for rec in self:
            if rec.training_date_start and rec.training_date_end:
                # Ensure the dates are valid before calculating duration
                duration = rec.training_date_end - rec.training_date_start
                rec.duration = str(duration.days) + " days" if duration.days >= 0 else "Invalid Duration"
            else:
                rec.duration = "0 days"
