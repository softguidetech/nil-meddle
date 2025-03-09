from odoo import models, fields, api

class CostDetails(models.Model):
    _name = 'cost.details'
    _description = 'Cost Details'

    cos_lead_id = fields.Many2one('crm.lead', string="CRM Lead", ondelete='cascade')
    name = fields.Char(string="Cost Name", required=True)
    description = fields.Text(string="Description")
    currency_id = fields.Many2one('res.currency', string="Currency", required=True, default=lambda self: self.env.company.currency_id.id)

    training_vendor = fields.Float(string="Vendor Share")  
    clc_cost = fields.Float(string="Training Cost")
    rate_card = fields.Float(string="Partner Rate")  
    nilme_share = fields.Float(string="NIL ME Share $")

    margin1 = fields.Float(string="Margin 1", compute='_compute_margin1')

    @api.depends('clc_cost', 'rate_card')
    def _compute_margin1(self):
        for record in self:
            record.margin1 = (record.clc_cost or 0) + (record.rate_card or 0)

    def write(self, vals):
        res = super(CostDetails, self).write(vals)
        # You removed 'price', so no need to trigger compute based on 'price'
        return res

    def unlink(self):
        leads_to_update = self.mapped('cos_lead_id')
        res = super(CostDetails, self).unlink()
        for lead in leads_to_update:
            lead._compute_total()
        return res
