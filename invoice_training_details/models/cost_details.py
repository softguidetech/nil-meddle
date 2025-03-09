from odoo import models, fields, api

class CostDetails(models.Model):
    _name = 'cost.details'
    _description = 'Cost Details'

    cos_lead_id = fields.Many2one('crm.lead', string="Lead", ondelete='cascade')
    name = fields.Char(string="Cost Name", required=True)
    description = fields.Text(string="Description")
    currency_id = fields.Many2one('res.currency', string="Currency", required=True, default=lambda self: self.env.company.currency_id.id)

    # Cost-Related Fields
    training_vendor = fields.Float(string="Vendor Share")  
    total_price_all = fields.Float(string="Logistics Cost")  
    margin1 = fields.Float(string="Margin 1", compute='_compute_margin1', store=True)
    clc_cost = fields.Float(string="Training Cost")
    rate_card = fields.Float(string="Partner Rate")  
    nilme_share = fields.Float(string="NIL ME Share $")
    price = fields.Float(string="Price")  

    @api.depends('clc_cost', 'rate_card', 'price')
    def _compute_margin1(self):
        for record in self:
            record.margin1 = (record.clc_cost or 0) + (record.rate_card or 0) - (record.nilme_share or 0)
