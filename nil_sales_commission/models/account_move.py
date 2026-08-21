from datetime import date

from odoo import api, fields, models


COMMISSION_CUTOFF_DATE = date(2026, 5, 31)


class AccountMove(models.Model):
    _inherit = 'account.move'

    exclude_from_commission = fields.Boolean(
        string='Exclude from Commission',
        default=False,
        copy=False,
    )

    def _nil_get_commission_sale_orders(self):
        """
        Find Sale Orders related to the invoice.

        Primary:
            Invoice Line -> Sale Line -> Sale Order

        Fallback:
            Invoice Origin -> Sale Order Number
        """
        self.ensure_one()

        SaleOrder = self.env['sale.order'].sudo()
        orders = self.invoice_line_ids.sale_line_ids.order_id

        origin = (self.invoice_origin or '').strip()

        if origin:
            origin_names = [
                value.strip()
                for value in origin.split(',')
                if value.strip()
            ]

            if origin_names:
                orders |= SaleOrder.search([
                    ('name', 'in', origin_names),
                ])

            if not orders:
                orders |= SaleOrder.search([
                    ('name', '=', origin),
                ])

        return orders

    def _nil_get_commission_lead(self):
        """
        Best-effort link from invoice to CRM Lead.
        The Lead link never controls whether an invoice appears.
        """
        self.ensure_one()

        leads = self._nil_get_commission_sale_orders().mapped(
            'opportunity_id'
        )

        if leads:
            return leads[:1]

        existing_commission = self.env[
            'nil.sales.commission'
        ].sudo().search([
            ('invoice_id', '=', self.id),
            ('lead_id', '!=', False),
        ], limit=1)

        if existing_commission:
            return existing_commission.lead_id

        return self.env['crm.lead']

    def _nil_sync_sales_commission(self):
        """
        Every Customer Invoice dated from 01-Jun-2026 onward gets
        one automatic Ruba Khattam commission row at 1.5%.

        IMPORTANT:
        Commission basis = CRM Lead Total Training Price.
        Invoice amount is NOT used for commission calculation.

        There is NO salesperson eligibility filter.

        Additional/manual commission rows are fully preserved and can be
        edited/deleted/reset by the user.

        If an invoice is deliberately excluded, its automatic Ruba row
        stays Excluded and is not recreated as Draft until Reset to Draft.
        """
        Commission = self.env[
            'nil.sales.commission'
        ].sudo()

        ruba_user = Commission._nil_get_ruba_user()

        for invoice in self:
            if invoice.move_type != 'out_invoice':
                continue

            if not invoice.invoice_date:
                continue

            if invoice.invoice_date <= COMMISSION_CUTOFF_DATE:
                continue

            lead = invoice._nil_get_commission_lead()

            # Commission basis is the TOTAL TRAINING VALUE from the CRM Lead,
            # NOT the invoice amount.
            #
            # The invoice is only the trigger/reference that makes the row appear.
            # If no Lead is linked, keep the row visible with Training Value = 0
            # so Ruba can fill/correct it manually if needed.
            training_value = float(
                lead.total_training_price or 0.0
            ) if lead else 0.0

            common_values = {
                'invoice_id': invoice.id,
                'lead_id': lead.id if lead else False,
                'customer_id': (
                    lead.partner_id.id
                    if lead and lead.partner_id
                    else invoice.partner_id.id
                    if invoice.partner_id
                    else False
                ),
                'company_id': invoice.company_id.id,
                'currency_id': (
                    lead.currency_id.id
                    if lead and lead.currency_id
                    else invoice.currency_id.id
                ),
                'training_value': training_value,
                'commission_date': invoice.invoice_date,
            }

            auto_ruba = Commission.search([
                ('invoice_id', '=', invoice.id),
                ('is_auto_ruba', '=', True),
            ], limit=1)

            # Adopt an existing non-paid Ruba row if this invoice came from
            # an older module version and no auto flag existed yet.
            if not auto_ruba and ruba_user:
                old_ruba = Commission.search([
                    ('invoice_id', '=', invoice.id),
                    ('salesperson_id', '=', ruba_user.id),
                    ('state', '!=', 'paid'),
                    ('is_auto_ruba', '=', False),
                ], limit=1)

                if old_ruba:
                    old_ruba.with_context(
                        nil_auto_sync=True
                    ).write({
                        'is_auto_ruba': True,
                    })
                    auto_ruba = old_ruba

            if invoice.exclude_from_commission:
                if auto_ruba and auto_ruba.state != 'paid':
                    auto_ruba.with_context(
                        nil_auto_sync=True
                    ).write({
                        **common_values,
                        'state': 'excluded',
                    })
                elif not auto_ruba:
                    values = dict(common_values)
                    values.update({
                        'salesperson_id': (
                            ruba_user.id
                            if ruba_user
                            else False
                        ),
                        'commission_rate': 1.5,
                        'commission_amount': (
                            training_value * 0.015
                        ),
                        'state': 'excluded',
                        'is_auto_ruba': True,
                    })

                    Commission.with_context(
                        nil_auto_sync=True
                    ).create(values)

                continue

            if auto_ruba:
                if auto_ruba.state != 'paid':
                    auto_ruba.with_context(
                        nil_auto_sync=True
                    ).write({
                        **common_values,
                        'salesperson_id': (
                            ruba_user.id
                            if ruba_user
                            else auto_ruba.salesperson_id.id
                        ),
                        'commission_rate': 1.5,
                    })

            else:
                values = dict(common_values)
                values.update({
                    'salesperson_id': (
                        ruba_user.id
                        if ruba_user
                        else False
                    ),
                    'commission_rate': 1.5,
                    'commission_amount': (
                        training_value * 0.015
                    ),
                    'state': 'draft',
                    'is_auto_ruba': True,
                })

                Commission.with_context(
                    nil_auto_sync=True
                ).create(values)

            # Keep MANUAL invoice-linked rows synchronized with invoice/lead
            # details, but NEVER overwrite their Commission For, rate or state.
            manual_rows = Commission.search([
                ('invoice_id', '=', invoice.id),
                ('is_auto_ruba', '=', False),
                ('state', '!=', 'paid'),
            ])

            if manual_rows:
                manual_rows.with_context(
                    nil_auto_sync=True
                ).write(common_values)

        return True

    @api.model
    def _nil_backfill_sales_commissions(self):
        """
        Re-scan ALL Customer Invoices from 01-Jun-2026 onward.

        No salesperson filter.
        No Posted-only filter.
        No positive-amount filter.

        Result:
        - Every invoice appears through an automatic Ruba 1.5% row.
        - Manual rows are preserved.
        - Excluded invoices remain excluded.
        """
        Commission = self.env[
            'nil.sales.commission'
        ].sudo()

        Commission._nil_prepare_invoice_commission_migration()

        invoices = self.sudo().search([
            ('move_type', '=', 'out_invoice'),
            ('invoice_date', '>', COMMISSION_CUTOFF_DATE),
        ])

        invoices._nil_sync_sales_commission()
        return True

    def action_post(self):
        result = super().action_post()
        self._nil_sync_sales_commission()
        return result

    def write(self, vals):
        result = super().write(vals)

        tracked_fields = {
            'state',
            'invoice_date',
            'invoice_user_id',
            'partner_id',
            'currency_id',
            'invoice_origin',
        }

        if tracked_fields.intersection(vals):
            self.filtered(
                lambda move:
                    move.move_type == 'out_invoice'
            )._nil_sync_sales_commission()

        return result

    def button_draft(self):
        result = super().button_draft()

        self.filtered(
            lambda move:
                move.move_type == 'out_invoice'
        )._nil_sync_sales_commission()

        return result

    def button_cancel(self):
        result = super().button_cancel()

        self.filtered(
            lambda move:
                move.move_type == 'out_invoice'
        )._nil_sync_sales_commission()

        return result
