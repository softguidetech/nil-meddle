from odoo import models, fields

class CostDetails(models.Model):
    _name = 'cost.details'
    _description = 'Cost Details'

    cos_lead_id = fields.Many2one('crm.lead', string="Lead", ondelete='cascade')
    name = fields.Char(string="Cost Name", required=True)
    description = fields.Text(string="Description")
    price = fields.Float(string="Price", required=True)
    currency_id = fields.Many2one('res.currency', string="Currency", required=True)

    def _compute_total_cost(self):
        for record in self:
            record.price = sum(record.mapped('price'))
