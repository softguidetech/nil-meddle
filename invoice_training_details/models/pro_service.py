# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools
from datetime import datetime
from odoo.exceptions import ValidationError

class ProService(models.Model):
    _name = "pro.service"
    _description = 'Propfessional Services'

    name = fields.Char(string='Service Name',)
    no_of_student = fields.Integer(string='No of Student')
    duration = fields.Char(string='Duration',)
    ordering_partner_id = fields.Many2one("res.partner", string="Ordering Partner")
    end_customer_id = fields.Many2one("res.partner", string="End Customer")
    training_date_start = fields.Date(string='Training Date start')
    training_date_end = fields.Date(string='Delivery Date')
    price = fields.Float(string='Total', readonly=False)
    pro_move_id = fields.Many2one('account.move', string='Move')
    pro_lead_id = fields.Many2one('crm.lead', string='Lead')
    pro_sale_id = fields.Many2one('sale.order', string='Sale Order')
    
    # instructor_id = fields.Many2one('hr.employee',string="Instructor")
    descriptions = fields.Char(string='Description')
    wor_hour_number = fields.Float(string='Qty')
    hourly_rate = fields.Float(string='Unit Price')
    training_id = fields.Many2one('product.product',string='Service Name')
    nil_custom_title = fields.Char(
        string='Custom Title',
        help='Optional: write any column heading you want to use in the PS report.',
    )
    nil_custom_value = fields.Char(
        string='Custom Value',
        help='Optional: enter the value matching your custom column heading.',
    )
    train_language = fields.Char(string='Language')
    location = fields.Selection([('DXB','NIL DXB'),('KSA','NIL KSA'),('Venue','Venue'),('Customer Choice','Customer Choice')])
    where_location = fields.Char(string='Project Location',default='Webex')
    payment_method = fields.Selection([('cash','Cash'),('clc','CLC')],default='cash')
    clcs_qty = fields.Float(string='CLCs Qty')
    default_item_code = fields.Char(related='training_id.default_code',string='Internal Ref')
    requester = fields.Char(string='Requester')
    end_customer = fields.Char(string='End Client')
    con_per = fields.Char(string='Contact Person')
    cisco_am = fields.Char(string='Cisco Account Manager')
    cost_clc = fields.Char(related='training_id.product_tmpl_id.cost_clc',string="Cost Clc")
    hyperlink = fields.Char(related='training_id.product_tmpl_id.hyperlink',string="Hyper Link")
    
    @api.onchange('wor_hour_number', 'hourly_rate')
    def _onchange_nil_ps_line_total(self):
        """Update the inline list immediately while Qty / Unit Price are edited."""
        for service in self:
            service.price = (service.wor_hour_number or 0.0) * (service.hourly_rate or 0.0)

    @api.model_create_multi
    def create(self, vals_list):
        """Compute totals for new lines; preserve legacy price-only imports."""
        prepared = []
        for values in vals_list:
            vals = dict(values)
            if 'wor_hour_number' in vals or 'hourly_rate' in vals:
                vals['price'] = (
                    (vals.get('wor_hour_number') or 0.0)
                    * (vals.get('hourly_rate') or 0.0)
                )
            prepared.append(vals)
        return super().create(prepared)

    def write(self, vals):
        """Only reprice lines whose quantity or rate was explicitly edited.

        Historical service lines and posted invoices are never bulk-repriced
        merely because the module is upgraded or another field changes.
        """
        if not ({'wor_hour_number', 'hourly_rate'} & vals.keys()):
            return super().write(vals)

        for service in self:
            write_vals = dict(vals)
            qty = write_vals.get('wor_hour_number', service.wor_hour_number) or 0.0
            unit_price = write_vals.get('hourly_rate', service.hourly_rate) or 0.0
            write_vals['price'] = qty * unit_price
            super(ProService, service).write(write_vals)
        return True

    # def _compute_date(self):
        
    #     duration = 0
    #     for rec in self:
    #         duration = rec.training_date_end - rec.training_date_start
    #         days = str(duration).replace(', 0:00:00','')
    #         rec.duration = days
           
