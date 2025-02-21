# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class Lead(models.Model):
    _inherit = 'crm.lead'

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
                                       string="Booking Details",
                                       help='You can attach the copy of your document', copy=False)
    details = fields.Html(string="Details")
    cost = fields.Float(string="Cost")
    training_vendor = fields.Char(string="Training Vendor")
    training_type = fields.Char(string="Training Type")

    # Extra
    instructor_id = fields.Many2one('hr.employee', string="Instructor")
    descriptions = fields.Char(string='Description')
    ordering_partner_id = fields.Many2one('res.partner', string='Ordering Partner')
    training_id = fields.Many2one('product.template', string='Training Name')

    train_language = fields.Char(string='Training Language')
    location = fields.Selection([('Cisco U', 'Cisco U'), ('ILT', 'ILT'), ('VILT', 'VILT')])
    payment_method = fields.Selection([('cash', 'Cash'), ('clc', 'CLC')], default='cash')
    clcs_qty = fields.Float(string='CLCs Qty')

    # Extra Information Tab
    clcs_qty = fields.Float(string='CLCs Qty')
    so_no = fields.Char(string='SO#')
    tr_expiry_date = fields.Date(string='Expiry Date')

    # ✅ Fixed: One2many field for Costs page
    cost_ids = fields.One2many('crm.lead.cost', 'lead_id', string="Costs")

    # Logistics Tab
    instructor_logistics = fields.Float(string='Venue')
    Uber = fields.Float(string='Uber')
    catering = fields.Float(string='Catering')

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
                rec.total_price_all = ticket_total + hotel_total + rec.cost + rec.instructor_logistics + rec.Uber + rec.catering
            else:
                rec.total_price_all = 0

    @api.depends('pro_service_ids.price')
    def _compute_service_price(self):
        for rec in self:
            rec.total_service_price = sum(rec.pro_service_ids.mapped('price')) if rec.pro_service_ids else 0

    @api.depends('training_course_ids.price')
    def _compute_training_price(self):
        for rec in self:
            rec.total_training_price = sum(rec.training_course_ids.mapped('price')) if rec.training_course_ids else 0


class CrmLeadCost(models.Model):
    _name = 'crm.lead.cost'
    _description = 'CRM Lead Costs'

    lead_id = fields.Many2one('crm.lead', string="Lead", ondelete='cascade')
    total_training_price = fields.Float(string="Total Training Price")
    cisco_cost = fields.Float(string="Cisco Training Cost")
    rate_card = fields.Float(string="Rate Card $")
    nilme_share = fields.Float(string="NIL ME Share $")
    par_share = fields.Float(string="Partner Share $")
    partner_l = fields.Selection([
        ('NIL LTD', 'NIL LTD'),
        ('NIL SA', 'NIL SA'),
        ('MIRA', 'MIRA'),
        ('Koeing', 'Koeing')
    ], string='Partner')
