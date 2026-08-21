from odoo import models, fields, api


class CostDetails(models.Model):
    _name = 'cost.details'
    _description = 'Cost Details'

    cos_lead_id = fields.Many2one(
        'crm.lead',
        string="Lead",
        ondelete='cascade'
    )

    name = fields.Char(string="Cost Name")
    description = fields.Text(string="Description")
    price = fields.Float(string="Price")

    # Partner Share
    # Manual in all cases EXCEPT:
    # CLC + EnterOne = automatic 20% after deducting direct costs
    training_vendor = fields.Float(string="Partner Share")

    # Logistics
    total_price_all = fields.Float(
        string="Logistics Cost",
        compute='_compute_total'
    )

    # Total Costs
    margin1 = fields.Float(
        string="Total Costs",
        compute='_compute_margin1'
    )

    # Kits & Labs
    clc_cost = fields.Float(string="Kits & Labs")

    rate_card = fields.Float(string="Partner Rate")

    # Instructor Cost
    ins_time = fields.Float(string="Instructor")

    # NIL ME Share
    nilme_share = fields.Float(
        string="NIL ME Share $",
        compute='_compute_nilme_share'
    )

    # Learning Partner
    learning_partner = fields.Selection([
        ('Koenig', 'Koenig'),
        ('Mira', 'Mira'),
        ('EnterOne', 'EnterOne'),
        ('NIL LTD', 'NIL LTD'),
        ('NIL SA', 'NIL SA')
    ], string='Learning Partner')

    # Cost
    cost = fields.Float(
        string="Cost",
        compute='_compute_total'
    )

    # Margin %
    margin = fields.Float(
        string="Margin (%)",
        compute='_compute_margin'
    )

    # Sales Commission
    # Always 5% of TOTAL TRAINING PRICE
    sales_commission = fields.Float(
        string="Sales Commission (5%)",
        compute='_compute_sales_commission'
    )

    # Payment Method
    # Taken automatically from the Training lines
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('clc', 'CLC'),
    ], string="Payment Method", compute='_compute_payment_method')


    # =========================================================
    # PAYMENT METHOD
    # =========================================================

    @api.depends(
        'cos_lead_id.training_course_ids.payment_method'
    )
    def _compute_payment_method(self):

        for rec in self:

            if not rec.cos_lead_id:
                rec.payment_method = 'cash'
                continue

            methods = rec.cos_lead_id.training_course_ids.mapped(
                'payment_method'
            )

            # If all training lines are CLC,
            # consider this Cost Detail as CLC.
            #
            # Otherwise keep Partner Share manual.
            if methods and all(
                method == 'clc'
                for method in methods
            ):
                rec.payment_method = 'clc'

            else:
                rec.payment_method = 'cash'


    # =========================================================
    # HELPERS
    # =========================================================

    def _get_direct_costs(self):
        """
        Direct Costs =
            Logistics
            + Kits & Labs
            + Instructor
        """

        self.ensure_one()

        return (
            (self.total_price_all or 0.0)
            + (self.clc_cost or 0.0)
            + (self.ins_time or 0.0)
        )


    def _is_enterone_clc(self):
        """
        EnterOne automatic calculation applies ONLY when:

        Payment Method = CLC
        AND
        Learning Partner = EnterOne
        """

        self.ensure_one()

        return (
            self.payment_method == 'clc'
            and self.learning_partner == 'EnterOne'
        )


    def _get_effective_partner_share(self):
        """
        CLC + EnterOne:

            Partner Share =
            20% × (
                Total Training Price
                - Logistics
                - Kits & Labs
                - Instructor
            )

        All other cases:

            Partner Share is entered manually.
        """

        self.ensure_one()

        # CLC + ENTERONE
        if self._is_enterone_clc():

            total_training_price = (
                self.cos_lead_id.total_training_price or 0.0
            )

            direct_costs = self._get_direct_costs()

            amount_after_costs = (
                total_training_price
                - direct_costs
            )

            if amount_after_costs > 0:

                return (
                    amount_after_costs
                    * 0.20
                )

            return 0.0

        # CASH OR OTHER PARTNERS
        return self.training_vendor or 0.0


    # =========================================================
    # LOGISTICS COST
    # =========================================================

    @api.depends(
        'cos_lead_id.ticket_ids.price',
        'cos_lead_id.hotel_ids.price',
        'cos_lead_id.cost_details_ids.price',
        'cos_lead_id.instructor_logistics',
        'cos_lead_id.venue',
        'cos_lead_id.ctrng',
        'cos_lead_id.uber',
        'ins_time'
    )
    def _compute_total(self):

        for rec in self:

            lead = rec.cos_lead_id

            if not lead:

                rec.total_price_all = 0.0
                rec.cost = 0.0

                continue

            ticket_total = sum(
                lead.ticket_ids.mapped('price')
            )

            hotel_total = sum(
                lead.hotel_ids.mapped('price')
            )

            cost_details_total = sum(
                lead.cost_details_ids.mapped('price')
            )

            instructor_logistics = float(
                lead.instructor_logistics or 0.0
            )

            venue = float(
                lead.venue or 0.0
            )

            catering = float(
                lead.ctrng or 0.0
            )

            uber = float(
                lead.uber or 0.0
            )

            total = (
                ticket_total
                + hotel_total
                + cost_details_total
                + instructor_logistics
                + venue
                + catering
                + uber
            )

            rec.total_price_all = total
            rec.cost = total


    # =========================================================
    # ENTERONE PARTNER SHARE
    # =========================================================

    @api.onchange(
        'learning_partner',
        'payment_method',
        'total_price_all',
        'clc_cost',
        'ins_time',
        'cos_lead_id.total_training_price'
    )
    def _onchange_enterone_partner_share(self):

        for rec in self:

            # Automatic ONLY for CLC + EnterOne
            if (
                rec.payment_method == 'clc'
                and rec.learning_partner == 'EnterOne'
            ):

                total_training_price = (
                    rec.cos_lead_id.total_training_price
                    or 0.0
                )

                direct_costs = (
                    (rec.total_price_all or 0.0)
                    + (rec.clc_cost or 0.0)
                    + (rec.ins_time or 0.0)
                )

                amount_after_costs = (
                    total_training_price
                    - direct_costs
                )

                if amount_after_costs > 0:

                    rec.training_vendor = (
                        amount_after_costs
                        * 0.20
                    )

                else:

                    rec.training_vendor = 0.0


    # =========================================================
    # TOTAL COSTS
    # =========================================================

    @api.depends(
        'training_vendor',
        'total_price_all',
        'clc_cost',
        'ins_time',
        'learning_partner',
        'payment_method',
        'cos_lead_id.total_training_price'
    )
    def _compute_margin1(self):

        for record in self:

            direct_costs = (
                (record.total_price_all or 0.0)
                + (record.clc_cost or 0.0)
                + (record.ins_time or 0.0)
            )

            partner_share = (
                record._get_effective_partner_share()
            )

            record.margin1 = (
                direct_costs
                + partner_share
            )


    # =========================================================
    # NIL ME SHARE
    # =========================================================

    @api.depends(
        'margin1',
        'training_vendor',
        'total_price_all',
        'clc_cost',
        'ins_time',
        'learning_partner',
        'payment_method',
        'cos_lead_id.total_training_price'
    )
    def _compute_nilme_share(self):

        for record in self:

            total_training_price = (
                record.cos_lead_id.total_training_price
                or 0.0
            )

            # -------------------------------------------------
            # CLC + ENTERONE
            # -------------------------------------------------

            if (
                record.payment_method == 'clc'
                and record.learning_partner == 'EnterOne'
            ):

                direct_costs = (
                    (record.total_price_all or 0.0)
                    + (record.clc_cost or 0.0)
                    + (record.ins_time or 0.0)
                )

                amount_after_costs = (
                    total_training_price
                    - direct_costs
                )

                if amount_after_costs > 0:

                    # EnterOne = 20%
                    # NIL ME = 80%
                    record.nilme_share = (
                        amount_after_costs
                        * 0.80
                    )

                else:

                    # Show actual loss
                    record.nilme_share = (
                        amount_after_costs
                    )

            # -------------------------------------------------
            # CASH OR OTHER PARTNERS
            # -------------------------------------------------

            else:

                record.nilme_share = (
                    total_training_price
                    - (record.margin1 or 0.0)
                )


    # =========================================================
    # MARGIN %
    # =========================================================

    @api.depends(
        'nilme_share',
        'cos_lead_id.total_training_price'
    )
    def _compute_margin(self):

        for record in self:

            total_training_price = (
                record.cos_lead_id.total_training_price
                or 0.0
            )

            if total_training_price:

                record.margin = (
                    (record.nilme_share or 0.0)
                    / total_training_price
                )

            else:

                record.margin = 0.0


    # =========================================================
    # SALES COMMISSION
    # =========================================================

    @api.depends(
        'cos_lead_id.total_training_price'
    )
    def _compute_sales_commission(self):
        """
        Sales Commission =
        5% of the FULL Training Value

        It does NOT depend on:
            - Partner Share
            - Logistics
            - Kits & Labs
            - Instructor
            - NIL ME Share
            - Profit Margin
        """

        for record in self:

            total_training_price = (
                record.cos_lead_id.total_training_price
                or 0.0
            )

            record.sales_commission = (
                total_training_price
                * 0.05
            )


    # =========================================================
    # QUOTATION CONTEXT
    # =========================================================

    def _prepare_opportunity_quotation_context(self):

        return {

            'default_cos_lead_id':
                self.cos_lead_id.id,

            'default_name':
                self.name,

            'default_description':
                self.description,

            'default_price':
                self.price,

            'default_training_vendor':
                self.training_vendor,

            'default_total_price_all':
                self.total_price_all,

            'default_margin1':
                self.margin1,

            'default_clc_cost':
                self.clc_cost,

            'default_rate_card':
                self.rate_card,

            'default_ins_time':
                self.ins_time,

            'default_nilme_share':
                self.nilme_share,

            'default_learning_partner':
                self.learning_partner,

            'default_cost':
                self.cost,

            'default_margin':
                self.margin,

            'default_sales_commission':
                self.sales_commission,
        }
