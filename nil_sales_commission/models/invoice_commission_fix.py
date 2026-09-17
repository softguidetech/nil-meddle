# -*- coding: utf-8 -*-

from odoo import models

from .account_move import COMMISSION_CUTOFF_DATE
from .sales_commission import RUBA_COMMISSION_RATE


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _nil_commission_credit_notes(self):
        """Posted credit notes that reverse this exact customer invoice."""
        self.ensure_one()
        if self.move_type != 'out_invoice':
            return self.env['account.move']

        return self.env['account.move'].sudo().search([
            ('move_type', '=', 'out_refund'),
            ('state', '=', 'posted'),
            ('reversed_entry_id', '=', self.id),
            ('company_id', '=', self.company_id.id),
        ])

    def _nil_commission_basis(self):
        """
        Commission follows the actual posted invoice value excluding tax.

        Standard posted credit notes linked through reversed_entry_id reduce
        the basis immediately. A full credit therefore reduces it to zero.
        """
        self.ensure_one()

        if self.move_type != 'out_invoice' or self.state != 'posted':
            return 0.0

        invoiced = abs(float(self.amount_untaxed or 0.0))
        credited = sum(
            abs(float(move.amount_untaxed or 0.0))
            for move in self._nil_commission_credit_notes()
        )
        return max(invoiced - credited, 0.0)

    def _nil_prepare_auto_commission_for_update(
        self,
        commission,
        values,
        target_state,
    ):
        """
        If an already-paid automatic commission changes, reverse its posted
        accounting entry first. The corrected commission then returns to an
        unpaid/cancelled state instead of leaving stale accounting behind.
        """
        if not commission:
            return commission

        material_fields = (
            'training_value',
            'commission_rate',
            'salesperson_id',
        )
        material_change = any(
            field_name in values
            and (
                commission[field_name].id
                if commission._fields[field_name].type == 'many2one'
                else commission[field_name]
            ) != values[field_name]
            for field_name in material_fields
        )

        if commission.state == 'paid' and (
            material_change
            or target_state != 'paid'
        ):
            commission._nil_reverse_paid_entry()
            commission.with_context(
                nil_skip_paid_lock=True,
                nil_auto_sync=True,
            ).write({'state': 'draft'})

        return commission

    def _nil_sync_one_auto_commission(
        self,
        auto_key,
        salesperson,
        rate,
        common_values,
        active,
        excluded,
    ):
        self.ensure_one()
        Commission = self.env['nil.sales.commission'].sudo()

        row = Commission.search([
            ('invoice_id', '=', self.id),
            ('auto_key', '=', auto_key),
        ], limit=1)

        if excluded:
            target_state = 'excluded'
        elif not active:
            target_state = 'cancelled'
        elif row and row.state == 'paid':
            target_state = 'paid'
        else:
            target_state = 'draft'

        values = dict(common_values)
        values.update({
            'salesperson_id': salesperson.id if salesperson else False,
            'commission_rate': rate,
            'auto_key': auto_key,
            'is_auto_ruba': auto_key == 'ruba',
            'excluded_by_invoice': bool(excluded),
        })

        if not row:
            # Draft/cancelled invoices must not manufacture zero-value rows.
            if not active or excluded:
                return Commission
            values['state'] = 'draft'
            return Commission.with_context(nil_auto_sync=True).create(values)

        # A previously paid row only stays Paid when nothing financial changed.
        if row.state == 'paid' and active and not excluded:
            expected_amount = (
                (values['training_value'] or 0.0)
                * (rate or 0.0)
                / 100.0
            )
            unchanged = (
                abs((row.training_value or 0.0) - (values['training_value'] or 0.0)) < 0.000001
                and abs((row.commission_rate or 0.0) - (rate or 0.0)) < 0.000001
                and row.salesperson_id == salesperson
                and abs((row.commission_amount or 0.0) - expected_amount) < 0.000001
            )
            if unchanged:
                target_state = 'paid'
            else:
                target_state = 'draft'

        row = self._nil_prepare_auto_commission_for_update(
            row,
            values,
            target_state,
        )

        write_values = dict(values)
        if row.state != 'paid':
            write_values['state'] = target_state

        row.with_context(
            nil_auto_sync=True,
            nil_skip_paid_lock=True,
        ).write(write_values)
        return row

    def _nil_sync_sales_commission(self):
        """
        Final invoice-based synchronization.

        Automatic commission is one row per invoice/type, calculated from the
        actual untaxed posted invoice amount after posted standard credit notes.
        Re-running this method updates the same rows and never duplicates them.
        Manual rows are left untouched.
        """
        Commission = self.env['nil.sales.commission'].sudo()

        for invoice in self:
            if invoice.move_type != 'out_invoice':
                continue

            lead = invoice._nil_get_commission_lead()
            salesperson = invoice._nil_get_deal_salesperson()
            basis = invoice._nil_commission_basis()

            date_allowed = bool(
                invoice.invoice_date
                and invoice.invoice_date > COMMISSION_CUTOFF_DATE
            )
            active = bool(
                invoice.state == 'posted'
                and date_allowed
                and basis > 0.0
            )
            excluded = bool(invoice.exclude_from_commission)

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
                'currency_id': invoice.currency_id.id,
                'commission_date': invoice.invoice_date,
                'training_value': basis,
            }

            # Ruba 1% is the global automatic commission row.
            ruba_user = Commission._nil_get_ruba_user()
            invoice._nil_sync_one_auto_commission(
                'ruba',
                ruba_user,
                RUBA_COMMISSION_RATE,
                common_values,
                active,
                excluded,
            )

            # Loudy/Baraa keep their configured fixed salesperson percentages.
            fixed_rate = Commission._nil_get_fixed_salesperson_rate(
                salesperson
            )
            fixed_row = Commission.search([
                ('invoice_id', '=', invoice.id),
                ('auto_key', '=', 'salesperson'),
            ], limit=1)

            if fixed_rate > 0.0:
                invoice._nil_sync_one_auto_commission(
                    'salesperson',
                    salesperson,
                    fixed_rate,
                    common_values,
                    active,
                    excluded,
                )
            elif fixed_row:
                invoice._nil_sync_one_auto_commission(
                    'salesperson',
                    fixed_row.salesperson_id,
                    fixed_row.commission_rate,
                    common_values,
                    False,
                    excluded,
                )

        return True

    def _nil_commission_impacted_invoices(self):
        """Return customer invoices affected by these invoices/credit notes."""
        impacted = self.env['account.move']
        for move in self:
            if move.move_type == 'out_invoice':
                impacted |= move
            elif move.move_type == 'out_refund' and move.reversed_entry_id:
                impacted |= move.reversed_entry_id
        return impacted

    def _nil_sync_commission_impacts(self):
        impacted = self._nil_commission_impacted_invoices()
        if impacted:
            impacted._nil_sync_sales_commission()
        return True

    def action_post(self):
        result = super().action_post()
        self._nil_sync_commission_impacts()
        return result

    def write(self, vals):
        result = super().write(vals)
        watched = {
            'state',
            'invoice_date',
            'exclude_from_commission',
            'reversed_entry_id',
        }
        if watched.intersection(vals):
            self._nil_sync_commission_impacts()
        return result

    def button_draft(self):
        result = super().button_draft()
        self._nil_sync_commission_impacts()
        return result

    def button_cancel(self):
        result = super().button_cancel()
        self._nil_sync_commission_impacts()
        return result
