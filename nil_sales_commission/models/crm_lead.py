from odoo import api, fields, models


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    commission_ids = fields.One2many(
        'nil.sales.commission',
        'lead_id',
        string='Sales Commissions',
    )

    commission_count = fields.Integer(
        string='Commission Count',
        compute='_compute_commission_count',
    )

    @api.depends('commission_ids')
    def _compute_commission_count(self):
        for lead in self:
            lead.commission_count = len(lead.commission_ids)

    @api.model_create_multi
    def create(self, vals_list):
        leads = super().create(vals_list)

        # In case a Lead is created directly in Invoiced stage
        leads._sync_sales_commission()

        return leads

    def write(self, vals):
        result = super().write(vals)

        # Recheck commission when any of these values change
        tracked_fields = {
            'stage_id',
            'user_id',
            'partner_id',
            'total_training_price',
        }

        if tracked_fields.intersection(vals):
            self._sync_sales_commission()

        return result

    def _is_invoiced_stage(self):
        """
        Returns True ONLY when the CRM Lead stage
        is named exactly "Invoiced".
        """

        self.ensure_one()

        if not self.stage_id:
            return False

        stage_name = (
            self.stage_id.name or ''
        ).strip().lower()

        return stage_name == 'invoiced'

    def _sync_sales_commission(self):
        """
        COMMISSION RULES

        1. Commission is created ONLY when:
               Lead Stage = Invoiced

        2. Commission =
               Total Training Price × 5%

        3. Salesperson =
               Lead Salesperson (user_id)

        4. New commission status =
               Pending

        5. Only ONE commission record is allowed
           per Lead.

        6. If Lead remains Invoiced and:
               - Salesperson changes
               - Customer changes
               - Training Value changes

           the Pending commission is updated.

        7. Paid commissions are NEVER automatically changed.

        8. Moving the Lead away from Invoiced
           does NOT delete an existing commission.
        """

        Commission = self.env['nil.sales.commission']

        for lead in self:

            # =====================================================
            # ONLY INVOICED LEADS
            # =====================================================

            if not lead._is_invoiced_stage():
                continue

            # =====================================================
            # SALESPERSON IS REQUIRED
            # =====================================================

            if not lead.user_id:
                continue

            # =====================================================
            # CHECK EXISTING COMMISSION
            # =====================================================

            commission = Commission.search([
                ('lead_id', '=', lead.id),
            ], limit=1)

            # =====================================================
            # TRAINING VALUE
            # =====================================================

            training_value = float(
                lead.total_training_price or 0.0
            )

            # =====================================================
            # COMPANY
            # =====================================================

            company = (
                lead.company_id
                or self.env.company
            )

            # =====================================================
            # CURRENCY
            # =====================================================

            currency = (
                lead.currency_id
                if lead.currency_id
                else company.currency_id
            )

            # =====================================================
            # COMMISSION VALUES
            # =====================================================

            values = {
                'salesperson_id': lead.user_id.id,

                'customer_id':
                    lead.partner_id.id
                    if lead.partner_id
                    else False,

                'company_id': company.id,

                'currency_id': currency.id,

                'training_value': training_value,

                'commission_rate': 5.0,

                'commission_amount':
                    training_value * 0.05,

                'commission_date':
                    fields.Date.context_today(lead),
            }

            # =====================================================
            # EXISTING COMMISSION
            # =====================================================

            if commission:

                # Paid commission is historical.
                # Never modify it automatically.
                if commission.state == 'paid':
                    continue

                # If previously cancelled and Lead
                # becomes Invoiced again, reactivate it.
                if commission.state == 'cancelled':
                    values['state'] = 'pending'

                commission.write(values)

            # =====================================================
            # NEW COMMISSION
            # =====================================================

            else:

                values.update({
                    'lead_id': lead.id,
                    'state': 'pending',
                })

                Commission.create(values)

        return True

    def action_view_sales_commission(self):
        """
        Opens the commission related to this Lead.
        """

        self.ensure_one()

        action = self.env[
            'ir.actions.actions'
        ]._for_xml_id(
            'nil_sales_commission.action_sales_commission'
        )

        action['domain'] = [
            ('lead_id', '=', self.id)
        ]

        action['context'] = {
            'default_lead_id': self.id,

            'default_salesperson_id':
                self.user_id.id
                if self.user_id
                else False,

            'default_customer_id':
                self.partner_id.id
                if self.partner_id
                else False,
        }

        commission = self.commission_ids[:1]

        if len(self.commission_ids) == 1:

            action['views'] = [
                (False, 'form')
            ]

            action['res_id'] = commission.id

        return action
