# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import qrcode
from io import BytesIO
from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = "account.move"

    training_name = fields.Char(string='Training Name')
    service_name = fields.Char(string='Service Name')
    total_training_price = fields.Monetary(string='Total Training Price', compute="_compute_training_price", store=True)
    half_advance_payment_before = fields.Monetary(string='Advance payment amount 50% (paid)')
    half_payment_after = fields.Monetary(string='50% Amount after Training Delivery (Not Yet Paid)')
    training_course_ids = fields.One2many('training.course', 'move_id', string='Training Courses')
    pro_service_ids = fields.One2many('pro.service','pro_move_id',srting='Professional Services')
    invoice_payment_am = fields.Monetary(string="Amount Paid",compute='_compute_am_paid')
    invoice_payment_per = fields.Float(string="Amount Paid Percentage %",compute='_compute_am_paid_per')
    
    display_training_table = fields.Boolean(string='Display Training Table', help='display traning table in training invoice PDF.')
    display_signature = fields.Boolean(string='Display Signature', help='display signature in training invoice PDF.')
    display_stamp = fields.Boolean(string='Display Stamp', help='display Stamp in training invoice PDF.')
    display_ksa_qr = fields.Boolean(string='Display KSA QR', help='display KSA Qr in training invoice PDF.')
    
    
    display_instructor = fields.Boolean(string='Display Instructor', help='display Instructor in training invoice PDF.')
    display_location = fields.Boolean(string='Display Location', help='display Location in training invoice PDF.')
    display_downpayment = fields.Boolean(string='Display Downpayment', help='display Downpayment in training invoice PDF.')
    display_total = fields.Boolean(string='Display Total Amount', help='display Total amount in training invoice PDF.')
    display_due_amount = fields.Boolean(string='Display Due Amount', help='display Due in training invoice PDF.')
    display_where = fields.Boolean(string="Display Where?")
    display_description = fields.Boolean(string="Display Description")
    
    #Add extera
    instructor_id = fields.Many2one('hr.employee',string="Instructor")
    descriptions = fields.Char(string='Description')
    # ordering_partner_id = fields.Many2one('res.partner',string='Ordering Partner')
    training_id = fields.Many2one('product.template',string='Training Name')
    train_language = fields.Char(string='Training Language')
    location = fields.Selection([('DXB','NIL DXB'),('KSA','NIL KSA'),('Venue','Venue'),('Customer Choice','Customer Choice')])
    where_location = fields.Char(string='Where?',default='Webex')
    payment_method = fields.Selection([('cash','Cash'),('clc','CLC')],default='cash')
    
    # extra information tab
    clcs_qty = fields.Float(string='CLCs Qty')
    so_no = fields.Char(string='SO#')
    tr_expiry_date = fields.Date(string='Expiry Date')

    # logistics tab
    instructor_logistics = fields.Char(string='Instructor Logistics')
    catering = fields.Selection([('NIL MM','NIL MN'),('Others','Others')],string='Catering')

    ks_qr_code = fields.Binary("KSA QR Code", compute="_compute_ksa_qr_code")
    
    bank_details = fields.Html(string='Bank Details')
    term_and_cond = fields.Html(string='Term and conditions')
    currency_total = fields.Float(string="Total in Currency",comput='_compute_cur_tot')
    
    def _compute_cur_tot(self):
        total = 0
        for rec in self:
            if rec.amount_total and rec.currency_id:
                rec.currency_total = rec.amount_total * rec.currency_id.rate
            else:
                rec.currency_total = 0
        
        
    def _compute_am_paid_per(self):
        per = 0
        for rec in self:
            if rec.invoice_payment_am > 0  and rec.amount_total > 0:
                per = rec.invoice_payment_am / rec.amount_total
                rec.invoice_payment_per = per * 100
            else:
                rec.invoice_payment_per = 0
            
    def _compute_am_paid(self):
        for rec in self:
            if rec.amount_residual and rec.amount_total:
                rec.invoice_payment_am = rec.amount_total - rec.amount_residual
            else:
                rec.invoice_payment_am = 0
    
    def generate_ksa_qr_code(self, seller_name, vat_number, invoice_date, total_amount, vat_amount):
        # Encode data in TLV format
        def encode_tlv(tag, value):
            value_bytes = value.encode('utf-8')
            return bytes([tag, len(value_bytes)]) + value_bytes

        qr_data = (
            encode_tlv(1, seller_name) +
            encode_tlv(2, vat_number) +
            encode_tlv(3, invoice_date) +
            encode_tlv(4, str(total_amount)) +
            encode_tlv(5, str(vat_amount))
        )

        # Generate QR code
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L)
        qr.add_data(base64.b64encode(qr_data).decode('utf-8'))
        qr.make(fit=True)

        # Convert QR code to image
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_code_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
        buffer.close()
        return qr_code_image

    @api.depends('partner_id', 'invoice_date', 'amount_total', 'amount_tax')
    def _compute_ksa_qr_code(self):
        for move in self:
            if move.move_type in ['out_invoice', 'out_refund'] and move.company_id.vat:
                move.ks_qr_code = self.generate_ksa_qr_code(
                    move.company_id.name,
                    move.company_id.vat,
                    move.invoice_date.strftime('%Y-%m-%d %H:%M:%S') if move.invoice_date else '',
                    move.amount_total,
                    move.amount_tax
                )
            else:
                move.ks_qr_code = False

    @api.depends('training_course_ids.price')
    def _compute_training_price(self):
        for rec in self:
            rec.total_training_price = sum(rec.training_course_ids.mapped('price'))
        
    def synch_order(self):
        l = []
        for rec in self.training_course_ids:
            val = {

                'product_id': rec.training_id.id,
                'quantity': 1,
                'price_unit': rec.price,
                
            }
            l.append((0, 0, val))
        self.write({'invoice_line_ids': l})
            
            
                  
