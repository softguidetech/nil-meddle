from odoo import models, fields

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    custom_field_1 = fields.Char(string="Custom Field 1")
    custom_field_2 = fields.Char(string="Custom Field 2")
