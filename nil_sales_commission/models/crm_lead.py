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

    def write(self, vals):
        result = super().write(vals)

        # Keep a still-pending commission synchronized with the lead,
        # but ONLY when the lead already has a posted customer invoice.
        tracked_fields = {
            'user_id',
            'partner_id',
            'total_training_price',
        }

        if tracked_fields.intersection(vals):
            self._sync_sales_commission()

        return result

    def _get_posted_customer_invoices(self):
        """Return posted customer invoices linked to this CRM lead via Sales Orders."""
        self.ensure_one()

        sale_orders = self.env['sale.order'].search([
            ('opportunity_id', '=', self.id),
        ])

        return sale_orders.mapped('invoice_ids').filtered(
            lambda move: move.move_type == 'out_invoice' and move.state == 'posted'
        )

    def _sync_sales_commission(self):
        """
        Create/update ONE commission record per CRM lead only after the lead
        has at least one POSTED customer invoice.

        - Before invoicing: no commission record is created.
        - Once invoiced: create Pending commission = 5% of total_training_price.
        - If the posted invoice is reset/cancelled and no posted invoice remains:
          cancel the Pending commission.
        - Paid commissions are historical snapshots and are never auto-changed.
        """
        Commission = self.env['nil.sales.commission']

        for lead in self:
            commission = Commission.search([
                ('lead_id', '=', lead.id),
            ], limit=1)

            posted_invoices = lead._get_posted_customer_invoices()

            # Not invoiced anymore: cancel only an unpaid/pending record.
            if not posted_invoices:
                if commission and commission.state == 'pending':
                    commission.write({'state': 'cancelled'})
                continue

            # No salesperson = nothing to assign yet.
            if not lead.user_id:
                continue

            training_value = float(
                getattr(lead, 'total_training_price', 0.0) or 0.0
            )

            lead_currency = getattr(lead, 'currency_id', False)
            if not lead_currency:
                lead_currency = getattr(lead, 'company_currency', False)

            company = lead.company_id or self.env.company
            currency = lead_currency or company.currency_id

            invoice_dates = [
                move.invoice_date or move.date
                for move in posted_invoices
                if (move.invoice_date or move.date)
            ]
            commission_date = min(invoice_dates) if invoice_dates else fields.Date.context_today(lead)

            values = {
                'salesperson_id': lead.user_id.id,
                'customer_id': lead.partner_id.id if lead.partner_id else False,
                'company_id': company.id,
                'currency_id': currency.id,
                'training_value': training_value,
                'commission_rate': 5.0,
                'commission_amount': training_value * 0.05,
                'commission_date': commission_date,
            }

            if commission:
                if commission.state == 'paid':
                    continue

                if commission.state == 'cancelled':
                    values['state'] = 'pending'

                commission.write(values)
            else:
                values.update({
                    'lead_id': lead.id,
                    'state': 'pending',
                })
                Commission.create(values)

        return True

    def action_view_sales_commission(self):
        self.ensure_one()

        action = self.env['ir.actions.actions']._for_xml_id(
            'nil_sales_commission.action_sales_commission'
        )
        action['domain'] = [('lead_id', '=', self.id)]
        action['context'] = {
            'default_lead_id': self.id,
            'default_salesperson_id': self.user_id.id,
            'default_customer_id': self.partner_id.id if self.partner_id else False,
        }

        commission = self.commission_ids[:1]
        if len(self.commission_ids) == 1:
            action['views'] = [(False, 'form')]
            action['res_id'] = commission.id

        return action
