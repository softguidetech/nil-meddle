# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api

class Lead(models.Model):
    _inherit = 'crm.lead'

    training_name = fields.Char(string='Training Name')
    service_name = fields.Char(string='Service Name')
    
    total_training_price = fields.Float(string='Total Training Price', compute="_compute_training_price", store=True, default=0.0)
    total_service_price = fields.Float(string='Total Service Price', compute="_compute_service_price", store=True, default=0.0)
    half_advance_payment_before = fields.Float(string='Advance Payment 50% (Paid)', default=0.0)
    half_payment_after = fields.Float(string='50% Amount After Training Delivery (Not Paid)', default=0.0)

    training_course_ids = fields.One2many('training.course', 'lead_id', string='Training Courses')
    pro_service_ids = fields.One2many('pro.service', 'pro_lead_id', string='Professional Services')
    ticket_ids = fields.One2many('ticket.ticket', 'ticket_lead_id', string='Tickets')
    hotel_ids = fields.One2many('hotel.hotel', 'hotel_lead_id', string='Hotels')

    total_price_all = fields.Float(string="Total Amount", compute='_compute_total', default=0.0)
    visa = fields.Boolean(string="Visa")
    start_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")

    book_details_id = fields.Many2many('ir.attachment', 'doc_attach_rel4', 'doc_id', 'attach_id5',
                                       string="Booking Details",
                                       help='Attach document copy', copy=False)
    details = fields.Html(string="Details")
    cost = fields.Float(string="Cost", default=0.0)
    training_vendor = fields.Float(string="Partner Share", default=0.0)
    training_type = fields.Float(string="Training Cost", default=0.0)

    # Extra fields
    instructor_id = fields.Many2one('hr.employee', string="Instructor")
    descriptions = fields.Char(string='Description')
    ordering_partner_id = fields.Many2one('res.partner', string='Ordering Partner')
    training_id = fields.Many2one('product.template', string='Training Name')

    train_language = fields.Char(string='Training Language')
    location = fields.Selection([('Cisco U', 'Cisco U'), ('ILT', 'ILT'), ('VILT', 'VILT')])
    payment_method = fields.Selection([('cash', 'Cash'), ('clc', 'CLC')], default='cash')
    clcs_qty = fields.Float(string='CLCs Qty', default=0.0)

    # Extra Information Tab
    so_no = fields.Char(string='SO#')
    tr_expiry_date = fields.Date(string='Expiry Date')

    # CLC Details
    clc_cost = fields.Float(string="CLCs Cost", default=0.0)
    rate_card = fields.Float(string="Rate Card $", default=0.0)
    nilme_share = fields.Float(string="NIL ME Share $", default=0.0)

    # Logistics Tab
    instructor_logistics = fields.Char(string='Instructor Logistics')
    catering = fields.Selection([('NIL MM', 'NIL MN'), ('Others', 'Others')], string='Catering')

    @api.model
    def create(self, vals):
        """Ensure float fields only contain numeric values before creating a record"""
        float_fields = ["total_training_price", "total_service_price", "half_advance_payment_before",
                        "half_payment_after", "total_price_all", "cost", "training_vendor", "training_type",
                        "clcs_qty", "clc_cost", "rate_card", "nilme_share"]

        for field in float_fields:
            if field in vals and not isinstance(vals[field], (int, float)):
                vals[field] = 0.0  # Default to 0 if an invalid value is found
        return super(Lead, self).create(vals)

    def write(self, vals):
        """Ensure float fields only contain numeric values before updating a record"""
        float_fields = ["total_training_price", "total_service_price", "half_advance_payment_before",
                        "half_payment_after", "total_price_all", "cost", "training_vendor", "training_type",
                        "clcs_qty", "clc_cost", "rate_card", "nilme_share"]

        for field in float_fields:
            if field in vals and not isinstance(vals[field], (int, float)):
                vals[field] = 0.0  # Default to 0 if an invalid value is found
        return super(Lead, self).write(vals)

    def _compute_total(self):
        """Ensure total calculation does not fail if invalid data is present"""
        for rec in self:
            ticket_total = sum(ticket.price for ticket in rec.ticket_ids if isinstance(ticket.price, (int, float)))
            hotel_total = sum(hotel.price for hotel in rec.hotel_ids if isinstance(hotel.price, (int, float)))
            cost = rec.cost if isinstance(rec.cost, (int, float)) else 0.0
            rec.total_price_all = ticket_total + hotel_total + cost

    @api.depends('pro_service_ids.price')
    def _compute_service_price(self):
        """Ensure service price calculation is safe"""
        for rec in self:
            rec.total_service_price = sum(service.price for service in rec.pro_service_ids if isinstance(service.price, (int, float)))

    @api.depends('training_course_ids.price')
    def _compute_training_price(self):
        """Ensure training price calculation is safe"""
        for rec in self:
            rec.total_training_price = sum(course.price for course in rec.training_course_ids if isinstance(course.price, (int, float)))

class ProductProduct(models.Model):
    _inherit = 'product.template'

    cost_clc = fields.Char(string="Cost Clc")
    hyperlink = fields.Char(string="Hyper Link")

class HotelHotel(models.Model):
    _name = 'hotel.hotel'
    _description = 'Hotels'

    hotel_lead_id = fields.Many2one('crm.lead', string="Lead")
    hotel_id = fields.Many2one('hotel.description', string="Hotel")
    date_from = fields.Date(string="Date From")
    date_to = fields.Date(string="Date To")
    nights = fields.Char(string="Nights", compute='_compute_nights')
    price = fields.Float(string="Price with Tax", compute='_compute_total', default=0.0)

    def _compute_total(self):
        for rec in self:
            rec.price = rec.price or 0.0

    def _compute_nights(self):
        for rec in self:
            rec.nights = str((rec.date_to - rec.date_from).days) + " Nights" if rec.date_from and rec.date_to else ""

class TicketTicket(models.Model):
    _name = 'ticket.ticket'
    _description = 'Tickets'

    ticket_lead_id = fields.Many2one('crm.lead', string="Lead")
    airline_id = fields.Many2one('airline.airline', string="Airlines")
    origin_id = fields.Many2one('loca.loca', string="Origin")
    destination_id = fields.Many2one('loca.loca', string="Destination")
    price = fields.Float(string="Price with Taxes", default=0.0)

class AirlineAirline(models.Model):
    _name = 'airline.airline'
    _description = 'Airlines'

    name = fields.Char(string="Airline", required=True)

class LocaLoca(models.Model):
    _name = 'loca.loca'
    _description = 'Locations'

    name = fields.Char(string="Location", required=True)

class HotelDescription(models.Model):
    _name = 'hotel.description'
    _description = 'Hotel Description'

    name = fields.Char(string="Hotel", required=True)
