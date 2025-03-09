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
    total_price_all = fields.Float(string="Logistics Cost", compute='_compute_total')  
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

    @api.depends('ticket_ids.price', 'hotel_ids.price', 'cost_details_ids.price', 'instructor_logistics', 'venue', 'ctrng', 'uber')
    def _compute_total(self):
        for rec in self:
            ticket_total = sum(ticket.price for ticket in rec.ticket_ids) if rec.ticket_ids else 0
            hotel_total = sum(hotel.price for hotel in rec.hotel_ids) if rec.hotel_ids else 0
            cost_details_total = sum(cost.price for cost in rec.cost_details_ids) if rec.cost_details_ids else 0
            instructor_logistics = float(rec.instructor_logistics) if rec.instructor_logistics else 0
            venue = rec.venue if rec.venue else 0
            catering = rec.ctrng if rec.ctrng else 0
            uber = rec.uber if rec.uber else 0

            rec.total_price_all = ticket_total + hotel_total + cost_details_total + instructor_logistics + venue + catering + uber

    @api.depends('training_vendor', 'total_price_all', 'clc_cost')
    def _compute_margin1(self):
        for record in self:
            record.margin1 = (record.training_vendor or 0) + (record.total_price_all or 0) + (record.clc_cost or 0)

    @api.depends('margin1', 'cos_lead_id.total_training_price')
    def _compute_nilme_share(self):
        for record in self:
            record.nilme_share = (record.cos_lead_id.total_training_price or 0) - (record.margin1 or 0)
