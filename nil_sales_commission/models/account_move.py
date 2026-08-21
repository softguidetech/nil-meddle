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
        Find every Sale Order related to the invoice.

        1) Standard invoice line -> sale line -> sale order link.
        2) Fallback through invoice_origin for older/custom invoices.
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

    def _nil_get_commission_salesperson(self):
        """
        Salesperson priority:
        1) CURRENT salesperson on linked CRM Lead.
        2) Invoice Salesperson.
        3) Sale Order Salesperson.

        IMPORTANT:
        A salesperson is NOT required for the invoice to appear in
        Commission Ledger. This method only provides the best available
        default value.
        """
        self.ensure_one()

        lead = self._nil_get_commission_lead()

        if lead and lead.user_id:
            return lead.user_id

        if self.invoice_user_id:
            return self.invoice_user_id

        sale_orders = self._nil_get_commission_sale_orders()

        if sale_orders and sale_orders[0].user_id:
            return sale_orders[0].user_id

        return self.env['res.users']

    def _nil_sync_sales_commission(self):
        """
        Ensure every customer invoice dated after 31-May-2026 appears in
        Commission Ledger, regardless of:
        - salesperson
        - invoice state
        - invoice amount
        - CRM link

        User-controlled exclusion is respected.

        Invoice-linked fixed fields:
        - Invoice
        - Invoice Date
        - Invoice Value Excl. Tax
        - Currency

        Lead-driven defaults:
        - Lead
        - Salesperson
        - Customer

        Existing Paid rows are never changed.
        Existing Excluded rows remain excluded.
        """
        Commission = self.env['nil.sales.commission'].sudo()

        for invoice in self:
            if invoice.move_type != 'out_invoice':
                continue

            if not invoice.invoice_date:
                continue

            if invoice.invoice_date <= COMMISSION_CUTOFF_DATE:
                continue

            commission = Commission.search([
                ('invoice_id', '=', invoice.id),
            ], limit=1)

            if invoice.exclude_from_commission:
                if commission and commission.state != 'paid':
                    commission.with_context(
                        nil_auto_sync=True
                    ).write({
                        'state': 'excluded',
                    })
                continue

            salesperson = invoice._nil_get_commission_salesperson()
            lead = invoice._nil_get_commission_lead()

            values = {
                'invoice_id': invoice.id,
                'lead_id': lead.id if lead else False,
                'salesperson_id': (
                    salesperson.id
                    if salesperson
                    else False
                ),
                'customer_id': (
                    lead.partner_id.id
                    if lead and lead.partner_id
                    else invoice.partner_id.id
                    if invoice.partner_id
                    else False
                ),
                'company_id': invoice.company_id.id,
                'currency_id': invoice.currency_id.id,
                'training_value': float(
                    invoice.amount_untaxed or 0.0
                ),
                'commission_date': invoice.invoice_date,
            }

            if commission:
                if commission.state == 'paid':
                    continue

                # Do not silently undo a deliberate exclusion.
                if commission.state == 'excluded':
                    continue

                # Only refresh the default rate when the user has never
                # manually overridden it.
                if not commission.manual_rate:
                    values['commission_rate'] = (
                        Commission._nil_get_default_commission_rate(
                            salesperson
                        )
                    )

                commission.with_context(
                    nil_auto_sync=True
                ).write(values)

            else:
                values.update({
                    'commission_rate':
                        Commission._nil_get_default_commission_rate(
                            salesperson
                        ),
                    'state': 'draft',
                    'manual_rate': False,
                })

                Commission.with_context(
                    nil_auto_sync=True
                ).create(values)

        return True

    @api.model
    def _nil_backfill_sales_commissions(self):
        """
        Backfill ALL customer invoices from 01-Jun-2026 onward.

        No salesperson filter.
        No Posted-only filter.
        No positive-amount filter.

        The user decides which rows to approve or exclude.
        """
        Commission = self.env['nil.sales.commission'].sudo()
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
