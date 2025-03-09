from odoo import models, fields, api

class CostDetails(models.Model):
    _name = 'cost.details'
    _description = 'Cost Details'

    cos_lead_id = fields.Many2one('crm.lead', string="Lead", ondelete='cascade')
    name = fields.Char(string="Cost Name")
    description = fields.Text(string="Description")
    price = fields.Float(string="Price")  # Make the price field optional
    currency_id = fields.Many2one('res.currency', string="Currency", required=True, default=lambda self: self.env.company.currency_id.id)

    # ✅ These cost fields now belong only to cost.details
    training_vendor = fields.Float(string="Partner Share")  
    total_price_all = fields.Float(string="Logistics Cost")  
    margin1 = fields.Float(string="Total Costs", compute='_compute_margin1')
    clc_cost = fields.Float(string="Training Cost")
    rate_card = fields.Float(string="Partner Rate")  
    nilme_share = fields.Float(string="NIL ME Share $", compute='_compute_nilme_share')
    learning_partner = fields.Selection([
        ('Koeing', 'Koeing'),
        ('Mira', 'Mira'),
        ('NIL LTD', 'NIL LTD'),
        ('NIL SA', 'NIL SA')
    ], string='Learning Partner')

    @api.depends('training_vendor', 'total_price_all', 'clc_cost', 'ticket_ids', 'hotel_ids', 'cost_details_ids', 'venue', 'ctrng', 'uber')
    def _compute_margin1(self):
        for record in self:
            ticket_total = sum(ticket.price for ticket in record.ticket_ids) if record.ticket_ids else 0
            hotel_total = sum(hotel.price for hotel in record.hotel_ids) if record.hotel_ids else 0
            cost_details_total = sum(cost.price for cost in record.cost_details_ids) if record.cost_details_ids else 0
            venue = record.venue if record.venue else 0
            catering = record.ctrng if record.ctrng else 0
            uber = record.uber if record.uber else 0
            
            record.margin1 = (record.training_vendor or 0) + (record.total_price_all or 0) + (record.clc_cost or 0) + ticket_total + hotel_total + cost_details_total + venue + catering + uber

    @api.depends('margin1', 'cos_lead_id.total_training_price')
    def _compute_nilme_share(self):
        for record in self:
            record.nilme_share = (record.cos_lead_id.total_training_price or 0) - (record.margin1 or 0)
