from odoo import api, fields, models
from datetime import timedelta

class TrainingCourse(models.Model):
    _name = "training.course"
    _description = 'Training Course'

    name = fields.Char(string='Training Name')
    no_of_student = fields.Integer(string='# of Students')
    duration = fields.Integer(string='Duration (Days)', compute='_compute_date', store=True)
    training_date_start = fields.Date(string='Start Date')
    training_date_end = fields.Date(string='End Date')
    price = fields.Float(string='Selling Price')
    move_id = fields.Many2one('account.move', string='Move')
    lead_id = fields.Many2one('crm.lead', string='Lead')
    sale_id = fields.Many2one('sale.order', string='Sale Order')
    
    instructor_id = fields.Many2one('hr.employee', string="Instructor")
    descriptions = fields.Char(string='Description')
    training_id = fields.Many2one('product.product', string='Training Name')
    train_language = fields.Char(string='Language')
    
    where_location2 = fields.Char(string='Where?')
    location = fields.Selection([('ILT', 'ILT'), ('VILT', 'VILT')])
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
                rec.duration = 0  # Default to 0 if dates are missing
