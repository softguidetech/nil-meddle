from odoo import models, fields, api

class CostDetails(models.Model):
    _name = 'cost.details'
    _description = 'Cost Details'
    def _register_hook(self):
        """Dynamically modify the tree view to force column widths in Odoo."""
        view_id = self.env.ref('your_module.view_cost_details_tree', raise_if_not_found=False)
        if view_id:
            view_id.sudo().write({'arch_base': '''
                <tree editable="bottom">
                    <field name="learning_partner" string="Learning Partner" style="width: 200px;"/>
                    <field name="currency_id" string="Currency" style="width: 150px;"/>
                    <field name="training_vendor" string="Partner Share" style="width: 180px;"/>
                    <field name="total_price_all" string="Logistics Cost" style="width: 180px;"/>
                    <field name="clc_cost" string="Training Cost" style="width: 180px;"/>
                    <field name="margin1" string="Total Costs" style="width: 180px;"/>
                    <field name="nilme_share" string="NIL ME Share" style="width: 180px;"/>
                    <field name="margin" widget="percentage" string="Margin (%)" style="width: 150px;"/>
                </tree>
            '''})

        # Inject CSS dynamically in settings (forces Odoo to apply the new styling)
        css_code = """
            <style>
            .o_list_view .auto_spacing td {
                min-width: 150px !important;
                max-width: auto !important;
                white-space: nowrap !important;
                overflow: hidden !important;
                text-overflow: ellipsis !important;
            }
            .o_list_view .auto_spacing {
                table-layout: auto !important;
                width: 100% !important;
            }
            </style>
        """
        self.env['ir.ui.view'].sudo().create({
            'name': 'AutoSpacingCSS',
            'type': 'qweb',
            'arch': f'''<t t-name="AutoSpacingCSS">{css_code}</t>'''
        })

    cos_lead_id = fields.Many2one('crm.lead', string="Lead", ondelete='cascade')
    name = fields.Char(string="Cost Name")
    description = fields.Text(string="Description")
    price = fields.Float(string="Price")  # Make the price field optional
    currency_id = fields.Many2one('res.currency', string="Currency", required=True, default=lambda self: self.env.company.currency_id.id)

    # ✅ These cost fields now belong only to cost.details
    training_vendor = fields.Float(string="Partner Share")  
    total_price_all = fields.Float(string="Logistics Cost", compute='_compute_total')  
    margin1 = fields.Float(string="Total Costs", compute='_compute_margin1')
    clc_cost = fields.Float(string="Training Cost")
    rate_card = fields.Float(string="Partner Rate")  
    nilme_share = fields.Float(string="NIL ME Share $", compute='_compute_nilme_share')
    learning_partner = fields.Selection([
        ('Koeing', 'Koeing'),
        ('Mira', 'Mira'),
        ('NIL LTD', 'NIL LTD'),
        ('NIL SA', 'NIL SA')
    ], string='Learning Partner')
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

def _prepare_opportunity_quotation_context(self):
    quotation_context = super()._prepare_opportunity_quotation_context()
    quotation_context.update({
        'default_cos_lead_id': self.cos_lead_id.id,
        'default_name': self.name,
        'default_description': self.description,
        'default_price': self.price,
        'default_currency_id': self.currency_id.id,
        'default_training_vendor': self.training_vendor,
        'default_total_price_all': self.total_price_all,
        'default_margin1': self.margin1,
        'default_clc_cost': self.clc_cost,
        'default_rate_card': self.rate_card,
        'default_nilme_share': self.nilme_share,
        'default_learning_partner': self.learning_partner,
        'default_cost': self.cost,
        'default_margin': self.margin,
    })
    return quotation_context
