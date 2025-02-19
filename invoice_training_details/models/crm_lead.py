# -*- coding: utf-8 -*-
from odoo import fields, models, api

# Inherit CRM Lead to include new fields
class Lead(models.Model):
    _inherit = 'crm.lead'

    training_name = fields.Char(string='Training Name')
    service_name = fields.Char(string='Service Name')
    total_training_price = fields.Float(string='Total Training Price', compute="_compute_training_price", store=True)
    total_service_price = fields.Float(string='Total Service Price', compute="_compute_service_price", store=True)
    half_advance_payment_before = fields.Float(string='Advance payment amount 50% (paid)')
    half_payment_after = fields.Float(string='50% Amount after Training Delivery (Not Yet Paid)')
    training_course_ids = fields.One2many('training.course', 'lead_id', string='Training Courses')
    pro_service_ids = fields.One2many('pro.service','pro_lead_id', string='Professional Services')
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
    training_vendor = fields.Char(string="Training Vendor")
    training_type = fields.Char(string="Training Type")
    
    # Add extra fields
    instructor_id = fields.Many2one('hr.employee', string="Instructor")
    descriptions = fields.Char(string='Description')
    ordering_partner_id = fields.Many2one('res.partner', string='Ordering Partner')
    training_id = fields.Many2one('product.template', string='Training Name')
    
    train_language = fields.Char(string='Training Language')
    location = fields.Selection([('Cisco U', 'Cisco U'), ('ILT', 'ILT'), ('VILT', 'VILT')])
    payment_method = fields.Selection([('cash', 'Cash'), ('clc', 'CLC')], default='cash')
    clcs_qty = fields.Float(string='CLCs Qty')
    
    # Extra information tab
    so_no = fields.Char(string='SO#')
    tr_expiry_date = fields.Date(string='Expiry Date')
    
    # CLC cost and margin fields
    clc_cost = fields.Char(string="CLCs Cost")
    rate_card = fields.Float(string="Rate Card $")
    nilme_share = fields.Float(string="NIL ME Share $")
    
    # Logistics tab
    instructor_logistics = fields.Char(string='Instructor Logistics')
    catering = fields.Selection([('NIL MM', 'NIL MM'), ('Others', 'Others')], string='Catering')
    
    # New CLC Fields
    training_cost = fields.Float(string="Training Cost")
    logistics_cost = fields.Float(string="Logistics Cost")
    
    # New fields for cost, share, and margin
    cisco_cost = fields.Float(string="Cisco Cost")
    partner_share = fields.Float(string="Partner Share")
    nil_me_share = fields.Float(string="NIL ME Share")
    other_costs = fields.Float(string="Other Costs")
    margin = fields.Float(string="Margin", compute='_compute_margin', store=True)
    
    @api.depends('total_price_all', 'cisco_cost', 'partner_share', 'nil_me_share', 'other_costs')
    def _compute_margin(self):
        for rec in self:
            # Margin is computed as the difference between the total price and total costs
            total_cost = rec.cisco_cost + rec.partner_share + rec.nil_me_share + rec.other_costs
            if rec.total_price_all:
                rec.margin = ((rec.total_price_all - total_cost) / rec.total_price_all) * 100
            else:
                rec.margin = 0
    
    def _compute_total(self):
        ticket_total = 0
        hotel_total = 0
        cost = 0
        for rec in self:
            if rec.ticket_ids and rec.hotel_ids:
                for ticket in rec.ticket_ids:
                    ticket_total += ticket.price
                for hotel in rec.hotel_ids:
                    hotel_total += hotel.price
                rec.total_price_all = ticket_total + hotel_total + rec.cost
            else:
                rec.total_price_all = 0

    @api.depends('pro_service_ids.price')
    def _compute_service_price(self):
        for rec in self:
            if rec.pro_service_ids:
                rec.total_service_price = sum(rec.pro_service_ids.mapped('price'))
            else:
                rec.total_service_price = 0
                
    @api.depends('training_course_ids.price')
    def _compute_training_price(self):
        for rec in self:
            if rec.training_course_ids:
                rec.total_training_price = sum(rec.training_course_ids.mapped('price'))
            else:
                rec.total_training_price = 0

    def _prepare_opportunity_quotation_context(self):
        quotation_context = super()._prepare_opportunity_quotation_context()
        quotation_context.update({
            'default_training_name': self.training_name,
            'default_training_course_ids': [(6, 0, self.training_course_ids.ids)],
            'default_pro_service_ids': [(6, 0, self.pro_service_ids.ids)],
            'default_clcs_qty': self.clcs_qty,
            'default_so_no': self.so_no,
            'default_tr_expiry_date': self.tr_expiry_date,
            'default_instructor_logistics': self.instructor_logistics,
            'default_catering': self.catering,
            'default_descriptions': self.descriptions,
            'default_ordering_partner': self.ordering_partner_id.id,
            'default_instructor_id': self.instructor_id.id,
            'default_training_id': self.training_id.id,
            'default_train_language': self.train_language,
            'default_location': self.location,
            'default_payment_method': self.payment_method,
            'default_clcs_qty': self.clcs_qty,
            'default_service_name': self.service_name,
            'default_hotel_ids': [(6, 0, self.hotel_ids.ids)],
            'default_ticket_ids': [(6, 0, self.ticket_ids.ids)],
            'default_visa': self.visa,
            'default_start_date': self.start_date,
            'default_to_date': self.to_date,
            'default_book_details_id': [(6, 0, self.book_details_id.ids)],
            'default_details': self.details,
            'default_cost': self.cost,
            'default_training_vendor': self.training_vendor,
            'default_training_type': self.training_type,
            'default_cisco_cost': self.cisco_cost,
            'default_partner_share': self.partner_share,
            'default_nil_me_share': self.nil_me_share,
            'default_other_costs': self.other_costs,
            'default_margin': self.margin,
        })
        return quotation_context


# Hotel Model
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
            rec.nights = str(duration.days) + ' Nights' if duration.days else '0 Nights'
            

# Ticket Model
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
    

# Airline Model
class AirlineAirline(models.Model):
    _name = 'airline.airline'
    _description = 'Airlines'
    
    name = fields.Char(string="Airline", required=True)
    

# Location Model
class LocaLoca(models.Model):
    _name = 'loca.loca'
    _description = 'Locations'
    
    name = fields.Char(string="Location", required=True)


# Flight Class Type Model
class FlightClassType(models.Model):
    _name = 'flight.class.type'
    _description = 'Classes'
    
    name = fields.Char(string="Class Type", required=True)


# Hotel Description Model
class HotelDescription(models.Model):
    _name = 'hotel.description'
    _description = 'Hotel Description'
    
    name = fields.Char(string="Hotel", required=True)


# Product Models
class ProductProduct(models.Model):
    _inherit = 'product.product'

    cost_clc = fields.Char(string="Cost Clc")
    hyperlink = fields.Char(string="Hyper Link")


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    cost_clc = fields.Char(string="Cost Clc")
    hyperlink = fields.Char(string="Hyper Link")

