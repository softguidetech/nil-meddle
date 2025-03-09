from odoo import models, fields, api

class CostDetails(models.Model):
    _name = 'cost.details'
    _description = 'Cost Details'

    cos_lead_id = fields.Many2one('crm.lead', string="Lead", ondelete='cascade')
    name = fields.Char(string="Cost Name", required=True)
    description = fields.Text(string="Description")
    currency_id = fields.Many2one('res.currency', string="Currency", required=True, default=lambda self: self.env.company.currency_id.id)

    # ✅ These cost fields now belong only to cost.details
    training_vendor = fields.Float(string="Vendor Share")  
    total_price_all = fields.Float(string="Logistics Cost")  
    ttl_costs = fields.Float(string="Margin 1", compute='_compute_ttl_costs')
    clc_cost = fields.Float(string="Training Cost")
    rate_card = fields.Float(string="Partner Rate")  
    nilme_share = fields.Float(string="NIL ME Share $")
    price = fields.Float(string="Price")

    @api.depends('clc_cost', 'rate_card', 'price')
    def _compute_ttl_costs(self):
        for record in self:
            record.ttl_costs = (record.clc_cost or 0) + (record.rate_card or 0) + (record.price or 0)
