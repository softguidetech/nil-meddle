# -*- coding: utf-8 -*-
from odoo import fields, models, api

class Lead(models.Model):
    _inherit = 'crm.lead'

    training_name = fields.Char(string='Training Name')
    venue = fields.Float(string='Venue')
    service_name = fields.Char(string='Service Name')
    total_training_price = fields.Float(string='Total Training Price', compute="_compute_training_price", store=True)
    total_service_price = fields.Float(string='Total Service Price', compute="_compute_service_price", store=True)
    half_advance_payment_before = fields.Float(string='Advance Payment Amount 50% (Paid)')
    half_payment_after = fields.Float(string='50% Amount after Training Delivery (Not Yet Paid)')

    training_course_ids = fields.One2many('training.course', 'lead_id', string='Training Courses')
    pro_service_ids = fields.One2many('pro.service', 'pro_lead_id', string='Professional Services')
    ticket_ids = fields.One2many('ticket.ticket', 'ticket_lead_id', string='Tickets')
    hotel_ids = fields.One2many('hotel.hotel', 'hotel_lead_id', string='Hotels')

    cost_details_ids = fields.One2many('cost.details', 'lead_id', string="Cost Details")

    total_price_all = fields.Float(string="Total Logistics", compute='_compute_total', store=True)
    visa = fields.Boolean(string="Visa")
    start_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")

    book_details_id = fields.Many2many('ir.attachment', string="Booking Details", help="Attach documents", copy=False)
    details = fields.Html(string="Details")
    cost = fields.Float(string="Cost")
    training_vendor = fields.Float(string="Partner Share")
    training_type = fields.Float(string="Logistics Cost")
    margin1 = fields.Float(string="Margin 1", compute='_compute_margin1', store=True)

    instructor_id = fields.Many2one('hr.employee', string="Instructor")
    descriptions = fields.Char(string='Description')
    ordering_partner_id = fields.Many2one('res.partner', string='Ordering Partner')
    training_id = fields.Many2one('product.template', string='Training Name')

    train_language = fields.Char(string='Language')
    location = fields.Selection([('ILT', 'ILT'), ('VILT', 'VILT')])
    payment_method = fields.Selection([('cash', 'Cash'), ('clc', 'CLC')], default='cash')
    clcs_qty = fields.Float(string='CLCs Qty')
    learnig_partner = fields.Selection([('Koeing', 'Koeing'), ('NIL LTD', 'NIL LTD'), ('NIL SA', 'NIL SA')])

    so_no = fields.Char(string='SO#')
    tr_expiry_date = fields.Date(string='Expiry Date')
    poref = fields.Char(string='PO Ref:')
    invref = fields.Char(string='Invoice Ref:')

    clc_cost = fields.Float(string="Training Cost")
    rate_card = fields.Float(string="Partner Share")
    nilme_share = fields.Float(string="NIL ME Share $")

    instructor_logistics = fields.Char(string='Instructor Logistics')
    uber = fields.Float(string='Uber')
    catering = fields.Selection([('NIL MM', 'NIL MN'), ('Others', 'Others')], string='Catering')
    ctrng = fields.Float(string='Catering')

    @api.depends('clc_cost', 'rate_card', 'total_price_all')
    def _compute_margin1(self):
        for record in self:
            record.margin1 = (record.clc_cost or 0) + (record.rate_card or 0) + (record.total_price_all or 0)

    @api.depends('ticket_ids.price', 'hotel_ids.price', 'cost', 'instructor_logistics', 'venue', 'ctrng', 'uber')
    def _compute_total(self):
        for rec in self:
            rec.total_price_all = sum([
                sum(ticket.price for ticket in rec.ticket_ids),
                sum(hotel.price for hotel in rec.hotel_ids),
                rec.cost or 0,
                rec.instructor_logistics or 0,
                rec.venue or 0,
                rec.ctrng or 0,
                rec.uber or 0
            ])

class CostDetails(models.Model):
    _name = 'cost.details'
    _description = 'Cost Details'

    lead_id = fields.Many2one('crm.lead', string="Lead", required=True, ondelete='cascade')
    learnig_partner = fields.Selection([('Koeing', 'Koeing'), ('NIL LTD', 'NIL LTD'), ('NIL SA', 'NIL SA')], string="Learning Partner")
    clc_cost = fields.Float(string="Training Cost")
    rate_card = fields.Float(string="Partner Share")
    nilme_share = fields.Float(string="NIL ME Share $")
    training_vendor = fields.Float(string="Partner Share")
    total_price_all = fields.Float(string="Total Price")
    margin1 = fields.Float(string="Margin")



class HotelHotel(models.Model):
    _name = 'hotel.hotel'
    _description = 'Hotels'
    
    hotel_lead_id = fields.Many2one('crm.lead', string="Lead")
    hotel_id = fields.Many2one('hotel.description', string="Hotel")
    date_from = fields.Date(string="Date From")
    date_to = fields.Date(string="Date To")
    location = fields.Char(string="Location")
    pax = fields.Char(string="PAX")
    room_type = fields.Char(string="Room Type")
    currency_id = fields.Many2one('res.currency', string="Currency", required=True)
    price = fields.Monetary(string="Price with Tax")


class TicketTicket(models.Model):
    _name = 'ticket.ticket'
    _description = 'Tickets'

    ticket_lead_id = fields.Many2one('crm.lead', string="Lead")
    airline_id = fields.Many2one('airline.airline', string="Airlines")
    origin_id = fields.Many2one('loca.loca', string="Origin")
    destination_id = fields.Many2one('loca.loca', string="Destination")
    date = fields.Date(string="Date")
    duration = fields.Char(string="Duration")
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
    _inherit = 'product.template'

    cost_clc = fields.Char(string="CLCs Cost")
    hyperlink = fields.Char(string="Hyper Link")
