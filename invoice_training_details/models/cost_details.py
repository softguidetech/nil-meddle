from odoo import models, fields, api

class CostDetails(models.Model):
    _name = 'cost.details'
    _description = 'Cost Details'

    currency_id = fields.Many2one(
        'res.currency',
        string="Currency",
        required=True,
        default=lambda self: self.env.company.currency_id.id
    )
    training_vendor = fields.Float(string="Vendor Share")  
    clc_cost = fields.Float(string="Training Cost")
    rate_card = fields.Float(string="Training Cost")
    price = fields.Float(string='Price', required=True)
    training_vendor = fields.Float(string="Vendor Share")
    total_price_all = fields.Float(string='Total Price', compute='_compute_total_price_all', store=True)

    @api.depends('price', 'training_vendor', 'clc_cost', 'rate_card')
    def _compute_total_price_all(self):
        for record in self:
            record.total_price_all = (record.price or 0) + (record.training_vendor or 0) + (record.clc_cost or 0)
    
    def write(self, vals):
        res = super(CostDetails, self).write(vals)
        if any(field in vals for field in ['price', 'training_vendor', 'clc_cost']):
            self.mapped('cos_detail_lead_id')._compute_total()
        return res

    def unlink(self):
        leads = self.mapped('cos_detail_lead_id')
        res = super(CostDetails, self).unlink()
        leads._compute_total()
        return res
