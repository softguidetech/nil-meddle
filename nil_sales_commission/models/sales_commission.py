from odoo import Command, api, fields, models, _
from odoo.exceptions import UserError, ValidationError


RUBA_COMMISSION_RATE = 1.5
RUBA_NAME = 'ruba khattam'

FIXED_SALESPERSON_RATES = {
    'loudy abdo': 5.0,
    'baraa abo saleh': 2.0,
}


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

    aed_currency_id = fields.Many2one(
        'res.currency',
        string='AED Currency',
        compute='_compute_commission_amount_aed',
        compute_sudo=True,
    )

    commission_amount_aed = fields.Monetary(
        string='Commission Amount AED',
        currency_field='aed_currency_id',
        compute='_compute_commission_amount_aed',
        compute_sudo=True,
    )

    @api.depends('commission_amount')
    def _compute_commission_amount_aed(self):
        aed_currency = self.env.ref(
            'base.AED',
            raise_if_not_found=False,
        )

        for rec in self:
            rec.aed_currency_id = aed_currency
            rec.commission_amount_aed = (
                (rec.commission_amount or 0.0)
                * 3.6725
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

    # New stable key used to prevent automatic duplication.
    # Manual rows keep False/NULL, so multiple manual rows remain allowed.
    auto_key = fields.Selection(
        [
            ('ruba', 'Ruba 1.5%'),
            ('salesperson', 'Fixed Salesperson'),
        ],
        string='Commission Type',
        default=False,
        copy=False,
        index=True,
    )

    # Kept for compatibility with previous module versions.
    is_auto_ruba = fields.Boolean(
        string='Automatic Ruba Commission',
        default=False,
        copy=False,
        index=True,
    )

    excluded_by_invoice = fields.Boolean(
        string='Excluded by Invoice',
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

    cost_detail_ids = fields.Many2many(
        'cost.details',
        string='Cost Details Margin',
        compute='_compute_cost_detail_ids',
        compute_sudo=True,
    )

    profit_learning_partner = fields.Char(
        string='Learning Partner',
        compute='_compute_profit_margin_summary',
        compute_sudo=True,
    )

    profit_total_costs = fields.Float(
        string='Total Costs',
        compute='_compute_profit_margin_summary',
        compute_sudo=True,
    )

    profit_nilme_share = fields.Float(
        string='NIL ME Share $',
        compute='_compute_profit_margin_summary',
        compute_sudo=True,
    )

    profit_margin_pct = fields.Float(
        string='Margin (%)',
        compute='_compute_profit_margin_summary',
        compute_sudo=True,
    )

    @api.depends(
        'lead_id',
        'lead_id.cost_details_ids',
        'lead_id.cost_details_ids.nilme_share',
        'lead_id.cost_details_ids.margin',
        'lead_id.cost_details_ids.margin1',
        'lead_id.cost_details_ids.learning_partner',
    )
    def _compute_cost_detail_ids(self):
        for rec in self:
            rec.cost_detail_ids = (
                rec.lead_id.cost_details_ids.sudo()
                if rec.lead_id
                else self.env['cost.details']
            )

    @api.depends(
        'lead_id',
        'lead_id.total_training_price',
        'lead_id.cost_details_ids',
        'lead_id.cost_details_ids.nilme_share',
        'lead_id.cost_details_ids.margin1',
        'lead_id.cost_details_ids.learning_partner',
    )
    def _compute_profit_margin_summary(self):
        for rec in self:
            cost_lines = (
                rec.lead_id.cost_details_ids.sudo()
                if rec.lead_id
                else self.env['cost.details']
            )

            partner_labels = []
            for line in cost_lines:
                if line.learning_partner:
                    label = dict(
                        line._fields['learning_partner'].selection
                    ).get(
                        line.learning_partner,
                        line.learning_partner,
                    )
                    if label not in partner_labels:
                        partner_labels.append(label)

            total_costs = sum(cost_lines.mapped('margin1'))
            nilme_share = sum(cost_lines.mapped('nilme_share'))
            total_training_price = float(
                rec.lead_id.total_training_price or 0.0
            ) if rec.lead_id else 0.0

            rec.profit_learning_partner = ', '.join(partner_labels)
            rec.profit_total_costs = total_costs
            rec.profit_nilme_share = nilme_share
            # Odoo's percentage widget expects a ratio.
            # Example: 0.4768 is displayed as 47.68%.
            rec.profit_margin_pct = (
                (nilme_share / total_training_price)
                if total_training_price
                else 0.0
            )

    _sql_constraints = [
        (
            'auto_invoice_commission_unique',
            'unique(invoice_id, auto_key)',
            'An automatic commission of this type already exists for this invoice.',
        ),
    ]

    @api.model
    def _nil_normalize_name(self, name):
        return ' '.join(
            (name or '').split()
        ).casefold()

    @api.model
    def _nil_get_ruba_user(self):
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
    def _nil_get_fixed_salesperson_rate(self, salesperson):
        """
        Loudy Abdo = 5%
        Baraa Abo Saleh = 2%

        Everyone else = 0% automatic salesperson commission.
        This NEVER controls invoice visibility.
        """
        if not salesperson:
            return 0.0

        normalized_name = self._nil_normalize_name(
            salesperson.name
        )

        return FIXED_SALESPERSON_RATES.get(
            normalized_name,
            0.0,
        )

    @api.model
    def _nil_prepare_invoice_commission_migration(self):
        """
        Preserve manual entries and clean only automatic Ruba duplicates
        created by older module versions.

        Manual rows are NEVER bulk-deleted here.
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

        flagged_ruba = self.sudo().search([
            ('invoice_id', '!=', False),
            ('is_auto_ruba', '=', True),
        ], order='invoice_id, id')

        grouped = {}

        for rec in flagged_ruba:
            grouped.setdefault(
                rec.invoice_id.id,
                self.browse()
            )
            grouped[rec.invoice_id.id] |= rec

        for rows in grouped.values():
            paid_rows = rows.filtered(
                lambda rec:
                    rec.state == 'paid'
            )

            keeper = (
                paid_rows[:1]
                if paid_rows
                else rows[:1]
            )

            keeper.with_context(
                nil_auto_sync=True,
                nil_skip_paid_lock=True,
            ).write({
                'auto_key': 'ruba',
                'is_auto_ruba': True,
            })

            extras = rows - keeper

            # Keep paid historical duplicates for audit history, but stop
            # treating them as automatic rows.
            paid_extras = extras.filtered(
                lambda rec:
                    rec.state == 'paid'
            )

            if paid_extras:
                paid_extras.with_context(
                    nil_skip_paid_lock=True
                ).write({
                    'auto_key': False,
                    'is_auto_ruba': False,
                })

            non_paid_extras = extras.filtered(
                lambda rec:
                    rec.state != 'paid'
            )

            if non_paid_extras:
                non_paid_extras.with_context(
                    nil_migration_cleanup=True
                ).unlink()

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

                vals.setdefault(
                    'training_value',
                    lead.total_training_price
                    if lead
                    else 0.0,
                )

            auto_key = vals.get('auto_key')

            if auto_key == 'ruba':
                ruba_user = self._nil_get_ruba_user()

                vals['salesperson_id'] = (
                    ruba_user.id
                    if ruba_user
                    else vals.get('salesperson_id')
                )
                vals['commission_rate'] = (
                    RUBA_COMMISSION_RATE
                )
                vals['is_auto_ruba'] = True

            elif auto_key == 'salesperson':
                salesperson = (
                    self.env['res.users'].browse(
                        vals.get('salesperson_id')
                    )
                    if vals.get('salesperson_id')
                    else self.env['res.users']
                )

                vals['commission_rate'] = (
                    self._nil_get_fixed_salesperson_rate(
                        salesperson
                    )
                )
                vals['is_auto_ruba'] = False

            else:
                # Manual row.
                salesperson = (
                    self.env['res.users'].browse(
                        vals.get('salesperson_id')
                    )
                    if vals.get('salesperson_id')
                    else self.env['res.users']
                )

                fixed_rate = (
                    self._nil_get_fixed_salesperson_rate(
                        salesperson
                    )
                )

                if fixed_rate > 0.0:
                    # Loudy/Baraa are fixed even on manual entries.
                    vals['commission_rate'] = fixed_rate
                else:
                    vals.setdefault(
                        'commission_rate',
                        0.0,
                    )

                vals['is_auto_ruba'] = False

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
            'auto_key',
            'is_auto_ruba',
        }

        for rec in self:
            if (
                rec.state == 'paid'
                and protected_fields.intersection(
                    vals
                )
                and not self.env.context.get(
                    'nil_skip_paid_lock'
                )
            ):
                raise UserError(_(
                    'Use Reset to Draft before editing a paid commission.'
                ))

        result = True

        for rec in self:
            rec_vals = dict(vals)

            auto_sync = self.env.context.get(
                'nil_auto_sync'
            )

            resulting_auto_key = rec_vals.get(
                'auto_key',
                rec.auto_key,
            )

            resulting_salesperson = (
                self.env['res.users'].browse(
                    rec_vals.get('salesperson_id')
                )
                if 'salesperson_id' in rec_vals
                and rec_vals.get('salesperson_id')
                else rec.salesperson_id
            )

            if resulting_auto_key == 'ruba':
                ruba_user = rec._nil_get_ruba_user()

                rec_vals['salesperson_id'] = (
                    ruba_user.id
                    if ruba_user
                    else rec.salesperson_id.id
                )
                rec_vals['commission_rate'] = (
                    RUBA_COMMISSION_RATE
                )
                rec_vals['is_auto_ruba'] = True

            elif resulting_auto_key == 'salesperson':
                fixed_rate = (
                    rec._nil_get_fixed_salesperson_rate(
                        resulting_salesperson
                    )
                )

                rec_vals['commission_rate'] = (
                    fixed_rate
                )
                rec_vals['is_auto_ruba'] = False

            else:
                # Manual rows remain editable, except Loudy/Baraa fixed rates.
                fixed_rate = (
                    rec._nil_get_fixed_salesperson_rate(
                        resulting_salesperson
                    )
                )

                if fixed_rate > 0.0:
                    rec_vals['commission_rate'] = (
                        fixed_rate
                    )

                rec_vals['is_auto_ruba'] = False

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
                or 'salesperson_id' in rec_vals
                or 'auto_key' in rec_vals
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

    def _nil_reverse_paid_entry(self):
        """
        Reverse posted accounting entry before a Paid row is reset/deleted.
        """
        for rec in self:
            if rec.state != 'paid' or not rec.move_id:
                continue

            move = rec.move_id.sudo()

            if not move.exists():
                rec.with_context(
                    nil_skip_paid_lock=True
                ).write({
                    'move_id': False,
                    'payment_date': False,
                })
                continue

            if move.state == 'posted':
                reversal_date = (
                    fields.Date.context_today(rec)
                )

                reversal_moves = move._reverse_moves(
                    default_values_list=[{
                        'date': reversal_date,
                        'ref': _(
                            'Reversal of %(commission)s',
                            commission=rec.name,
                        ),
                    }],
                    cancel=False,
                )

                if reversal_moves.filtered(
                    lambda reversal:
                        reversal.state != 'posted'
                ):
                    reversal_moves.action_post()

            rec.with_context(
                nil_skip_paid_lock=True
            ).write({
                'move_id': False,
                'payment_date': False,
            })

        return True

    def unlink(self):
        """
        Manual rows can always be deleted.

        Paid rows are reversed first.

        Automatic Ruba delete = exclude the whole invoice so Ruba's 1.5%
        is not recreated on the next backfill.

        Migration/sync cleanup bypasses that exclusion behavior.
        """
        paid_records = self.filtered(
            lambda rec:
                rec.state == 'paid'
        )

        if paid_records:
            paid_records._nil_reverse_paid_entry()

        if not (
            self.env.context.get('nil_migration_cleanup')
            or self.env.context.get('nil_sync_cleanup')
        ):
            auto_ruba_rows = self.filtered(
                lambda rec:
                    rec.auto_key == 'ruba'
                    and rec.invoice_id
            )

            for rec in auto_ruba_rows:
                rec.invoice_id.sudo().write({
                    'exclude_from_commission': True,
                })

        return super().unlink()

    @api.onchange(
        'invoice_id',
        'salesperson_id',
        'commission_rate',
        'training_value',
        'auto_key',
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

                rec.training_value = (
                    lead.total_training_price
                    if lead
                    else rec.training_value
                )

                rec.commission_date = (
                    invoice.invoice_date
                    or fields.Date.context_today(rec)
                )

            if rec.auto_key == 'ruba':
                ruba_user = (
                    rec._nil_get_ruba_user()
                )
                rec.salesperson_id = ruba_user
                rec.commission_rate = (
                    RUBA_COMMISSION_RATE
                )

            elif rec.auto_key == 'salesperson':
                rec.commission_rate = (
                    rec._nil_get_fixed_salesperson_rate(
                        rec.salesperson_id
                    )
                )

            else:
                fixed_rate = (
                    rec._nil_get_fixed_salesperson_rate(
                        rec.salesperson_id
                    )
                )

                if fixed_rate > 0.0:
                    rec.commission_rate = fixed_rate

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

            # ---------------------------------------------------------
            # AUTO-FILL ACCOUNTING DEFAULTS ON APPROVAL
            # ---------------------------------------------------------
            # Payment Journal:
            #     Incentive
            #
            # Commission Expense Account:
            #     82109 Incentive - Operation
            #
            # Payment / Credit Account:
            #     512022 Bank Emirates Islamic Bank
            #     Checking Account/Current -AED
            # ---------------------------------------------------------

            Journal = self.env['account.journal'].sudo()
            Account = self.env['account.account'].sudo()

            payment_journal = Journal.search([
                ('company_id', '=', rec.company_id.id),
                ('name', '=', 'Incentive'),
            ], limit=1)

            if not payment_journal:
                payment_journal = Journal.search([
                    ('company_id', '=', rec.company_id.id),
                    ('name', 'ilike', 'Incentive'),
                ], limit=1)

            expense_account = Account.search([
                ('company_id', '=', rec.company_id.id),
                ('code', '=', '82109'),
            ], limit=1)

            if not expense_account:
                expense_account = Account.search([
                    ('company_id', '=', rec.company_id.id),
                    ('name', '=', 'Incentive - Operation'),
                ], limit=1)

            payment_account = Account.search([
                ('company_id', '=', rec.company_id.id),
                ('code', '=', '512022'),
            ], limit=1)

            if not payment_account:
                payment_account = Account.search([
                    ('company_id', '=', rec.company_id.id),
                    ('name', 'ilike',
                     'Bank Emirates Islamic Bank Checking Account/Current'),
                ], limit=1)

            if not payment_journal:
                raise UserError(_(
                    'Payment Journal "Incentive" was not found for company %(company)s.',
                    company=rec.company_id.display_name,
                ))

            if not expense_account:
                raise UserError(_(
                    'Commission Expense Account 82109 Incentive - Operation '
                    'was not found for company %(company)s.',
                    company=rec.company_id.display_name,
                ))

            if not payment_account:
                raise UserError(_(
                    'Payment / Credit Account 512022 Bank Emirates Islamic Bank '
                    'Checking Account/Current -AED was not found for company %(company)s.',
                    company=rec.company_id.display_name,
                ))

            if rec.invoice_id and rec.auto_key == 'ruba':
                rec.invoice_id.sudo().write({
                    'exclude_from_commission':
                        False,
                })

            rec.write({
                'state': 'pending',
                'payment_journal_id': payment_journal.id,
                'expense_account_id': expense_account.id,
                'payment_account_id': payment_account.id,
            })

        return True

    def action_exclude(self):
        for rec in self:
            if rec.state == 'paid':
                raise UserError(_(
                    'Reset a paid commission to Draft before excluding it.'
                ))

            if rec.invoice_id and rec.auto_key == 'ruba':
                rec.invoice_id.sudo().write({
                    'exclude_from_commission':
                        True,
                })

            rec.write({
                'state': 'excluded',
            })

        return self.env[
            'ir.actions.actions'
        ]._for_xml_id(
            'nil_sales_commission.action_sales_commission'
        )

    def action_reset_draft(self):
        """
        Reset ANY entry to Draft.

        Paid rows:
        - reverse accounting entry
        - unlock
        - return to Draft
        """
        for rec in self:
            if rec.state == 'paid':
                rec._nil_reverse_paid_entry()

            if (
                rec.invoice_id
                and rec.auto_key == 'ruba'
            ):
                rec.invoice_id.sudo().write({
                    'exclude_from_commission':
                        False,
                })

            rec.with_context(
                nil_skip_paid_lock=True
            ).write({
                'state': 'draft',
                'excluded_by_invoice': False,
                'payment_date': False,
                'move_id': False,
            })

        return self.env[
            'ir.actions.actions'
        ]._for_xml_id(
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

            aed_currency = self.env.ref(
                'base.AED',
                raise_if_not_found=False,
            )

            if not aed_currency:
                raise UserError(_(
                    'AED currency was not found in Odoo.'
                ))

            # Fixed business rate requested:
            # USD commission x 3.6725 = AED commission.
            aed_amount = (
                (rec.commission_amount or 0.0)
                * 3.6725
            )

            # Debit/Credit are always stored in company currency in Odoo.
            # If company currency is AED, use the AED amount directly.
            # Otherwise keep AED as the transaction currency and let Odoo
            # carry the equivalent company-currency balance.
            if company_currency == aed_currency:
                company_amount = aed_amount
            else:
                company_amount = aed_currency._convert(
                    aed_amount,
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

            # Keep the journal-entry label as a plain string.
            # Using keyword "source" with Odoo's translation alias _()
            # conflicts with GettextAlias.__call__(source, ...).
            line_name = 'Sales Commission - %s - %s' % (
                rec.salesperson_id.name,
                source_name,
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

            if aed_currency != company_currency:
                debit_line.update({
                    'currency_id':
                        aed_currency.id,
                    'amount_currency':
                        aed_amount,
                })

                credit_line.update({
                    'currency_id':
                        aed_currency.id,
                    'amount_currency':
                        -aed_amount,
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

            rec.with_context(
                nil_skip_paid_lock=True
            ).write({
                'state': 'paid',
                'payment_date':
                    payment_date,
                'move_id':
                    move.id,
            })

        return True

    # Compatibility with older buttons/actions.
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
