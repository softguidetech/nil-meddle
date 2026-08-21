from odoo import Command, api, fields, models, _
from odoo.exceptions import UserError, ValidationError


RUBA_COMMISSION_RATE = 1.5
RUBA_NAME = 'ruba khattam'


class SalesCommission(models.Model):
    _name = 'nil.sales.commission'
    _description = 'Sales Commission'
    _order = 'commission_date desc, id desc'
    _rec_name = 'name'

    name = fields.Char(
        string='Commission Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
    )

    invoice_id = fields.Many2one(
        'account.move',
        string='Invoice',
        copy=False,
        index=True,
        ondelete='restrict',
        domain="[('move_type', '=', 'out_invoice')]",
    )

    invoice_state = fields.Selection(
        related='invoice_id.state',
        string='Invoice Status',
        readonly=True,
        store=True,
    )

    lead_id = fields.Many2one(
        'crm.lead',
        string='Lead / Opportunity',
        ondelete='set null',
        index=True,
    )

    salesperson_id = fields.Many2one(
        'res.users',
        string='Commission For',
        index=True,
    )

    customer_id = fields.Many2one(
        'res.partner',
        string='Customer',
        index=True,
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id,
    )

    training_value = fields.Monetary(
        string='Training Value',
        currency_field='currency_id',
        required=True,
        default=0.0,
    )

    commission_rate = fields.Float(
        string='Commission %',
        default=0.0,
        required=True,
    )

    commission_amount = fields.Monetary(
        string='Commission Amount',
        currency_field='currency_id',
        required=True,
        default=0.0,
    )

    commission_date = fields.Date(
        string='Commission Date',
        required=True,
        default=fields.Date.context_today,
        index=True,
    )

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('pending', 'Approved'),
            ('paid', 'Paid'),
            ('excluded', 'Excluded'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        required=True,
        default='draft',
        index=True,
    )

    # Marks the one automatic Ruba 1.5% row generated for each invoice.
    # Manual rows are False and remain fully editable.
    is_auto_ruba = fields.Boolean(
        string='Automatic Ruba Commission',
        default=False,
        copy=False,
        index=True,
    )

    payment_date = fields.Date(
        string='Payment Date',
        readonly=True,
        copy=False,
    )

    payment_journal_id = fields.Many2one(
        'account.journal',
        string='Payment Journal',
        domain="[('company_id', '=', company_id), ('type', 'in', ['bank', 'cash', 'general'])]",
        check_company=True,
    )

    expense_account_id = fields.Many2one(
        'account.account',
        string='Commission Expense Account',
        domain="[('company_id', '=', company_id), ('account_type', 'in', ['expense', 'expense_direct_cost', 'expense_depreciation'])]",
        check_company=True,
    )

    payment_account_id = fields.Many2one(
        'account.account',
        string='Payment / Credit Account',
        domain="[('company_id', '=', company_id), ('deprecated', '=', False)]",
        check_company=True,
    )

    move_id = fields.Many2one(
        'account.move',
        string='Journal Entry',
        readonly=True,
        copy=False,
        ondelete='restrict',
    )

    notes = fields.Text(
        string='Notes'
    )

    # Intentionally NO unique(invoice_id) SQL constraint.
    # One invoice may have:
    # - the automatic Ruba 1.5% row
    # - one or more additional manual commission rows
    _sql_constraints = []

    @api.model
    def _nil_normalize_name(self, name):
        return ' '.join(
            (name or '').split()
        ).casefold()

    @api.model
    def _nil_get_ruba_user(self):
        """
        Return Ruba Khattam's Odoo user.

        In this database Ruba is the main Administrator user.
        We first match by name, then safely fall back to base.user_admin.
        """
        Users = self.env[
            'res.users'
        ].sudo().with_context(
            active_test=False
        )

        candidates = Users.search([
            ('name', 'ilike', 'Ruba Khattam'),
        ])

        for user in candidates:
            if self._nil_normalize_name(
                user.name
            ) == RUBA_NAME:
                return user

        admin = self.env.ref(
            'base.user_admin',
            raise_if_not_found=False,
        )

        if admin:
            return admin

        return Users.browse()

    @api.model
    def _nil_prepare_invoice_commission_migration(self):
        """
        Preserve ALL manual entries.

        Also remove the old one-row-per-invoice constraint so one invoice can
        have Ruba's automatic row plus additional manual commission rows.
        """
        constraint_names = [
            'nil_sales_commission_lead_commission_unique',
            'lead_commission_unique',
            'nil_sales_commission_invoice_commission_unique',
            'invoice_commission_unique',
        ]

        for constraint_name in constraint_names:
            self.env.cr.execute(
                'ALTER TABLE nil_sales_commission '
                'DROP CONSTRAINT IF EXISTS %s'
                % constraint_name
            )

        return True

    @api.model_create_multi
    def create(self, vals_list):
        sequence = self.env['ir.sequence']

        for vals in vals_list:
            if vals.get(
                'name',
                _('New')
            ) == _('New'):
                vals['name'] = (
                    sequence.next_by_code(
                        'sales.commission'
                    )
                    or _('New')
                )

            invoice_id = vals.get('invoice_id')

            if invoice_id:
                invoice = self.env[
                    'account.move'
                ].browse(invoice_id)

                lead = (
                    invoice._nil_get_commission_lead()
                )

                vals.setdefault(
                    'lead_id',
                    lead.id if lead else False,
                )

                vals.setdefault(
                    'customer_id',
                    lead.partner_id.id
                    if lead and lead.partner_id
                    else invoice.partner_id.id
                    if invoice.partner_id
                    else False,
                )

                vals.setdefault(
                    'company_id',
                    invoice.company_id.id,
                )

                vals.setdefault(
                    'currency_id',
                    lead.currency_id.id
                    if lead and lead.currency_id
                    else invoice.currency_id.id,
                )

                vals.setdefault(
                    'commission_date',
                    invoice.invoice_date,
                )

                # Commission basis is the training value on the CRM Lead,
                # not the invoice untaxed amount.
                vals.setdefault(
                    'training_value',
                    lead.total_training_price
                    if lead
                    else 0.0,
                )

            # Automatic Ruba rows always use Ruba + 1.5%.
            if vals.get('is_auto_ruba'):
                ruba_user = self._nil_get_ruba_user()

                vals['salesperson_id'] = (
                    ruba_user.id
                    if ruba_user
                    else vals.get('salesperson_id')
                )

                vals['commission_rate'] = (
                    RUBA_COMMISSION_RATE
                )

            else:
                # Manual entries stay manual.
                vals.setdefault(
                    'commission_rate',
                    0.0,
                )

            training_value = float(
                vals.get(
                    'training_value',
                    0.0,
                )
                or 0.0
            )

            commission_rate = float(
                vals.get(
                    'commission_rate',
                    0.0,
                )
                or 0.0
            )

            vals['commission_amount'] = (
                training_value
                * (commission_rate / 100.0)
            )

        return super().create(vals_list)

    def write(self, vals):
        protected_fields = {
            'invoice_id',
            'lead_id',
            'salesperson_id',
            'customer_id',
            'company_id',
            'currency_id',
            'training_value',
            'commission_rate',
            'commission_amount',
            'commission_date',
            'is_auto_ruba',
        }

        for rec in self:
            if (
                rec.state == 'paid'
                and protected_fields.intersection(
                    vals
                )
            ):
                raise UserError(_(
                    'A paid commission is locked because it already has '
                    'an accounting entry.'
                ))

        result = True

        for rec in self:
            rec_vals = dict(vals)

            auto_sync = self.env.context.get(
                'nil_auto_sync'
            )

            # Automatic Ruba row is always Ruba 1.5%.
            if rec.is_auto_ruba and auto_sync:
                ruba_user = rec._nil_get_ruba_user()

                rec_vals['salesperson_id'] = (
                    ruba_user.id
                    if ruba_user
                    else rec.salesperson_id.id
                )

                rec_vals['commission_rate'] = (
                    RUBA_COMMISSION_RATE
                )

            training_value = float(
                rec_vals.get(
                    'training_value',
                    rec.training_value,
                )
                or 0.0
            )

            commission_rate = float(
                rec_vals.get(
                    'commission_rate',
                    rec.commission_rate,
                )
                or 0.0
            )

            if (
                'training_value' in rec_vals
                or 'commission_rate' in rec_vals
            ):
                rec_vals['commission_amount'] = (
                    training_value
                    * (commission_rate / 100.0)
                )

            result = super(
                SalesCommission,
                rec
            ).write(rec_vals)

        return result

    def unlink(self):
        """
        FULL delete freedom for every NON-PAID entry.

        Manual row:
            delete normally.

        Automatic Ruba row:
            deleting it also marks the invoice as Excluded so the next
            backfill does not recreate it immediately.

        Paid rows stay protected because they already have a posted journal
        entry.
        """
        if any(
            rec.state == 'paid'
            for rec in self
        ):
            raise UserError(_(
                'Paid commissions cannot be deleted while their journal '
                'entry is posted.'
            ))

        auto_rows = self.filtered(
            lambda rec:
                rec.is_auto_ruba
                and rec.invoice_id
        )

        for rec in auto_rows:
            rec.invoice_id.sudo().write({
                'exclude_from_commission': True,
            })

        return super().unlink()

    @api.onchange(
        'invoice_id',
        'commission_rate',
        'training_value',
    )
    def _onchange_commission_fields(self):
        for rec in self:
            if rec.invoice_id:
                invoice = rec.invoice_id
                lead = (
                    invoice._nil_get_commission_lead()
                )

                rec.lead_id = lead

                rec.customer_id = (
                    lead.partner_id
                    if lead and lead.partner_id
                    else invoice.partner_id
                )

                rec.company_id = (
                    invoice.company_id
                )

                rec.currency_id = (
                    lead.currency_id
                    if lead and lead.currency_id
                    else invoice.currency_id
                )

                # Commission is calculated on CRM Lead Total Training Price.
                rec.training_value = (
                    lead.total_training_price
                    if lead
                    else rec.training_value
                )

                rec.commission_date = (
                    invoice.invoice_date
                    or fields.Date.context_today(
                        rec
                    )
                )

            if rec.is_auto_ruba:
                ruba_user = (
                    rec._nil_get_ruba_user()
                )

                rec.salesperson_id = ruba_user
                rec.commission_rate = (
                    RUBA_COMMISSION_RATE
                )

            rec.commission_amount = (
                (rec.training_value or 0.0)
                * (
                    (rec.commission_rate or 0.0)
                    / 100.0
                )
            )

    @api.constrains(
        'commission_rate',
    )
    def _check_commission_rate(self):
        for rec in self:
            if rec.commission_rate < 0:
                raise ValidationError(_(
                    'Commission percentage cannot be negative.'
                ))

    def action_approve(self):
        for rec in self:
            if rec.state not in (
                'draft',
                'cancelled',
            ):
                raise UserError(_(
                    'Only Draft commissions can be approved.'
                ))

            if not rec.salesperson_id:
                raise UserError(_(
                    'Please select who receives this commission.'
                ))

            if rec.commission_rate <= 0:
                raise UserError(_(
                    'Commission percentage must be greater than zero.'
                ))

            if rec.invoice_id:
                rec.invoice_id.sudo().write({
                    'exclude_from_commission':
                        False,
                })

            rec.write({
                'state': 'pending',
            })

        return True

    def action_exclude(self):
        for rec in self:
            if rec.state == 'paid':
                raise UserError(_(
                    'A paid commission cannot be excluded.'
                ))

            if rec.is_auto_ruba and rec.invoice_id:
                rec.invoice_id.sudo().write({
                    'exclude_from_commission':
                        True,
                })

            rec.write({
                'state': 'excluded',
            })

        # Immediately return to the normal ledger.
        # The normal ledger hides Excluded rows, so the invoice disappears
        # from the user's working list as soon as it is excluded.
        return self.env['ir.actions.actions']._for_xml_id(
            'nil_sales_commission.action_sales_commission'
        )

    def action_reset_draft(self):
        """
        Works for BOTH automatic and manually created non-paid entries.

        If the row was excluded, Reset to Draft makes it visible again
        in the normal Commission Ledger.
        """
        for rec in self:
            if rec.state == 'paid':
                raise UserError(_(
                    'A paid commission cannot be reset to Draft.'
                ))

            if rec.is_auto_ruba and rec.invoice_id:
                rec.invoice_id.sudo().write({
                    'exclude_from_commission':
                        False,
                })

            rec.write({
                'state': 'draft',
            })

        return self.env['ir.actions.actions']._for_xml_id(
            'nil_sales_commission.action_sales_commission'
        )

    def action_mark_paid(self):
        for rec in self:
            if rec.state != 'pending':
                raise UserError(_(
                    'Only Approved commissions can be marked as paid.'
                ))

            if not rec.salesperson_id:
                raise UserError(_(
                    'Please select who receives this commission.'
                ))

            if rec.commission_amount <= 0:
                raise UserError(_(
                    'Commission amount must be greater than zero.'
                ))

            if not rec.payment_journal_id:
                raise UserError(_(
                    'Please select a Payment Journal.'
                ))

            if not rec.expense_account_id:
                raise UserError(_(
                    'Please select a Commission Expense Account.'
                ))

            if not rec.payment_account_id:
                raise UserError(_(
                    'Please select a Payment / Credit Account.'
                ))

            payment_date = (
                fields.Date.context_today(rec)
            )

            company = rec.company_id
            company_currency = company.currency_id
            currency = rec.currency_id

            company_amount = currency._convert(
                rec.commission_amount,
                company_currency,
                company,
                payment_date,
            )

            source_name = (
                rec.invoice_id.name
                if rec.invoice_id
                else rec.lead_id.name
                if rec.lead_id
                else rec.name
            )

            line_name = _(
                'Sales Commission - %(salesperson)s - %(source)s',
                salesperson=rec.salesperson_id.name,
                source=source_name,
            )

            partner = rec.salesperson_id.partner_id

            debit_line = {
                'name': line_name,
                'account_id':
                    rec.expense_account_id.id,
                'partner_id':
                    partner.id,
                'debit': company_amount,
                'credit': 0.0,
            }

            credit_line = {
                'name': line_name,
                'account_id':
                    rec.payment_account_id.id,
                'partner_id':
                    partner.id,
                'debit': 0.0,
                'credit': company_amount,
            }

            if currency != company_currency:
                debit_line.update({
                    'currency_id':
                        currency.id,
                    'amount_currency':
                        rec.commission_amount,
                })

                credit_line.update({
                    'currency_id':
                        currency.id,
                    'amount_currency':
                        -rec.commission_amount,
                })

            move = self.env[
                'account.move'
            ].create({
                'move_type': 'entry',
                'date': payment_date,
                'journal_id':
                    rec.payment_journal_id.id,
                'ref': rec.name,
                'company_id': company.id,
                'line_ids': [
                    Command.create(
                        debit_line
                    ),
                    Command.create(
                        credit_line
                    ),
                ],
            })

            move.action_post()

            rec.write({
                'state': 'paid',
                'payment_date':
                    payment_date,
                'move_id':
                    move.id,
            })

        return True

    # Compatibility with buttons/actions from older module versions.
    def action_cancel(self):
        return self.action_exclude()

    def action_reset_pending(self):
        return self.action_reset_draft()

    def action_open_move(self):
        self.ensure_one()

        if not self.move_id:
            raise UserError(_(
                'No journal entry is linked to this commission.'
            ))

        return {
            'type':
                'ir.actions.act_window',
            'name':
                _('Journal Entry'),
            'res_model':
                'account.move',
            'res_id':
                self.move_id.id,
            'view_mode':
                'form',
            'target':
                'current',
        }
