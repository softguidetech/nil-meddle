# -*- coding: utf-8 -*-

from odoo import api, models, fields


class SaleOrder(models.Model):
    _inherit = "sale.order"

    training_name = fields.Char(string='Training Name')
    service_name = fields.Char(string='Service Name')
    total_training_price = fields.Float(string='Total Training Price', compute="_compute_training_price", store=True)
    half_advance_payment_before = fields.Float(string='Advance payment amount 50% (paid)')
    half_payment_after = fields.Float(string='50% Amount after Training Delivery (Not Yet Paid)')
    training_course_ids = fields.One2many('training.course', 'sale_id', string='Training Courses')
    pro_service_ids = fields.One2many('pro.service','pro_sale_id',srting='Professional Services')
    
    #Add extera
    instructor_id = fields.Many2one('hr.employee',string="Instructor")
    descriptions = fields.Char(string='Description')
    # ordering_partner_id = fields.Many2one('res.partner',string='Ordering Partner')
    training_id = fields.Many2one('product.template',string='Training Name')
    train_language = fields.Char(string='Training Language')
    location = fields.Selection([('DXB','NIL DXB'),('KSA','NIL KSA'),('Venue','Venue'),('Customer Choice','Customer Choice')])
    where_location = fields.Char(string='Where?',default='Webex')
    payment_method = fields.Selection([('cash','Cash'),('clc','CLC')],default='cash')
    
    display_training_table = fields.Boolean(string='Display Training Table', help='display traning table in training invoice PDF.')
    display_signature = fields.Boolean(string='Display Signature', help='display signature in training invoice PDF.')
    display_stamp = fields.Boolean(string='Display Stamp', help='display Stamp in training invoice PDF.')
    display_ksa_qr = fields.Boolean(string='Display KSA QR', help='display KSA Qr in training invoice PDF.')
    
    # extra information tab
    clcs_qty = fields.Float(string='CLCs Qty')
    so_no = fields.Char(string='SO#')
    tr_expiry_date = fields.Date(string='Expiry Date')

    # logistics tab
    instructor_logistics = fields.Char(string='Instructor Logistics')
    catering = fields.Selection([('NIL MM','NIL MN'),('Others','Others')],string='Catering')
    
    bank_details = fields.Html(string='Bank Details',default='We kindly request you to transfer OR deposit cheque payment to below bank account details </br> Account Name: NIL Data Communications Middle East DMCC Emirates Islamic Bank JLT Branch - Dubai- UAE </br> Swiftcode: MEBLAEAD </br> Account Currency: USD </br> IBAN: AE690340003528215597102')
    term_and_cond = fields.Html(string='Term and conditions',default=' 1. PO Reference #: PCD-006-2024 </br> 2. PO Amendment PCD-006-2024 </br> 3. End customer name: Saudi Authority for Data and Artificial Intelligence, Saudi Arabia. </br>4. The invoice amount does not include VAT or Withholding tajes - it must be paid by Taqnia Cyber if any, without any charging or deduction from the invoice amount.5. Taqnia Cyber will pay the taxes to KSA authorities directly.</br> 6. Taqnia Cyber must bear Money transfers or bank charges on payment.</br>')
    @api.depends('training_course_ids.price')
    def _compute_training_price(self):
        for rec in self:
            rec.total_training_price = sum(rec.training_course_ids.mapped('price'))

    def _prepare_invoice(self):
        vals = super()._prepare_invoice()
        vals.update({
            'training_name': self.training_name,
            'half_advance_payment_before': self.half_advance_payment_before,
            'half_payment_after': self.half_payment_after,
            'training_course_ids': [(6, 0, self.training_course_ids.ids)],
            'pro_service_ids': [(6, 0, self.pro_service_ids.ids)],
            'clcs_qty': self.clcs_qty,
            'so_no': self.so_no,
            'tr_expiry_date': self.tr_expiry_date,
            'instructor_logistics': self.instructor_logistics,
            'catering': self.catering,
            # 'descriptions': self.descriptions,
            # 'ordering_partner_id': self.ordering_partner_id.id,
            # 'where_location': self.where_location,
            
            'instructor_id': self.instructor_id.id,
            'training_id': self.training_id.id,
            # 'train_language': self.train_language,
            # 'location': self.location,
            # 'payment_method': self.payment_method,
            'clcs_qty': self.clcs_qty,
            'service_name': self.service_name,
            'bank_details': self.bank_details,
            'term_and_cond': self.term_and_cond,
            
        })
        return vals
        
    # ks_qr_code = fields.Binary("KSA QR Code", compute="_compute_ksa_qr_code")

    # def generate_ksa_qr_code(self, seller_name, vat_number, invoice_date, total_amount, vat_amount):
    #     # Encode data in TLV format
    #     def encode_tlv(tag, value):
    #         value_bytes = value.encode('utf-8')
    #         return bytes([tag, len(value_bytes)]) + value_bytes

    #     qr_data = (
    #         encode_tlv(1, seller_name) +
    #         encode_tlv(2, vat_number) +
    #         encode_tlv(3, invoice_date) +
    #         encode_tlv(4, str(total_amount)) +
    #         encode_tlv(5, str(vat_amount))
    #     )

    #     # Generate QR code
    #     qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L)
    #     qr.add_data(base64.b64encode(qr_data).decode('utf-8'))
    #     qr.make(fit=True)

    #     # Convert QR code to image
    #     img = qr.make_image(fill_color="black", back_color="white")
    #     buffer = BytesIO()
    #     img.save(buffer, format="PNG")
    #     qr_code_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
    #     buffer.close()
    #     return qr_code_image

    # @api.depends('partner_id', 'date', 'amount_total', 'amount_tax')
    # def _compute_ksa_qr_code(self):
    #     for move in self:
    #         if move.move_type in ['out_invoice', 'out_refund'] and move.company_id.vat:
    #             move.ks_qr_code = self.generate_ksa_qr_code(
    #                 move.company_id.name,
    #                 move.company_id.vat,
    #                 move.invoice_date.strftime('%Y-%m-%d %H:%M:%S') if move.invoice_date else '',
    #                 move.amount_total,
    #                 move.amount_tax
    #             )
    #         else:
    #             move.ks_qr_code = False

    @api.depends('training_course_ids.price')
    def _compute_training_price(self):
        for rec in self:
            rec.total_training_price = sum(rec.training_course_ids.mapped('price'))

