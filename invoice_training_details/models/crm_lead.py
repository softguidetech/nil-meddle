# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api

class Lead(models.Model):
    _inherit = 'crm.lead'

    training_name = fields.Char(string='Training Name')
    venue = fields.Float(string='Venue')
    service_name = fields.Char(string='Service Name')
    total_training_price = fields.Float(string='Total Training Price', compute="_compute_training_price", store=True)
    total_service_price = fields.Float(string='Total Service Price', compute="_compute_service_price", store=True)
    half_advance_payment_before = fields.Float(string='Advance payment amount 50% (paid)')
    half_payment_after = fields.Float(string='50% Amount after Training Delivery (Not Yet Paid)')
    training_course_ids = fields.One2many('training.course', 'lead_id', string='Training Courses')
    pro_service_ids = fields.One2many('pro.service', 'pro_lead_id', string='Professional Services')
    ticket_ids = fields.One2many('ticket.ticket', 'ticket_lead_id', string='Tickets')
    hotel_ids = fields.One2many('hotel.hotel', 'hotel_lead_id', string='Hotels')
    cost_details_ids = fields.One2many('cost.details', 'cost_lead_id', string="Cost Details")
    total_price_all = fields.Float(string="Total Logistics", compute='_compute_total')
    visa = fields.Boolean(string="Visa")
    start_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")
    book_details_id = fields.Many2many('ir.attachment', 'doc_attach_rel4', 'doc_id', 'attach_id5',
                                       string="Booking Details",
                                       help='You can attach the copy of your document', copy=False)
    details = fields.Html(string="Details")
    cost = fields.Float(string="Cost")
    training_vendor = fields.Float(string="Partner Share")
    training_type = fields.Float(string="Logistics Cost")
    margin1 = fields.Float(string="Margin 1", compute='_compute_margin1')

    @api.depends('clc_cost', 'rate_card', 'total_price_all')
    def _compute_margin1(self):
        for record in self:
            record.margin1 = record.clc_cost + record.rate_card + record.total_price_all

    # Add extra
    instructor_id = fields.Many2one('hr.employee', string="Instructor")
    descriptions = fields.Char(string='Description')
    ordering_partner_id = fields.Many2one('res.partner', string='Ordering Partner')
    training_id = fields.Many2one('product.template', string='Training Name')
    train_language = fields.Char(string='Language')
    location = fields.Selection([('ILT', 'ILT'), ('VILT', 'VILT')])
    payment_method = fields.Selection([('cash', 'Cash'), ('clc', 'CLC')], default='cash')
    clcs_qty = fields.Float(string='CLCs Qty')
    learnig_partner = fields.Selection([('Koeing', 'Koeing'), ('NIL LTD', 'NIL LTD'), ('NIL SA', 'NIL SA')])

    # extra information tab
    clcs_qty = fields.Float(string='Customer CLCs Qty')
    so_no = fields.Char(string='SO#')
    tr_expiry_date = fields.Date(string='Expiry Date')
    poref = fields.Char(string='PO Ref:')
    invref = fields.Char(string='Invoice Ref:')

    clc_cost = fields.Float(string="Training Cost")
    rate_card = fields.Float(string="Partner Share")
    nilme_share = fields.Float(string="NIL ME Share $")

    # logistics tab
    instructor_logistics = fields.Char(string='Instructor Logistics')
    uber = fields.Float(string='Uber')
    catering = fields.Selection([('NIL MM', 'NIL MN'), ('Others', 'Others')], string='Catering')
    ctrng = fields.Float(string='Catering')  # Now it's manually editable

   @api.depends('ticket_ids.price',
                'hotel_ids.price',
                'cost',
                'instructor_logistics',
                'venue',
                'ctrng',
                'uber')

   def _compute_total(self):
        for rec in self:
            ticket_total=sum(ticket.price for ticket in rec.ticket_ids) if rec.ticket_ids else 0
            hotel_total=sum(hotel.price for hotel in rec.hotel_ids) if rec.hotel_ids else 0
            instructor_logistics=rec.instructor_logistics if isinstance(rec.instructor_logistics, (int, float)) else 0
            venue=rec.venue if isinstance(rec.venue, (int, float)) else 0
            catering=rec.ctrng if isinstance(rec.ctrng, (int, float)) else 0
            uber=rec.uber if isinstance(rec.uber, (int, float)) else 0
            rec.total_price_all=ticket_total + hotel_total + rec.cost + instructor_logistics + venue + catering + uber

   @api.depends('pro_service_ids.price')

   def _compute_service_price(self):
        for rec in self:
            if rec.pro_service_ids:
                rec.total_service_price=sum(rec.pro_service_ids.mapped('price'))
            else:
                rec.total_service_price=0

   @api.depends('training_course_ids.price')

   def _compute_training_price(self):
        for rec in self:
            if rec.training_course_ids:
                rec.total_training_price=sum(rec.training_course_ids.mapped('price'))
            else:
                rec.total_training_price=0

   def _prepare_opportunity_quotation_context(self):
        quotation_context=super()._prepare_opportunity_quotation_context()
        quotation_context.update({
            default_training_name: self.training_name,
            default_training_course_ids: [(6, 0, self.training_course_ids.ids)],
            default_pro_service_ids: [(6, 0, self.pro_service_ids.ids)],
            default_clcs_qty: self.clcs_qty,
            default_so_no: self.so_no,
            default_tr_expiry_date: self.tr_expiry_date,
            default_instructor_logistics: self.instructor_logistics,
            default_catering: str(self.catering),
            default_ctrng: self.ctrng,
            default_descriptions: self.descriptions,
            default_ordering_partner: self.ordering_partner_id.id,
            default_instructor_id: self.instructor_id.id,
            default_training_id: self.training_id.id,
            default_train_language: self.train_language,
            default_location: self.location,
            default_learnig_partner: self.learnig_partner,
            default_margin1: self.margin1,
            default_uber: self.uber,
            default_payment_method: self.payment_method,
            default_clcs_qty: self.clcs_qty,
            default_service_name: self.service_name,
            default_hotel_ids: [(6, 0, self.hotel_ids.ids)],
            default_ticket_ids: [(6, 0, self.ticket_ids.ids)],
            default_cost_details_ids,
            default_visa: self.visa,
            default_start_date: self.start_date,
            default_to_date: self.to_date,
            default_venue: self.venue,
            default_book_details_id: [(6, 0, self.book_details_id.ids)],
            default_details: self.details,
            default_cost: self.cost,
            default_training_vendor: self.training_vendor,
           })
        return quotation_context

class CostDetails(models.Model):
   _name:str ='cost.details'
   _description:str ='Cost Details'

   lead_id:int=fields.Many2one(
       crm.lead,
       string:str ="Lead",
       required=True,
       ondelete:str ='cascade')

   learnig_partner:str=fields.Selection([('Koeing',
                                          str ='Koeing'),
                                         ('NIL LTD',
                                          str ='NIL LTD'),
                                         ('NIL SA',
                                          str ='NIL SA')],
                                        string:str ="Learning Partner")

   clc_cost:int=fields.Float(
       string:str ="Training Cost")

   rate_card:int=fields.Float(
       string:str ="Partner Share")

   nilme_share:int=fields.Float(
       string:str ="NIL ME Share $")

   training_vendor:int=fields.Float(
       string:str ="Partner Share")

   total_price_all:int=fields.Float(
       string:str ="Total Price")

   margin1:int=fields.Float(
       string:str ="Margin")

class HotelHotel(models.Model):
   _name:str ='hotel.hotel'
   _description:str ='Hotels'

   hotel_lead_id:int=fields.Many2one(
       crm.lead,
       string:str ="Lead")

   hotel_order_id:int=fields.Many2one(
       sale.order,
       string:str ="Order")

   hotel_id:int=fields.Many2one(
       hotel.description,
       string:str ="Hotel")

   date_from:int=fields.Date(
       string:str ="Date From")

   date_to:int=fields.Date(
       string:str ="Date To")

   nights:int=fields.Char(
       string:str ="Nights",
       compute:str ='_compute_nights')

   location:int=fields.Char(
       string:str ="Location")

   pax:int=fields.Char(
       string:str ="PAX")

   des:int=fields.Char(
       string:str ="Description")

   room_type:int=fields.Char(
       string:str ="Room Type")

   currency_id:int=fields.Many2one(
       res.currency,
       required=True)

def _compute_total(self):
        for rec in:
           price_without_tax+tax

def _compute_nights(self):
        duration:int+=0
        for rec in:
           duration+=rec.date_to - rec.date_from
           days=str
