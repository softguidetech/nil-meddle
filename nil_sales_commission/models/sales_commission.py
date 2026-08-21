from odoo import Command, api, fields, models, _
from odoo.exceptions import UserError, ValidationError


# Commission rates are driven by the CURRENT salesperson on the CRM Lead.
# Matching is case-insensitive and ignores surrounding spaces.
COMMISSION_RATES = {
    'ruba khattam': 1.5,
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

    lead_id = fields.Many2one(
        'crm.lead',
        string='Lead / Opportunity',
        ondelete='set null',
        index=True,
    )

    salesperson_id = fields.Many2one(
        'res.users',
        string='Salesperson',
        required=True,
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
        string='Invoice Value (Excl. Tax)',
        currency_field='currency_id',
        required=True,
    )

    commission_rate = fields.Float(
        string='Commission %',
        default=0.0,
        required=True,
        readonly=True,
    )

    commission_amount = fields.Monetary(
        string='Commission Amount',
        currency_field='currency_id',
        required=True,
    )

    commission_date = fields.Date(
        string='Commission Date',
        required=True,
        default=fields.Date.context_today,
        index=True,
    )

    state = fields.Selection(
        [
            ('pending', 'Pending'),
            ('paid', 'Paid'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        required=True,
        default='pending',
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

    notes = fields.Text(string='Notes')

    _sql_constraints = [
        (
            'invoice_commission_unique',
            'unique(invoice_id)',
            'A commission record already exists for this invoice.',
        ),
    ]

    @api.model
    def _nil_normalize_salesperson_name(self, name):
        """Normalize case and repeated/extra spaces in salesperson names."""
        return ' '.join((name or '').split()).casefold()

    @api.model
    def _nil_get_commission_rate(self, salesperson):
        """
        Return the commission rate for an approved salesperson.

        Ruba Khattam      = 1.5%
        Loudy Abdo        = 5%
        Baraa Abo Saleh   = 2%

        Anyone else       = 0%
        """
        if not salesperson:
            return 0.0

        salesperson_name = self._nil_normalize_salesperson_name(
            salesperson.name
        )

        normalized_rates = {
            self._nil_normalize_salesperson_name(name): rate
            for name, rate in COMMISSION_RATES.items()
        }

        return normalized_rates.get(salesperson_name, 0.0)

    @api.model
    def _nil_is_allowed_salesperson(self, salesperson):
        return self._nil_get_commission_rate(salesperson) > 0.0

    @api.model
    def _nil_prepare_invoice_commission_migration(self):
        """
        Remove the old one-commission-per-lead database constraint and clear
        unpaid legacy rows that were created by the former CRM-stage logic.
        Paid historical rows are preserved.
        """
        self.env.cr.execute(
            'ALTER TABLE nil_sales_commission '
            'DROP CONSTRAINT IF EXISTS nil_sales_commission_lead_commission_unique'
        )
        self.env.cr.execute(
            'ALTER TABLE nil_sales_commission '
            'DROP CONSTRAINT IF EXISTS lead_commission_unique'
        )

        legacy = self.sudo().search([
            ('invoice_id', '=', False),
            ('state', '!=', 'paid'),
        ])
        if legacy:
            legacy.unlink()

        return True

    @api.model_create_multi
    def create(self, vals_list):
        sequence = self.env['ir.sequence']

        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = sequence.next_by_code('sales.commission') or _('New')

            invoice_id = vals.get('invoice_id')
            if invoice_id:
                invoice = self.env['account.move'].browse(invoice_id)
                lead = invoice._nil_get_commission_lead()

                vals.setdefault('lead_id', lead.id if lead else False)
                vals.setdefault(
                    'customer_id',
                    lead.partner_id.id
                    if lead and lead.partner_id
                    else invoice.partner_id.id
                    if invoice.partner_id
                    else False,
                )
                vals.setdefault('company_id', invoice.company_id.id)
                vals.setdefault('currency_id', invoice.currency_id.id)
                vals.setdefault('commission_date', invoice.invoice_date)
                vals.setdefault('training_value', invoice.amount_untaxed or 0.0)

                if not vals.get('salesperson_id'):
                    salesperson = invoice._nil_get_commission_salesperson()
                    vals['salesperson_id'] = salesperson.id if salesperson else False

            salesperson = (
                self.env['res.users'].browse(vals.get('salesperson_id'))
                if vals.get('salesperson_id')
                else self.env['res.users']
            )

            training_value = float(vals.get('training_value', 0.0) or 0.0)
            commission_rate = self._nil_get_commission_rate(salesperson)

            vals['commission_rate'] = commission_rate
            vals['commission_amount'] = (
                training_value * (commission_rate / 100.0)
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
        }

        for rec in self:
            if rec.state == 'paid' and protected_fields.intersection(vals):
                raise UserError(_(
                    'A paid commission is locked. Reverse/correct its journal entry before changing the commission values.'
                ))

        result = True

        # Recalculate rate and amount per record because the rate depends
        # on the salesperson assigned to that specific commission row.
        for rec in self:
            rec_vals = dict(vals)

            salesperson = (
                self.env['res.users'].browse(rec_vals['salesperson_id'])
                if rec_vals.get('salesperson_id')
                else rec.salesperson_id
            )

            training_value = float(
                rec_vals.get('training_value', rec.training_value) or 0.0
            )

            if (
                'salesperson_id' in rec_vals
                or 'training_value' in rec_vals
            ):
                commission_rate = self._nil_get_commission_rate(salesperson)
                rec_vals['commission_rate'] = commission_rate
                rec_vals['commission_amount'] = (
                    training_value * (commission_rate / 100.0)
                )

            result = super(SalesCommission, rec).write(rec_vals)

        return result

    def unlink(self):
        if any(rec.state == 'paid' for rec in self):
            raise UserError(_('Paid commissions cannot be deleted.'))
        return super().unlink()

    @api.onchange('invoice_id', 'salesperson_id')
    def _onchange_invoice_id(self):
        for rec in self:
            if rec.invoice_id:
                invoice = rec.invoice_id
                lead = invoice._nil_get_commission_lead()
                salesperson = (
                    lead.user_id
                    if lead
                    else invoice._nil_get_commission_salesperson()
                )

                rec.lead_id = lead
                rec.salesperson_id = salesperson
                rec.customer_id = (
                    lead.partner_id
                    if lead and lead.partner_id
                    else invoice.partner_id
                )
                rec.company_id = invoice.company_id
                rec.currency_id = invoice.currency_id
                rec.training_value = invoice.amount_untaxed or 0.0
                rec.commission_date = (
                    invoice.invoice_date
                    or fields.Date.context_today(rec)
                )

            rate = rec._nil_get_commission_rate(rec.salesperson_id)
            rec.commission_rate = rate
            rec.commission_amount = (
                (rec.training_value or 0.0) * (rate / 100.0)
            )

    @api.constrains('training_value', 'commission_amount')
    def _check_non_negative_amounts(self):
        for rec in self:
            if rec.training_value < 0 or rec.commission_amount < 0:
                raise ValidationError(
                    _('Invoice value and commission amount cannot be negative.')
                )

    def action_mark_paid(self):
        for rec in self:
            if rec.state != 'pending':
                raise UserError(_('Only pending commissions can be marked as paid.'))

            if rec.commission_amount <= 0:
                raise UserError(_('Commission amount must be greater than zero.'))

            if not rec.payment_journal_id:
                raise UserError(_('Please select a Payment Journal.'))

            if not rec.expense_account_id:
                raise UserError(_('Please select a Commission Expense Account.'))

            if not rec.payment_account_id:
                raise UserError(_('Please select a Payment / Credit Account.'))

            payment_date = fields.Date.context_today(rec)
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
                'account_id': rec.expense_account_id.id,
                'partner_id': partner.id,
                'debit': company_amount,
                'credit': 0.0,
            }

            credit_line = {
                'name': line_name,
                'account_id': rec.payment_account_id.id,
                'partner_id': partner.id,
                'debit': 0.0,
                'credit': company_amount,
            }

            if currency != company_currency:
                debit_line.update({
                    'currency_id': currency.id,
                    'amount_currency': rec.commission_amount,
                })
                credit_line.update({
                    'currency_id': currency.id,
                    'amount_currency': -rec.commission_amount,
                })

            move = self.env['account.move'].create({
                'move_type': 'entry',
                'date': payment_date,
                'journal_id': rec.payment_journal_id.id,
                'ref': rec.name,
                'company_id': company.id,
                'line_ids': [
                    Command.create(debit_line),
                    Command.create(credit_line),
                ],
            })
            move.action_post()

            rec.write({
                'state': 'paid',
                'payment_date': payment_date,
                'move_id': move.id,
            })

        return True

    def action_cancel(self):
        for rec in self:
            if rec.state == 'paid':
                raise UserError(
                    _('A paid commission cannot be cancelled from here.')
                )
            rec.state = 'cancelled'
        return True

    def action_reset_pending(self):
        for rec in self:
            if rec.state != 'cancelled':
                raise UserError(
                    _('Only cancelled commissions can be reset to pending.')
                )
            rec.state = 'pending'
        return True

    def action_open_move(self):
        self.ensure_one()
        if not self.move_id:
            raise UserError(_('No journal entry is linked to this commission.'))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Journal Entry'),
            'res_model': 'account.move',
            'res_id': self.move_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
