# -*- coding: utf-8 -*-

from odoo import api, models, fields


class SaleOrder(models.Model):
    _inherit = "sale.order"

    training_name = fields.Char(string='Training Name')
    service_name = fields.Char(string='Service Name')
    total_training_price = fields.Monetary(string='Total Training Price', compute="_compute_training_price", store=True)
    total_service_price = fields.Float(string='Total Servicr Price', compute="_compute_service_price", store=True)
    half_advance_payment_before = fields.Monetary(string='Advance payment amount 50% (paid)')
    half_payment_after = fields.Monetary(string='50% Amount after Training Delivery (Not Yet Paid)')
    training_course_ids = fields.One2many('training.course', 'sale_id', string='Training Courses')
    pro_service_ids = fields.One2many('pro.service','pro_sale_id',srting='Professional Services')
    cos_lead_id = fields.Many2one('some.model', string="Cos Lead")


    venue = fields.Float(string='Venue')
    cost_details_ids = fields.One2many('cost.details', 'cos_lead_id', string="Costs Details")
    margin1 = fields.Float(string="Total Costs", compute='_compute_margin1')
    learnig_partner = fields.Selection([('Koeing','Koeing'),('NIL LTD','NIL LTD'),('NIL SA','NIL SA')])
    currency_id = fields.Many2one('res.currency', string="Currency", required=True, default=lambda self: self.env.company.currency_id.id)
    training_vendor = fields.Float(string="Partner Share")  
    total_price_all = fields.Float(string="Logistics Cost", compute='_compute_total')  
    margin1 = fields.Float(string="Total Costs", compute='_compute_margin1')
    clc_cost = fields.Float(string="Training Cost")
    rate_card = fields.Float(string="Partner Rate")  
    nilme_share = fields.Float(string="NIL ME Share $", compute='_compute_nilme_share')
    cost = fields.Float(string="Cost", compute='_compute_total')
    margin = fields.Float(string="Margin (%)", compute='_compute_margin')  # New field with percentage label

    @api.depends('cos_lead_id.ticket_ids.price', 'cos_lead_id.hotel_ids.price', 'cos_lead_id.cost_details_ids.price', 'cos_lead_id.instructor_logistics', 'cos_lead_id.venue', 'cos_lead_id.ctrng', 'cos_lead_id.uber')
    def _compute_total(self):
        for rec in self:
            ticket_total = sum(ticket.price for ticket in rec.cos_lead_id.ticket_ids) if rec.cos_lead_id.ticket_ids else 0
            hotel_total = sum(hotel.price for hotel in rec.cos_lead_id.hotel_ids) if rec.cos_lead_id.hotel_ids else 0
            cost_details_total = sum(cost.price for cost in rec.cos_lead_id.cost_details_ids) if rec.cos_lead_id.cost_details_ids else 0
            instructor_logistics = float(rec.cos_lead_id.instructor_logistics) if rec.cos_lead_id.instructor_logistics else 0
            venue = rec.cos_lead_id.venue if rec.cos_lead_id.venue else 0
            catering = rec.cos_lead_id.ctrng if rec.cos_lead_id.ctrng else 0
            uber = rec.cos_lead_id.uber if rec.cos_lead_id.uber else 0

            total = ticket_total + hotel_total + cost_details_total + instructor_logistics + venue + catering + uber
            rec.total_price_all = total
            rec.cost = total  # Calculate the cost field

    @api.depends('training_vendor', 'total_price_all', 'clc_cost')
    def _compute_margin1(self):
        for record in self:
            record.margin1 = (record.training_vendor or 0) + (record.total_price_all or 0) + (record.clc_cost or 0)

    @api.depends('margin1', 'cos_lead_id.total_training_price')
    def _compute_nilme_share(self):
        for record in self:
            record.nilme_share = (record.cos_lead_id.total_training_price or 0) - (record.margin1 or 0)

    @api.depends('margin1', 'cos_lead_id.total_training_price')
    def _compute_margin(self):
        for record in self:
            total_training_price = record.cos_lead_id.total_training_price or 1  # Avoid division by zero
            record.margin = ((record.nilme_share or 0) / total_training_price)



    
    #Add extera
    instructor_id = fields.Many2one('hr.employee',string="Instructor")
    descriptions = fields.Char(string='Description')
    # ordering_partner_id = fields.Many2one('res.partner',string='Ordering Partner')
    training_id = fields.Many2one('product.template',string='Training Name')
    train_language = fields.Char(string='Training Language')
    location = fields.Selection([('Cisco U','Cisco U'),('ILT','ILT'),('VILT','VILT')])
    where_location = fields.Char(string='Where?')
    payment_method = fields.Selection([('cash','Cash'),('clc','CLC')],default='cash')
    
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
    
    # 
    ticket_ids = fields.One2many('ticket.ticket','ticket_order_id',string='Tickets')
    hotel_ids = fields.One2many('hotel.hotel','hotel_order_id',string='Hotels')
    total_price_all = fields.Float(string="Total Amount",compute='_compute_total')
    visa = fields.Boolean(string="Visa")
    start_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")
    book_details_id = fields.Many2many('ir.attachment', 'doc_attach_order', 'doc_id', 'attach_order_id',
                                         string="Booking Details",
                                         help='You can attach the copy of your document', copy=False)
    details = fields.Html(string="Details")
    cost = fields.Float(string="Cost")
    currency_total = fields.Float(string="Total in Currency",compute='_compute_cur_tot')
    
    training_vendor = fields.Char(string="Training Vendor")
    training_type = fields.Char(string="Training Type")
    
    @api.depends('amount_total', 'currency_id')
    def _compute_cur_tot(self):
        total = 0
        for rec in self:
            if rec.amount_total and rec.currency_id:
                rec.currency_total = float(rec.amount_total) / float(rec.currency_id.rate)
                # round(rec.currency_total,2)
            # raise ValidationError(rec.currency_total)
            else:
                rec.currency_total = 0
                
    def _compute_total(self):
        ticket_total =0
        hotel_toal=0
        cost = 0
        for rec in self:
            if rec.ticket_ids and rec.hotel_ids:
                for ticket in rec.ticket_ids:
                    ticket_total+=ticket.price
                for hotel in rec.hotel_ids:
                    hotel_toal+=hotel.price
                rec.total_price_all = ticket_total + hotel_toal + rec.cost
            else:
                rec.total_price_all = 0
    
    # extra information tab
    clcs_qty = fields.Float(string='Customer CLCs Qty')
    so_no = fields.Char(string='SO#')
    tr_expiry_date = fields.Date(string='Expiry Date')
    poref = fields.Char(string='PO Ref:')
    invref = fields.Char(string='Invoice Ref:')

    # logistics tab
    instructor_logistics = fields.Char(string='Instructor Logistics')
    uber = fields.Float(string='Uber')
    ctrng = fields.Float(string='Catering')  # Now it's manually editable
    bank_details = fields.Html(string='Bank Details',default='We kindly request you to transfer OR deposit cheque payment to below bank account details </br> Account Name: NIL Data Communications Middle East DMCC Emirates Islamic Bank JLT Branch - Dubai- UAE </br> Swiftcode: MEBLAEAD </br> Account Currency: USD </br> IBAN: AE690340003528215597102')
    term_and_cond = fields.Html(string='Term and conditions',default=' 1. PO Reference #: PCD-006-2024 </br> 2. PO Amendment PCD-006-2024 </br> 3. End customer name: Saudi Authority for Data and Artificial Intelligence, Saudi Arabia. </br>4. The invoice amount does not include VAT or Withholding tajes - it must be paid by Taqnia Cyber if any, without any charging or deduction from the invoice amount.5. Taqnia Cyber will pay the taxes to KSA authorities directly.</br> 6. Taqnia Cyber must bear Money transfers or bank charges on payment.</br>')
    
    @api.depends('pro_service_ids.price')
    def _compute_service_price(self):
        for rec in self:
            if rec.training_course_ids:
                rec.total_service_price = sum(rec.training_course_ids.mapped('price'))
            
            else:
                rec.total_service_price = 0
                
    @api.depends('training_course_ids.price')
    def _compute_training_price(self):
        for rec in self:
            if rec.training_course_ids:
                rec.total_training_price = sum(rec.training_course_ids.mapped('price'))
            else:
                rec.total_training_price = 0
                
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
            
