from odoo import models, fields, api

class CostDetails(models.Model):
    _name = 'cost.details'
    _description = 'Cost Details'

    cos_lead_id = fields.Many2one('crm.lead', string="Lead", ondelete='cascade')
    name = fields.Char(string="Cost Name")
    description = fields.Text(string="Description")
    price = fields.Float(string="Price", digits=(16, 2))  # Enforcing decimal precision
    currency_id = fields.Many2one(
        'res.currency', string="Currency", required=True, 
        default=lambda self: self.env.company.currency_id.id
    )

    # Cost Breakdown Fields
    training_vendor = fields.Float(string="Partner Share", digits=(16, 2))
    total_price_all = fields.Float(string="Logistics Cost", compute='_compute_total', store=True, digits=(16, 2))
    margin1 = fields.Float(string="Total Costs", compute='_compute_margin1', store=True, digits=(16, 2))
    clc_cost = fields.Float(string="Training Cost", digits=(16, 2))
    rate_card = fields.Float(string="Partner Rate", digits=(16, 2))
    nilme_share = fields.Float(string="NIL ME Share $", compute='_compute_nilme_share', store=True, digits=(16, 2))

    learning_partner = fields.Selection([
        ('Koeing', 'Koeing'),
        ('Mira', 'Mira'),
        ('NIL LTD', 'NIL LTD'),
        ('NIL SA', 'NIL SA')
    ], string='Learning Partner')

    cost = fields.Float(string="Cost", compute='_compute_total', store=True, digits=(16, 2))
    margin = fields.Float(string="Margin (%)", compute='_compute_margin', store=True, digits=(16, 2))

    ### COMPUTE METHODS ###

    @api.depends('cos_lead_id.ticket_ids.price', 'cos_lead_id.hotel_ids.price', 
                 'cos_lead_id.cost_details_ids.price', 'cos_lead_id.instructor_logistics', 
                 'cos_lead_id.venue', 'cos_lead_id.ctrng', 'cos_lead_id.uber')
    def _compute_total(self):
        """Computes the total cost based on multiple components."""
        for rec in self:
            total = sum([
                sum(ticket.price for ticket in rec.cos_lead_id.ticket_ids or []),
                sum(hotel.price for hotel in rec.cos_lead_id.hotel_ids or []),
                sum(cost.price for cost in rec.cos_lead_id.cost_details_ids or []),
                rec.cos_lead_id.instructor_logistics or 0,
                rec.cos_lead_id.venue or 0,
                rec.cos_lead_id.ctrng or 0,
                rec.cos_lead_id.uber or 0
            ])
            rec.total_price_all = total
            rec.cost = total  # Store cost separately if needed

    @api.depends('training_vendor', 'total_price_all', 'clc_cost')
    def _compute_margin1(self):
        """Computes the total cost (margin1)."""
        for rec in self:
            rec.margin1 = (rec.training_vendor or 0) + (rec.total_price_all or 0) + (rec.clc_cost or 0)

    @api.depends('margin1', 'cos_lead_id.total_training_price')
    def _compute_nilme_share(self):
        """Computes the NIL ME share after cost deductions."""
        for rec in self:
            rec.nilme_share = (rec.cos_lead_id.total_training_price or 0) - (rec.margin1 or 0)

    @api.depends('nilme_share', 'cos_lead_id.total_training_price')
    def _compute_margin(self):
        """Computes margin as a percentage."""
        for rec in self:
            total_price = rec.cos_lead_id.total_training_price or 1  # Avoid division by zero
            rec.margin = ((rec.nilme_share or 0) / total_price) * 100  # Convert to percentage

    ### OPPORTUNITY QUOTATION CONTEXT ###

    def _prepare_opportunity_quotation_context(self):
        """Prepares the context for generating a quotation from the opportunity."""
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

    ### AUTO-SPACING TREE VIEW FIX ###
    
    def init(self):
        """Dynamically modifies the tree view to ensure proper auto-spacing."""
        view_id = self.env.ref('your_module.view_cost_details_tree', raise_if_not_found=False)
        if view_id:
            view_id.write({'arch_base': '''
                <tree editable="bottom" class="auto_spacing">
                    <field name="learning_partner"/>
                    <field name="currency_id"/>
                    <field name="training_vendor"/>
                    <field name="total_price_all"/>
                    <field name="clc_cost"/>
                    <field name="margin1"/>
                    <field name="nilme_share"/>
                    <field name="margin" widget="percentage"/>
                </tree>
            '''})
