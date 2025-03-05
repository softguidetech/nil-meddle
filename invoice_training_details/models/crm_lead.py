# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class Lead(models.Model):
    _inherit = 'crm.lead'

    training_name = fields.Char(string='Training Name')
    service_name = fields.Char(string='Service Name')
    total_training_price = fields.Float(string='Total Training Price', compute="_compute_training_price", store=True)
    total_service_price = fields.Float(string='Total Service Price', compute="_compute_service_price", store=True)
    half_advance_payment_before = fields.Float(string='Advance Payment Amount 50% (Paid)')
    half_payment_after = fields.Float(string='50% Amount After Training Delivery (Not Yet Paid)')
    training_course_ids = fields.One2many('training.course', 'lead_id', string='Training Courses')
    pro_service_ids = fields.One2many('pro.service', 'pro_lead_id', string='Professional Services')
    ticket_ids = fields.One2many('ticket.ticket', 'ticket_lead_id', string='Tickets')
    hotel_ids = fields.One2many('hotel.hotel', 'hotel_lead_id', string='Hotels')
    total_price_all = fields.Float(string="Logistics Cost", compute='_compute_total')
    visa = fields.Boolean(string="Visa")
    start_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")
    book_details_id = fields.Many2many('ir.attachment', 'doc_attach_rel4', 'doc_id', 'attach_id5',
                                       string="Booking Details",
                                       help='You can attach the copy of your document', copy=False)
    cost_details_ids = fields.One2many('cost.details', 'lead_id', string="Cost Details")

    @api.depends('ticket_ids.price', 'hotel_ids.price')
    def _compute_total(self):
        for rec in self:
            ticket_total = sum(rec.ticket_ids.mapped('price')) if rec.ticket_ids else 0
            hotel_total = sum(rec.hotel_ids.mapped('price')) if rec.hotel_ids else 0
            rec.total_price_all = ticket_total + hotel_total

    @api.depends('pro_service_ids.price')
    def _compute_service_price(self):
        for rec in self:
            rec.total_service_price = sum(rec.pro_service_ids.mapped('price')) if rec.pro_service_ids else 0

    @api.depends('training_course_ids.price')
    def _compute_training_price(self):
        for rec in self:
            rec.total_training_price = sum(rec.training_course_ids.mapped('price')) if rec.training_course_ids else 0


class CostDetails(models.Model):
    _name = 'cost.details'
    _description = 'Cost Details'

    lead_id = fields.Many2one('crm.lead', string="Lead")
    clc_cost = fields.Float(string="CLC Cost")
    rate_card = fields.Float(string="Rate Card")
    nilme_share = fields.Float(string="NILME Share")
    training_vendor = fields.Float(string="Partner Share")
    total_price_all = fields.Float(string="Total Price")
    instructor_id = fields.Many2one('hr.employee', string="Instructor")
    descriptions = fields.Char(string='Description')
    ordering_partner_id = fields.Many2one('res.partner', string='Ordering Partner')
    training_id = fields.Many2one('product.template', string='Training Name')
    train_language = fields.Char(string='Language')
    location = fields.Selection([('ILT', 'ILT'), ('VILT', 'VILT')], string='Location')
    payment_method = fields.Selection([('cash', 'Cash'), ('clc', 'CLC')], default='cash', string='Payment Method')
    clcs_qty = fields.Float(string='Customer CLCs Qty')
    so_no = fields.Char(string='SO#')
    tr_expiry_date = fields.Date(string='Expiry Date')
    poref = fields.Char(string='PO Reference')
    invref = fields.Char(string='Invoice Reference')
    instructor_logistics = fields.Char(string='Instructor Logistics')
    catering = fields.Selection([('NIL MM', 'NIL MM'), ('Others', 'Others')], string='Catering')


class Hotel(models.Model):
    _name = 'hotel.hotel'
    _description = 'Hotels'

    hotel_lead_id = fields.Many2one('crm.lead', string="Lead")
    hotel_order_id = fields.Many2one('sale.order', string="Order")
    hotel_id = fields.Many2one('hotel.description', string="Hotel")
    date_from = fields.Date(string="Date From")
    date_to = fields.Date(string="Date To")
    nights = fields.Char(string="Nights", compute='_compute_nights')
    location = fields.Char(string="Location")
    pax = fields.Char(string="PAX")
    des = fields.Char(string="Description")
    room_type = fields.Char(string="Room Type")
    currency_id = fields.Many2one('res.currency', string="Currency", required=True)
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
                rec.nights = (rec.date_to - rec.date_from).days


class Ticket(models.Model):
    _name = 'ticket.ticket'
    _description = 'Tickets'

    ticket_lead_id = fields.Many2one('crm.lead', string="Lead")
    ticket_order_id = fields.Many2one('sale.order', string="Order")
    airline_id = fields.Many2one('airline.airline', string="Airlines")
    origin_id = fields.Many2one('loca.loca', string="Origin")
    destination_id = fields.Many2one('loca.loca', string="Destination")
    date = fields.Date(string="Date")
    class_type_id = fields.Many2one('flight.class.type', string="Class Type")
    currency_id = fields.Many2one('res.currency', string="Currency", required=True)
    price = fields.Monetary(string="Price with Taxes", required=True)


class Airline(models.Model):
    _name = 'airline.airline'
    _description = 'Airlines'

    name = fields.Char(string="Airline", required=True)


class Location(models.Model):
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
