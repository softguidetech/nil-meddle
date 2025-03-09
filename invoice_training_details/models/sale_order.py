# -*- coding: utf-8 -*-

from odoo import api, models, fields

class SaleOrder(models.Model):
    _inherit = "sale.order"

    training_name = fields.Char(string='Training Name')
    service_name = fields.Char(string='Service Name')
    total_training_price = fields.Monetary(string='Total Training Price', compute="_compute_training_price", store=True)
    total_service_price = fields.Float(string='Total Service Price', compute="_compute_service_price", store=True)
    half_advance_payment_before = fields.Monetary(string='Advance payment amount 50% (paid)')
    half_payment_after = fields.Monetary(string='50% Amount after Training Delivery (Not Yet Paid)')
    training_course_ids = fields.One2many('training.course', 'sale_id', string='Training Courses')
    pro_service_ids = fields.One2many('pro.service', 'pro_sale_id', string='Professional Services')
    
    # Add extra fields
    instructor_id = fields.Many2one('hr.employee', string="Instructor")
    descriptions = fields.Char(string='Description')
    training_id = fields.Many2one('product.template', string='Training Name')
    train_language = fields.Char(string='Training Language')
    location = fields.Selection([('Cisco U', 'Cisco U'), ('ILT', 'ILT'), ('VILT', 'VILT')])
    where_location = fields.Char(string='Where?')
    payment_method = fields.Selection([('cash', 'Cash'), ('clc', 'CLC')], default='cash')
    
    display_training_table = fields.Boolean(string='Display Training Table', help='Display training table in training invoice PDF.')
    display_signature = fields.Boolean(string='Display Signature', help='Display signature in training invoice PDF.')
    display_stamp = fields.Boolean(string='Display Stamp', help='Display stamp in training invoice PDF.')
    display_ksa_qr = fields.Boolean(string='Display KSA QR', help='Display KSA QR in training invoice PDF.')
    
    display_instructor = fields.Boolean(string='Display Instructor', help='Display instructor in training invoice PDF.')
    display_location = fields.Boolean(string='Display Location', help='Display location in training invoice PDF.')
    display_downpayment = fields.Boolean(string='Display Downpayment', help='Display downpayment in training invoice PDF.')
    display_total = fields.Boolean(string='Display Total Amount', help='Display total amount in training invoice PDF.')
    display_due_amount = fields.Boolean(string='Display Due Amount', help='Display due amount in training invoice PDF.')
    display_where = fields.Boolean(string="Display Where?")
    display_description = fields.Boolean(string="Display Description")
    
    # Additional fields
    ticket_ids = fields.One2many('ticket.ticket', 'ticket_order_id', string='Tickets')
    hotel_ids = fields.One2many('hotel.hotel', 'hotel_order_id', string='Hotels')
    total_price_all = fields.Float(string="Total Amount", compute='_compute_total')
    visa = fields.Boolean(string="Visa")
    start_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")
    book_details_id = fields.Many2many('ir.attachment', 'doc_attach_order', 'doc_id', 'attach_order_id',
                                       string="Booking Details",
                                       help='You can attach the copy of your document', copy=False)
    details = fields.Html(string="Details")
    cost = fields.Float(string="Cost")
    currency_total = fields.Float(string="Total in Currency", compute='_compute_cur_tot')
    
    training_vendor = fields.Char(string="Training Vendor")
    training_type = fields.Char(string="Training Type")
    
    @api.depends('amount_total', 'currency_id')
    def _compute_cur_tot(self):
        for rec in self:
            if rec.amount_total and rec.currency_id:
                rec.currency_total = float(rec.amount_total) / float(rec.currency_id.rate)
            else:
                rec.currency_total = 0
                
    @api.depends('ticket_ids.price', 'hotel_ids.price', 'cost')
    def _compute_total(self):
        for rec in self:
            ticket_total = sum(ticket.price for ticket in rec.ticket_ids) if rec.ticket_ids else 0
            hotel_total = sum(hotel.price for hotel in rec.hotel_ids) if rec.hotel_ids else 0
            rec.total_price_all = ticket_total + hotel_total + rec.cost
    
    # Extra information tab
    clcs_qty = fields.Float(string='CLCs Qty')
    so_no = fields.Char(string='SO#')
    tr_expiry_date = fields.Date(string='Expiry Date')

    # Logistics tab
    instructor_logistics = fields.Char(string='Instructor Logistics')
    catering = fields.Selection([('NIL MM', 'NIL MN'), ('Others', 'Others')], string='Catering')
    
    bank_details = fields.Html(string='Bank Details', default='We kindly request you to transfer OR deposit cheque payment to below bank account details </br> Account Name: NIL Data Communications Middle East DMCC Emirates Islamic Bank JLT Branch - Dubai- UAE </br> Swiftcode: MEBLAEAD </br> Account Currency: USD </br> IBAN: AE690340003528215597102')
    term_and_cond = fields.Html(string='Term and conditions', default='1. PO Reference #: PCD-006-2024 </br> 2. PO Amendment PCD-006-2024 </br> 3. End customer name: Saudi Authority for Data and Artificial Intelligence, Saudi Arabia. </br> 4. The invoice amount does not include VAT or Withholding taxes - it must be paid by Taqnia Cyber if any, without any charging or deduction from the invoice amount. 5. Taqnia Cyber will pay the taxes to KSA authorities directly. </br> 6. Taqnia Cyber must bear Money transfers or bank charges on payment.')
    
    @api.depends('pro_service_ids.price')
    def _compute_service_price(self):
        for rec in self:
            rec.total_service_price = sum(rec.pro_service_ids.mapped('price')) if rec.pro_service_ids else 0
                
    @api.depends('training_course_ids.price')
    def _compute_training_price(self):
        for rec in self:
            rec.total_training_price = sum(rec.training_course_ids.mapped('price')) if rec.training_course_ids else 0
                
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
            'instructor_id': self.instructor_id.id,
            'training_id': self.training_id.id,
            'service_name': self.service_name,
            'bank_details': self.bank_details,
            'term_and_cond': self.term_and_cond,
            'training_vendor': self.training_vendor,
            'training_type': self.training_type,
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
            
    def synch_order(self):
        l = []
       
        for rec in self.training_course_ids:
            val = {

                'product_id': rec.training_id.id,
                # 'product_id': rec.training_id.id,
                'name': rec.training_id.name,
                'product_uom_qty': 1,
                'price_unit': rec.price,
                # 'order_id': self.id,
                
            }
            l.append((0, 0, val))
            
        
        self.write({'order_line': []})
        self.write({'order_line': l})
            
    def synch_pro_order(self):
        l = []
       
        for rec in self.pro_service_ids:
            val = {

                'product_id': rec.training_id.id,
                # 'product_id': rec.training_id.id,
                'name': rec.training_id.name,
                'product_uom_qty': 1,
                'price_unit': rec.price,
                # 'order_id': self.id,
                
            }
            l.append((0, 0, val))
            
        
        self.write({'order_line': []})
        self.write({'order_line': l})
            
