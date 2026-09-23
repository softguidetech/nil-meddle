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

        if (
            self.move_type != 'out_invoice'
            or self.state != 'posted'
        ):
            return 0.0

        invoiced = abs(
            float(self.amount_untaxed or 0.0)
        )

        credited = sum(
            abs(float(move.amount_untaxed or 0.0))
            for move in self._nil_commission_credit_notes()
        )

        return max(
            invoiced - credited,
            0.0,
        )

    def _nil_prepare_auto_commission_for_update(
        self,
        commission,
        values,
        target_state,
    ):
        """
        If an already-paid automatic commission changes,
        reverse its posted accounting entry first.
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
            ).write({
                'state': 'draft',
            })

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
        """
        Keep ONE automatic commission row per invoice/type.

        Important:
        - Re-sync never creates duplicates.
        - Existing Approved/Excluded decisions are preserved.
        - Paid rows are protected.
        - Old automatic rows are adopted where safe.
        """
        self.ensure_one()

        Commission = (
            self.env['nil.sales.commission']
            .sudo()
        )

        # ---------------------------------------------------------
        # EXISTING AUTOMATIC ROW
        # ---------------------------------------------------------
        row = Commission.search([
            ('invoice_id', '=', self.id),
            ('auto_key', '=', auto_key),
        ], order='id asc', limit=1)

        # ---------------------------------------------------------
        # LEGACY ROWS
        #
        # Only attempt legacy adoption for Ruba or known fixed-rate
        # salesperson rows.
        #
        # This avoids accidentally converting a manually-created
        # 0% commission into an automatic salesperson commission.
        # ---------------------------------------------------------
        legacy_rows = Commission.browse()

        if auto_key == 'ruba' or rate > 0.0:
            legacy_rows = Commission.search([
                ('invoice_id', '=', self.id),
                ('auto_key', '=', False),
                (
                    'salesperson_id',
                    '=',
                    salesperson.id
                    if salesperson
                    else False
                ),
                ('commission_rate', '=', rate),
                (
                    'is_auto_ruba',
                    '=',
                    auto_key == 'ruba',
                ),
            ], order='id asc')

        # ---------------------------------------------------------
        # ADOPT OLD ROW INSTEAD OF CREATING DUPLICATE
        # ---------------------------------------------------------
        if not row and legacy_rows:
            paid_legacy_rows = (
                legacy_rows.filtered(
                    lambda rec:
                        rec.state == 'paid'
                )
            )

            row = (
                paid_legacy_rows[:1]
                if paid_legacy_rows
                else legacy_rows[:1]
            )

            row.with_context(
                nil_auto_sync=True,
                nil_skip_paid_lock=True,
            ).write({
                'auto_key': auto_key,
                'is_auto_ruba':
                    auto_key == 'ruba',
            })

        # ---------------------------------------------------------
        # REMOVE NON-PAID LEGACY DUPLICATES
        #
        # Never automatically delete a Paid commission.
        # ---------------------------------------------------------
        if row and legacy_rows:
            duplicate_rows = (
                legacy_rows - row
            )

            unpaid_duplicates = (
                duplicate_rows.filtered(
                    lambda rec:
                        rec.state != 'paid'
                )
            )

            if unpaid_duplicates:
                unpaid_duplicates.with_context(
                    nil_sync_cleanup=True
                ).unlink()

        # ---------------------------------------------------------
        # STATUS
        #
        # Management decision must survive re-sync:
        # Draft     = waiting for decision
        # Pending   = approved
        # Excluded  = rejected
        # Paid      = paid
        # ---------------------------------------------------------
        if excluded:
            target_state = 'excluded'

        elif not active:
            target_state = 'cancelled'

        elif row and row.state in (
            'pending',
            'excluded',
            'paid',
        ):
            target_state = row.state

        else:
            target_state = 'draft'

        # ---------------------------------------------------------
        # VALUES
        # ---------------------------------------------------------
        values = dict(common_values)

        values.update({
            'salesperson_id': (
                salesperson.id
                if salesperson
                else False
            ),
            'commission_rate': rate,
            'auto_key': auto_key,
            'is_auto_ruba':
                auto_key == 'ruba',
            'excluded_by_invoice':
                bool(excluded),
        })

        # ---------------------------------------------------------
        # CREATE NEW ROW
        #
        # Only eligible posted invoices create a commission row.
        # New row always starts Draft so management can decide.
        # ---------------------------------------------------------
        if not row:
            if not active or excluded:
                return Commission

            values['state'] = 'draft'

            return Commission.with_context(
                nil_auto_sync=True
            ).create(values)

        # ---------------------------------------------------------
        # PAID COMMISSION
        #
        # Keep Paid only when nothing financially changed.
        # ---------------------------------------------------------
        if (
            row.state == 'paid'
            and active
            and not excluded
        ):
            expected_amount = (
                (values['training_value'] or 0.0)
                * (rate or 0.0)
                / 100.0
            )

            unchanged = (
                abs(
                    (row.training_value or 0.0)
                    - (
                        values['training_value']
                        or 0.0
                    )
                ) < 0.000001

                and abs(
                    (row.commission_rate or 0.0)
                    - (rate or 0.0)
                ) < 0.000001

                and (
                    row.salesperson_id
                    == salesperson
                )

                and abs(
                    (
                        row.commission_amount
                        or 0.0
                    )
                    - expected_amount
                ) < 0.000001
            )

            if unchanged:
                target_state = 'paid'
            else:
                target_state = 'draft'

        # ---------------------------------------------------------
        # PREPARE EXISTING ROW
        # ---------------------------------------------------------
        row = (
            self
            ._nil_prepare_auto_commission_for_update(
                row,
                values,
                target_state,
            )
        )

        write_values = dict(values)

        if row.state != 'paid':
            write_values['state'] = (
                target_state
            )

        row.with_context(
            nil_auto_sync=True,
            nil_skip_paid_lock=True,
        ).write(write_values)

        return row

    def _nil_sync_sales_commission(self):
        """
        Synchronize commission ledger from Customer Invoices.

        RULES:

        1. Every eligible posted Customer Invoice is reviewed.
        2. The Salesperson written ON THE INVOICE is the salesperson
           used for the salesperson commission row.
        3. Every invoice with a Salesperson gets a salesperson row.
        4. The row starts Draft.
        5. Management decides Approve or Exclude.
        6. Re-sync does not duplicate the invoice.
        7. Approved / Excluded decisions are preserved.
        8. Ruba's automatic 1% logic remains unchanged.
        """
        Commission = (
            self.env['nil.sales.commission']
            .sudo()
        )

        for invoice in self:

            # -----------------------------------------------------
            # CUSTOMER INVOICES ONLY
            # -----------------------------------------------------
            if invoice.move_type != 'out_invoice':
                continue

            # -----------------------------------------------------
            # RELATED CRM LEAD
            # -----------------------------------------------------
            lead = (
                invoice
                ._nil_get_commission_lead()
            )

            # -----------------------------------------------------
            # SALESPERSON
            #
            # IMPORTANT:
            # Invoice Salesperson is the PRIMARY source.
            #
            # Only fall back to CRM/Sale Order if the invoice itself
            # has no salesperson.
            # -----------------------------------------------------
            salesperson = (
                invoice.invoice_user_id.sudo()
                if invoice.invoice_user_id
                else
                invoice._nil_get_deal_salesperson()
            )

            # -----------------------------------------------------
            # COMMISSION BASIS
            # -----------------------------------------------------
            basis = (
                invoice
                ._nil_commission_basis()
            )

            # -----------------------------------------------------
            # ELIGIBILITY
            # -----------------------------------------------------
            date_allowed = bool(
                invoice.invoice_date
                and (
                    invoice.invoice_date
                    > COMMISSION_CUTOFF_DATE
                )
            )

            active = bool(
                invoice.state == 'posted'
                and date_allowed
                and basis > 0.0
            )

            excluded = bool(
                invoice.exclude_from_commission
            )

            # -----------------------------------------------------
            # COMMON VALUES
            # -----------------------------------------------------
            common_values = {
                'invoice_id':
                    invoice.id,

                'lead_id':
                    lead.id
                    if lead
                    else False,

                'customer_id': (
                    lead.partner_id.id
                    if (
                        lead
                        and lead.partner_id
                    )
                    else
                    invoice.partner_id.id
                    if invoice.partner_id
                    else False
                ),

                'company_id':
                    invoice.company_id.id,

                'currency_id':
                    invoice.currency_id.id,

                'commission_date':
                    invoice.invoice_date,

                'training_value':
                    basis,
            }

            # =====================================================
            # 1) RUBA COMMISSION
            # =====================================================
            ruba_user = (
                Commission
                ._nil_get_ruba_user()
            )

            invoice._nil_sync_one_auto_commission(
                'ruba',
                ruba_user,
                RUBA_COMMISSION_RATE,
                common_values,
                active,
                excluded,
            )

            # =====================================================
            # 2) SALESPERSON COMMISSION
            #
            # EVERY INVOICE WITH A SALESPERSON MUST APPEAR.
            #
            # No filtering based on Loudy/Baraa names.
            # =====================================================
            salesperson_row = (
                Commission.search([
                    (
                        'invoice_id',
                        '=',
                        invoice.id,
                    ),
                    (
                        'auto_key',
                        '=',
                        'salesperson',
                    ),
                ], order='id asc', limit=1)
            )

            if salesperson:

                fixed_rate = (
                    Commission
                    ._nil_get_fixed_salesperson_rate(
                        salesperson
                    )
                )

                # For known fixed salespeople use configured rate.
                #
                # If this salesperson does not have a fixed rate,
                # preserve an already-existing rate rather than
                # resetting it during every sync.
                salesperson_rate = (
                    fixed_rate
                )

                if (
                    fixed_rate <= 0.0
                    and salesperson_row
                    and (
                        salesperson_row.salesperson_id
                        == salesperson
                    )
                ):
                    salesperson_rate = (
                        salesperson_row
                        .commission_rate
                        or 0.0
                    )

                invoice._nil_sync_one_auto_commission(
                    'salesperson',
                    salesperson,
                    salesperson_rate,
                    common_values,
                    active,
                    excluded,
                )

            # -----------------------------------------------------
            # Invoice no longer has salesperson.
            #
            # Remove only an UNPAID automatic salesperson row.
            # Paid history must remain.
            # -----------------------------------------------------
            elif (
                salesperson_row
                and salesperson_row.state
                != 'paid'
            ):
                salesperson_row.with_context(
                    nil_sync_cleanup=True
                ).unlink()

        return True

    def _nil_commission_impacted_invoices(self):
        """
        Return customer invoices affected
        by invoices / credit notes.
        """
        impacted = (
            self.env['account.move']
        )

        for move in self:

            if move.move_type == 'out_invoice':
                impacted |= move

            elif (
                move.move_type == 'out_refund'
                and move.reversed_entry_id
            ):
                impacted |= (
                    move.reversed_entry_id
                )

        return impacted

    def _nil_sync_commission_impacts(self):
        impacted = (
            self
            ._nil_commission_impacted_invoices()
        )

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
            'invoice_user_id',
            'partner_id',
            'currency_id',
            'invoice_origin',
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
