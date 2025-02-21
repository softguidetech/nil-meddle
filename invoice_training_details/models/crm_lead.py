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
    pro_service_ids = fields.One2many('pro.service','pro_lead_id', string='Professional Services')
    ticket_ids = fields.One2many('ticket.ticket','ticket_lead_id',string='Tickets')
    hotel_ids = fields.One2many('hotel.hotel','hotel_lead_id',string='Hotels')
    total_price_all = fields.Float(string="Total Amount",compute='_compute_total')
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
    cost_vendor = fields.Char(string="Cost Vendor")
    total_cost_price = fields.Float(string='Total Cost Price', compute="_compute_total_cost_price", store=True)
    
    # Extra fields
    instructor_id = fields.Many2one('hr.employee', string="Instructor")
    ordering_partner_id = fields.Many2one('res.partner', string='Ordering Partner')
    training_id = fields.Many2one('product.template', string='Training Name')
    train_language = fields.Char(string='Training Language')
    location = fields.Selection([('Cisco U','Cisco U'),('ILT','ILT'),('VILT','VILT')])
    payment_method = fields.Selection([('cash','Cash'),('clc','CLC')], default='cash')
    clcs_qty = fields.Float(string='CLCs Qty')
    so_no = fields.Char(string='SO#')
    tr_expiry_date = fields.Date(string='Expiry Date')
    clc_cost = fields.Float(string="CLCs Cost")
    rate_card = fields.Float(string="Rate Card $")
    nilme_share = fields.Float(string="NIL ME Share $")
    cisco_training_cost = fields.Float(string="Cisco Training Cost")
    partner = fields.Selection([
        ('koenig', 'Koenig'),
        ('nil_ltd', 'NIL LTD'),
        ('nil_sa', 'NIL SA'),
        ('mira', 'Mira')
    ], string="Partner")

    costs_line_ids = fields.One2many('cost.details', 'lead_id', string='Cost Details')
    
    @api.depends('costs_line_ids.clc_cost')
    def _compute_total_cost_price(self):
        for rec in self:
            rec.total_cost_price = sum(rec.costs_line_ids.mapped('clc_cost'))

class CostDetails(models.Model):
    _name = 'cost.details'
    _description = 'Cost Details'

    lead_id = fields.Many2one('crm.lead', string="Lead")
    clc_cost = fields.Float(string="CLCs Cost")
    rate_card = fields.Float(string="Rate Card $")
    nilme_share = fields.Float(string="NIL ME Share $")
    cisco_training_cost = fields.Float(string="Cisco Training Cost")
    partner = fields.Selection([
        ('koenig', 'Koenig'),
        ('nil_ltd', 'NIL LTD'),
        ('nil_sa', 'NIL SA'),
        ('mira', 'Mira')
    ], string="Partner")
