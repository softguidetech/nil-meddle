# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api

class Lead(models.Model):
    _inherit = 'crm.lead'

    currency_id = fields.Many2one(
        "res.currency", string="Currency", default=lambda self: self.env.ref("base.USD"), required=True
    )
    amount_usd = fields.Monetary(
        string="Expected Revenue (USD)", currency_field="currency_id"
    )
    training_name = fields.Char(string='Training Name')
    venue = fields.Float(string='Venue')  
    service_name = fields.Char(string='Service Name')
    total_training_price = fields.Float(string='Total Training Price', compute="_compute_training_price", store=True)
    
    @api.depends('training_course_ids.price')
    def _compute_training_price(self):
        for rec in self:
            rec.total_training_price = sum(rec.training_course_ids.mapped('price')) if rec.training_course_ids else 0

    total_service_price = fields.Float(string='Total Service Price', compute="_compute_service_price", store=True)
    half_advance_payment_before = fields.Float(string='Advance payment amount 50% (paid)')
    half_payment_after = fields.Float(string='50% Amount after Training Delivery (Not Yet Paid)')
    training_course_ids = fields.One2many('training.course', 'lead_id', string='Training Courses')
    pro_service_ids = fields.One2many('pro.service','pro_lead_id',string='Professional Services')
    end_customer = fields.Char(string='End Client')
    cisco_am = fields.Char(string='Cisco Account Manager')
    cost_details_ids = fields.One2many('cost.details', 'cos_lead_id', string="Costs Details")
    ticket_ids = fields.One2many('ticket.ticket','ticket_lead_id',string='Tickets')
    hotel_ids = fields.One2many('hotel.hotel','hotel_lead_id',string='Hotels')
    total_price_all = fields.Float(string="Total Logistics",compute='_compute_total')
    visa = fields.Boolean(string="Visa")
    start_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")

    @api.depends('ticket_ids.price', 'hotel_ids.price', 'cost_details_ids.price', 'instructor_logistics', 'venue', 'ctrng', 'uber')
    def _compute_total(self):
        for rec in self:
            ticket_total = sum(ticket.price for ticket in rec.ticket_ids) if rec.ticket_ids else 0
            hotel_total = sum(hotel.price for hotel in rec.hotel_ids) if rec.hotel_ids else 0
            cost_details_total = sum(cost.price for cost in rec.cost_details_ids) if rec.cost_details_ids else 0
            instructor_logistics = float(rec.instructor_logistics) if rec.instructor_logistics else 0
            venue = float(rec.venue) if rec.venue and rec.venue.isnumeric() else 0
            uber = rec.uber if rec.uber else 0

            rec.total_price_all = ticket_total + hotel_total + cost_details_total + instructor_logistics + venue + uber

    @api.depends('pro_service_ids.price')
    def _compute_service_price(self):
        for rec in self:
            rec.total_service_price = sum(rec.pro_service_ids.mapped('price')) if rec.pro_service_ids else 0

class HotelHotel(models.Model):
    _name = 'hotel.hotel'
    _description = 'Hotels'

    hotel_lead_id = fields.Many2one('crm.lead', string="Lead")
    hotel_id = fields.Many2one('hotel.description', string="Hotel")
    date_from = fields.Date(string="Date From")
    date_to = fields.Date(string="Date To")
    nights = fields.Char(string="Nights", compute='_compute_nights')
    price_without_tax = fields.Monetary(string="Price", required=True)
    tax = fields.Monetary(string="Taxes", required=True)
    price = fields.Monetary(string="Price with Tax", compute='_compute_total')

    @api.depends('price_without_tax', 'tax')
    def _compute_total(self):
        for rec in self:
            rec.price = rec.price_without_tax + rec.tax

    @api.depends('date_from', 'date_to')
    def _compute_nights(self):
        for rec in self:
            if rec.date_from and rec.date_to:
                rec.nights = str((rec.date_to - rec.date_from).days) + " Nights"
            else:
                rec.nights = "0 Nights"

class TicketTicket(models.Model):
    _name = 'ticket.ticket'
    _description = 'Tickets'

    ticket_lead_id = fields.Many2one('crm.lead', string="Lead")
    airline_id = fields.Many2one('airline.airline', string="Airlines")
    origin_id = fields.Many2one('loca.loca', string="Origin")
    destination_id = fields.Many2one('loca.loca', string="Destination")
    date = fields.Date(string="Date")
    currency_id = fields.Many2one('res.currency', string="Currency", required=True)
    price = fields.Monetary(string="Price with Taxes", required=True)

class AirlineAirline(models.Model):
    _name = 'airline.airline'
    _description = 'Airlines'

    name = fields.Char(string="Airline", required=True)

class LocaLoca(models.Model):
    _name = 'loca.loca'
    _description = 'Locations'

    name = fields.Char(string="Location", required=True)

class FlightClassType(models.Model):
    _name = 'flight.class.type'
    _description = 'Classes'

    name = fields.Char(string="Class Type", required=True)

class HotelDescription(models.Model):
    _name = 'hotel.description'
    _description = 'Hotel Description'

    name = fields.Char(string="Hotel", required=True)

class ProductProduct(models.Model):
    _inherit = 'product.product'

    cost_clc = fields.Char(string="CLCs Cost")
    hyperlink = fields.Char(string="Hyper Link")

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    cost_clc = fields.Char(string="CLCs Cost")
    hyperlink = fields.Char(string="Hyper Link")
