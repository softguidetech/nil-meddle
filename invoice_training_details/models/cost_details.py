from odoo import models, fields, api

class CostDetails(models.Model):
    _inherit = 'cost.details'  # Ensure the model extends correctly

    def _register_hook(self):
        """Modify the Cost Details tree view inside the CRM Lead form."""
        view_id = self.env.ref('crm.crm_lead_view_form', raise_if_not_found=False)  # 🔥 FIXED: Correctly references the CRM Lead form

        if view_id:
            view_id.sudo().write({'arch_base': '''
                <form>
                    <sheet>
                        <group>
                            <notebook>
                                <page string="Cost Details">
                                    <field name="cost_details_ids">
                                        <tree editable="bottom">
                                            <field name="learning_partner" string="Learning Partner" colspan="3"/>
                                            <field name="currency_id" string="Currency" colspan="2"/>
                                            <field name="training_vendor" string="Partner Share" colspan="3"/>
                                            <field name="total_price_all" string="Logistics Cost" colspan="3"/>
                                            <field name="clc_cost" string="Training Cost" colspan="3"/>
                                            <field name="margin1" string="Total Costs" colspan="3"/>
                                            <field name="nilme_share" string="NIL ME Share" colspan="3"/>
                                            <field name="margin" widget="percentage" string="Margin (%)" colspan="3"/>
                                        </tree>
                                    </field>
                                </page>
                            </notebook>
                        </group>
                    </sheet>
                </form>
            '''})

        # Inject CSS dynamically using QWeb to force column widths inside CRM Lead
        self.env['ir.ui.view'].sudo().create({
            'name': 'AutoSpacingCSS',
            'type': 'qweb',
            'arch': '''
                <t t-name="AutoSpacingCSS">
                    <style>
                    .o_list_view th, .o_list_view td {
                        min-width: 180px !important;
                        max-width: auto !important;
                        white-space: nowrap !important;
                        overflow: hidden !important;
                        text-overflow: ellipsis !important;
                    }
                    </style>
                </t>
            '''
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
