
from odoo import models, fields, api

class CostDetails(models.Model):
    _name = 'cost.details'
    _description = 'Cost Details'

    cos_lead_id = fields.Many2one('crm.lead', string='Lead')
    name = fields.Char(string='Cost Line Name', required=True)
    description = fields.Text(string='Description')
    price = fields.Float(string='Price')
    currency_id = fields.Many2one('res.currency', string='Currency')
    training_vendor = fields.Float(string='Training Vendor Cost')
    total_price_all = fields.Float(string='Total Price')
    clc_cost = fields.Float(string='CLC Cost')
    rate_card = fields.Float(string='Rate Card')
    nilme_share = fields.Float(string='NILME Share')

    @api.depends('clc_cost', 'rate_card', 'price')
    def _compute_margin1(self):
        for record in self:
            record.margin1 = (record.clc_cost or 0) + (record.rate_card or 0) + (record.price or 0)
