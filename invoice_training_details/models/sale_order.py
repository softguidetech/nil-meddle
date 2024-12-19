# -*- coding: utf-8 -*-

from odoo import api, models, fields


class SaleOrder(models.Model):
    _inherit = "sale.order"

    training_name = fields.Char(string='Training Name')
    total_training_price = fields.Float(string='Total Training Price', compute="_compute_training_price", store=True)
    half_advance_payment_before = fields.Float(string='Advance payment amount 50% (paid)')
    half_payment_after = fields.Float(string='50% Amount after Training Delivery (Not Yet Paid)')
    training_course_ids = fields.One2many('training.course', 'sale_id', string='Training Courses')
    
    #Add extera
    instructor_id = fields.Many2one('res.employee',string="Instructor")
    training_id = fields.Many2one('product.template',string='Training Name')
    train_language = fields.Char(string='Training Language')
    location = fields.Char(string='Location')
    payment_method = fields.Selection([('cash','Cash'),('clc','CLC')],default='cash')
    
    
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

    def _prepare_invoice(self):
        vals = super()._prepare_invoice()
        vals.update({
            'training_name': self.training_name,
            'half_advance_payment_before': self.half_advance_payment_before,
            'half_payment_after': self.half_payment_after,
            'training_course_ids': [(6, 0, self.training_course_ids.ids)],
            'clcs_qty': self.clcs_qty,
            'so_no': self.so_no,
            'tr_expiry_date': self.tr_expiry_date,
            'instructor_logistics': self.instructor_logistics,
            'catering': self.catering,
            
            'instructor_id': self.instructor_id.id,
            'training_id': self.training_id.id,
            'train_language': self.train_language,
            'location': self.location,
            'payment_method': self.payment_method,
        })
        return vals
