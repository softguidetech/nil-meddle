# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api

# crm.lead Model - Inheriting and adding the One2many relationship
class Lead(models.Model):
    _inherit = 'crm.lead'

    # One2many relationship to link to the training.cost model
    training_cost_ids = fields.One2many('training.cost', 'lead_id', string="Training Costs")
    
    # Extra fields
    training_name = fields.Char(string='Training Name')
    service_name = fields.Char(string='Service Name')
    total_training_price = fields.Float(string='Total Training Price', compute="_compute_training_price", store=True)
    total_service_price = fields.Float(string='Total Service Price', compute="_compute_service_price", store=True)
    half_advance_payment_before = fields.Float(string='Advance payment amount 50% (paid)')
    half_payment_after = fields.Float(string='50% Amount after Training Delivery (Not Yet Paid)')
    training_course_ids = fields.One2many('training.course', 'lead_id', string='Training Courses')
    pro_service_ids = fields.One2many('pro.service', 'pro_lead_id', string='Professional Services')
    ticket_ids = fields.One2many('ticket.ticket', 'ticket_lead_id', string='Tickets')
    hotel_ids = fields.One2many('hotel.hotel', 'hotel_lead_id', string='Hotels')
    total_price_all = fields.Float(string="Total Amount", compute='_compute_total')
    visa = fields.Boolean(string="Visa")
    start_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")
    book_details_id = fields.Many2many('ir.attachment', 'doc_attach_rel4', 'doc_id', 'attach_id5', 
                                       string="Booking Details", help='You can attach the copy of your document', copy=False)
    details = fields.Html(string="Details")
    cost = fields.Float(string="Cost")

    instructor_id = fields.Many2one('hr.employee', string="Instructor")
    descriptions = fields.Char(string='Description')
    ordering_partner_id = fields.Many2one('res.partner', string='Ordering Partner')
    training_id = fields.Many2one('product.template', string='Training Name')

    train_language = fields.Char(string='Language')
    location = fields.Selection([('ILT', 'ILT'), ('VILT', 'VILT')])
    payment_method = fields.Selection([('cash', 'Cash'), ('clc', 'CLC')], default='cash')
    clcs_qty = fields.Float(string='CLCs Qty')

    # Extra Information Tab
    so_no = fields.Char(string='SO#')
    tr_expiry_date = fields.Date(string='Expiry Date')
    poref = fields.Char(string='PO Reference')
    invref = fields.Char(string='Invoice Reference')


# training.cost Model - This is the new model to store the cost details
class TrainingCost(models.Model):
    _name = 'training.cost'
    _description = 'Training Costs'

    lead_id = fields.Many2one('crm.lead', string="Lead")  # This creates the link to crm.lead
    clc_cost = fields.Float(string="Training Cost")
    rate_card = fields.Float(string="Rate Card $")
    nilme_share = fields.Float(string="NIL ME Share $")
    training_vendor = fields.Float(string="Training Vendor")
    training_type = fields.Float(string="Training Type")

    # Optional fields for logistics
    instructor_logistics = fields.Char(string='Instructor Logistics')
    catering = fields.Selection([('NIL MM', 'NIL MN'), ('Others', 'Others')], string='Catering')

    @api.depends('clc_cost', 'rate_card', 'nilme_share', 'training_vendor', 'training_type')
    def _compute_total(self):
        for rec in self:
            rec.total_price_all = rec.clc_cost + rec.rate_card + rec.nilme_share + rec.training_vendor + rec.training_type


# Other models for Hotels, Tickets, etc. (if needed)
class HotelHotel(models.Model):
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

    def _compute_total(self):
        for rec in self:
            rec.price = rec.price_without_tax + rec.tax

    def _compute_nights(self):
        for rec in self:
            duration = rec.date_to - rec.date_from
            rec.nights = str(duration.days) + " Nights"


class TicketTicket(models.Model):
    _name = 'ticket.ticket'
    _description = 'Tickets'

    ticket_lead_id = fields.Many2one('crm.lead', string="Lead")
    ticket_order_id = fields.Many2one('sale.order', string="Order")
    airline_id = fields.Many2one('airline.airline', string="Airlines")
    origin_id = fields.Many2one('loca.loca', string="Origin")
    destination_id = fields.Many2one('loca.loca', string="Destination")
    date = fields.Date(string="Date")
    duration = fields.Char(string="Duration")
    time_from = fields.Float(string="Available Time From")
    time_to = fields.Float(string="Available Time To")
    stop = fields.Char(string="Stop")
    class_type_id = fields.Many2one('flight.class.type', string="Class Type")
    currency_id = fields.Many2one('res.currency', string="Currency", required=True)
    price = fields.Monetary(string="Price with Taxes", required=True)
