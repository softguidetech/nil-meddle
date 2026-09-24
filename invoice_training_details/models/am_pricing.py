# -*- coding: utf-8 -*-

from markupsafe import Markup, escape

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang


class AmPricing(models.Model):
    _name = 'am.pricing'
    _description = 'Account Manager Pricing'
    _order = 'sent_at desc, id desc'

    lead_id = fields.Many2one(
        'crm.lead',
        string='Opportunity',
        required=True,
        ondelete='cascade',
        index=True,
    )
    account_manager_id = fields.Many2one(
        'res.users',
        string='Account Manager',
        required=True,
        index=True,
    )
    sent_by_id = fields.Many2one(
        'res.users',
        string='Sent By',
        required=True,
        default=lambda self: self.env.user,
        readonly=True,
    )
    sent_at = fields.Datetime(
        string='Sent At',
        required=True,
        default=fields.Datetime.now,
        readonly=True,
    )
    markup_pct = fields.Float(
        string='Markup %',
        digits=(16, 2),
        readonly=True,
        groups='base.group_system',
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        readonly=True,
    )
    line_ids = fields.One2many(
        'am.pricing.line',
        'pricing_id',
        string='Trainings',
        readonly=True,
    )
    subtotal = fields.Monetary(
        string='Subtotal Before VAT',
        currency_field='currency_id',
        compute='_compute_totals',
        store=True,
    )
    vat_amount = fields.Monetary(
        string='VAT Amount',
        currency_field='currency_id',
        compute='_compute_totals',
        store=True,
    )
    total = fields.Monetary(
        string='Total Including VAT',
        currency_field='currency_id',
        compute='_compute_totals',
        store=True,
    )

    @api.depends(
        'line_ids.price_before_vat',
        'line_ids.vat_amount',
        'line_ids.total',
    )
    def _compute_totals(self):
        for rec in self:
            rec.subtotal = sum(rec.line_ids.mapped('price_before_vat'))
            rec.vat_amount = sum(rec.line_ids.mapped('vat_amount'))
            rec.total = sum(rec.line_ids.mapped('total'))

    def _compute_display_name(self):
        for rec in self:
            stamp = fields.Datetime.to_string(rec.sent_at) if rec.sent_at else ''
            rec.display_name = 'AM Pricing - %s' % stamp if stamp else 'AM Pricing'


class AmPricingLine(models.Model):
    _name = 'am.pricing.line'
    _description = 'Account Manager Pricing Line'
    _order = 'id'

    pricing_id = fields.Many2one(
        'am.pricing',
        required=True,
        ondelete='cascade',
        index=True,
    )
    course_id = fields.Many2one(
        'training.course',
        string='Training Source',
        readonly=True,
        ondelete='set null',
        groups='base.group_system',
    )
    training_name = fields.Char(
        string='Training',
        required=True,
        readonly=True,
    )
    description = fields.Text(
        string='Description',
        readonly=True,
    )
    delivery_type = fields.Selection(
        [('Online', 'Online'), ('On site', 'On site')],
        string='Delivery Type',
        readonly=True,
    )
    students = fields.Integer(
        string='Students',
        readonly=True,
    )
    currency_id = fields.Many2one(
        related='pricing_id.currency_id',
        store=True,
        readonly=True,
    )
    price_before_vat = fields.Monetary(
        string='Price Before VAT',
        currency_field='currency_id',
        readonly=True,
    )
    vat_rate = fields.Float(
        string='VAT %',
        digits=(16, 2),
        readonly=True,
    )
    vat_amount = fields.Monetary(
        string='VAT Amount',
        currency_field='currency_id',
        readonly=True,
    )
    total = fields.Monetary(
        string='Total',
        currency_field='currency_id',
        readonly=True,
    )


class AmPricingWizard(models.TransientModel):
    _name = 'am.pricing.wizard'
    _description = 'Send Pricing to Account Manager'

    lead_id = fields.Many2one(
        'crm.lead',
        string='Opportunity',
        required=True,
        readonly=True,
    )
    account_manager_id = fields.Many2one(
        'res.users',
        string='Account Manager',
        required=True,
        domain=[('share', '=', False)],
    )
    markup_pct = fields.Float(
        string='Markup %',
        digits=(16, 2),
        default=0.0,
        required=True,
        help='Selling Price Before VAT = LCP Total Cost x (1 + Markup %).',
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        readonly=True,
    )

    available_course_ids = fields.Many2many(
        'training.course',
        'am_pricing_wizard_available_rel',
        'wizard_id',
        'course_id',
        string='Available Cash Trainings',
        compute='_compute_available_courses',
    )
    selected_course_ids = fields.Many2many(
        'training.course',
        'am_pricing_wizard_selected_rel',
        'wizard_id',
        'course_id',
        string='Cash Trainings',
    )

    preview_html = fields.Html(
        string='Pricing Preview',
        compute='_compute_preview_and_totals',
        sanitize=False,
    )
    subtotal = fields.Monetary(
        string='Subtotal Before VAT',
        currency_field='currency_id',
        compute='_compute_preview_and_totals',
    )
    vat_amount = fields.Monetary(
        string='VAT Amount',
        currency_field='currency_id',
        compute='_compute_preview_and_totals',
    )
    total = fields.Monetary(
        string='Total Including VAT',
        currency_field='currency_id',
        compute='_compute_preview_and_totals',
    )

    @api.depends('lead_id')
    def _compute_available_courses(self):
        for rec in self:
            rec.available_course_ids = rec.lead_id.training_course_ids.filtered(
                lambda course: course.payment_method == 'cash'
            )

    @api.constrains('markup_pct')
    def _check_markup_pct(self):
        for rec in self:
            if rec.markup_pct < 0:
                raise ValidationError(_('Markup % cannot be negative.'))

    @api.model
    def default_get(self, fields_list):
        vals = super().default_get(fields_list)

        if self.env.context.get('active_model') != 'crm.lead':
            return vals

        lead = self.env['crm.lead'].browse(
            self.env.context.get('active_id')
        ).exists()
        if not lead:
            return vals

        cash_courses = lead.training_course_ids.filtered(
            lambda course: course.payment_method == 'cash'
        )
        if not cash_courses:
            raise UserError(_('This opportunity has no Cash trainings to send.'))

        currencies = cash_courses.mapped('lcp_currency_id').filtered(lambda c: c)
        currency = currencies[:1] or self.env.ref('base.USD')

        vals.update({
            'lead_id': lead.id,
            'account_manager_id': lead.user_id.id or self.env.user.id,
            'currency_id': currency.id,
            'markup_pct': 0.0,
            'selected_course_ids': [(6, 0, [])],
        })
        return vals

    def _course_price_values(self, course):
        self.ensure_one()
        cost_amount = course.lcp_total_costs or 0.0
        price_before_vat = cost_amount * (1.0 + ((self.markup_pct or 0.0) / 100.0))
        vat_rate = course.lcp_vat_rate or 0.0
        vat_amount = price_before_vat * vat_rate / 100.0
        total = price_before_vat + vat_amount
        return {
            'cost_amount': cost_amount,
            'price_before_vat': price_before_vat,
            'vat_rate': vat_rate,
            'vat_amount': vat_amount,
            'total': total,
        }

    def _course_description(self, course):
        return (
            course.descriptions
            or course.training_id.description_sale
            or ''
        )

    @api.depends(
        'selected_course_ids',
        'selected_course_ids.lcp_total_costs',
        'selected_course_ids.lcp_vat_rate',
        'selected_course_ids.no_of_student',
        'selected_course_ids.location',
        'selected_course_ids.training_id',
        'selected_course_ids.descriptions',
        'markup_pct',
        'currency_id',
    )
    def _compute_preview_and_totals(self):
        for rec in self:
            subtotal = 0.0
            vat_total = 0.0
            grand_total = 0.0
            rows = []

            selected = rec.selected_course_ids
            currencies = selected.mapped('lcp_currency_id').filtered(lambda c: c)

            if len(currencies) > 1:
                rec.subtotal = 0.0
                rec.vat_amount = 0.0
                rec.total = 0.0
                rec.preview_html = (
                    '<div class="alert alert-warning">'
                    'Selected trainings use different currencies. '
                    'Please select trainings with the same currency.'
                    '</div>'
                )
                continue

            currency = currencies[:1] or rec.currency_id
            for course in selected:
                values = rec._course_price_values(course)
                subtotal += values['price_before_vat']
                vat_total += values['vat_amount']
                grand_total += values['total']

                training_name = (
                    course.training_id.display_name
                    or course.name
                    or _('Training')
                )
                delivery = dict(
                    course._fields['location'].selection
                ).get(course.location, course.location or '')

                rows.append(
                    '<tr>'
                    '<td style="padding:6px;border:1px solid #ddd;">%s</td>'
                    '<td style="padding:6px;border:1px solid #ddd;">%s</td>'
                    '<td style="padding:6px;border:1px solid #ddd;">%s</td>'
                    '<td style="padding:6px;border:1px solid #ddd;text-align:center;">%s</td>'
                    '<td style="padding:6px;border:1px solid #ddd;text-align:right;">%s</td>'
                    '<td style="padding:6px;border:1px solid #ddd;text-align:right;">%s%%</td>'
                    '<td style="padding:6px;border:1px solid #ddd;text-align:right;">%s</td>'
                    '<td style="padding:6px;border:1px solid #ddd;text-align:right;"><strong>%s</strong></td>'
                    '</tr>'
                    % (
                        escape(training_name),
                        escape(rec._course_description(course)),
                        escape(delivery),
                        course.no_of_student or 0,
                        escape(formatLang(
                            rec.env,
                            values['price_before_vat'],
                            currency_obj=currency,
                        )),
                        ('%g' % values['vat_rate']),
                        escape(formatLang(
                            rec.env,
                            values['vat_amount'],
                            currency_obj=currency,
                        )),
                        escape(formatLang(
                            rec.env,
                            values['total'],
                            currency_obj=currency,
                        )),
                    )
                )

            rec.subtotal = subtotal
            rec.vat_amount = vat_total
            rec.total = grand_total

            if not rows:
                rec.preview_html = (
                    '<div class="alert alert-info">'
                    'Select one or more Cash trainings to preview the pricing.'
                    '</div>'
                )
                continue

            rec.preview_html = Markup(
                '<table style="border-collapse:collapse;width:100%%;">'
                '<thead><tr>'
                '<th style="padding:6px;border:1px solid #ddd;text-align:left;">Training</th>'
                '<th style="padding:6px;border:1px solid #ddd;text-align:left;">Description</th>'
                '<th style="padding:6px;border:1px solid #ddd;text-align:left;">Delivery Type</th>'
                '<th style="padding:6px;border:1px solid #ddd;">Students</th>'
                '<th style="padding:6px;border:1px solid #ddd;">Price Before VAT</th>'
                '<th style="padding:6px;border:1px solid #ddd;">VAT</th>'
                '<th style="padding:6px;border:1px solid #ddd;">VAT Amount</th>'
                '<th style="padding:6px;border:1px solid #ddd;">Total</th>'
                '</tr></thead><tbody>%s</tbody></table>'
            ) % Markup(''.join(rows))

    def action_send(self):
        self.ensure_one()

        if self.markup_pct < 0:
            raise UserError(_('Markup % cannot be negative.'))

        selected = self.selected_course_ids
        if not selected:
            raise UserError(_('Select at least one Cash training.'))

        invalid = selected.filtered(lambda c: c.payment_method != 'cash')
        if invalid:
            raise UserError(_('Only Cash trainings can be sent to the Account Manager.'))

        currencies = selected.mapped('lcp_currency_id').filtered(lambda c: c)
        if len(currencies) > 1:
            raise UserError(_('Selected trainings must use the same currency.'))

        if not self.account_manager_id:
            raise UserError(_('Select an Account Manager.'))

        currency = currencies[:1] or self.currency_id

        line_commands = []
        for course in selected:
            values = self._course_price_values(course)
            line_commands.append((0, 0, {
                'course_id': course.id,
                'training_name': (
                    course.training_id.display_name
                    or course.name
                    or _('Training')
                ),
                'description': self._course_description(course),
                'delivery_type': course.location or False,
                'students': course.no_of_student or 0,
                'price_before_vat': values['price_before_vat'],
                'vat_rate': values['vat_rate'],
                'vat_amount': values['vat_amount'],
                'total': values['total'],
            }))

        pricing = self.env['am.pricing'].create({
            'lead_id': self.lead_id.id,
            'account_manager_id': self.account_manager_id.id,
            'sent_by_id': self.env.user.id,
            'sent_at': fields.Datetime.now(),
            'markup_pct': self.markup_pct,
            'currency_id': currency.id,
            'line_ids': line_commands,
        })

        rows = []
        for line in pricing.line_ids:
            delivery = dict(
                line._fields['delivery_type'].selection
            ).get(line.delivery_type, line.delivery_type or '')

            rows.append(
                '<tr>'
                '<td style="padding:6px;border:1px solid #ddd;">%s</td>'
                '<td style="padding:6px;border:1px solid #ddd;">%s</td>'
                '<td style="padding:6px;border:1px solid #ddd;">%s</td>'
                '<td style="padding:6px;border:1px solid #ddd;text-align:center;">%s</td>'
                '<td style="padding:6px;border:1px solid #ddd;text-align:right;">%s</td>'
                '<td style="padding:6px;border:1px solid #ddd;text-align:right;">%s%%</td>'
                '<td style="padding:6px;border:1px solid #ddd;text-align:right;">%s</td>'
                '<td style="padding:6px;border:1px solid #ddd;text-align:right;"><strong>%s</strong></td>'
                '</tr>'
                % (
                    escape(line.training_name or ''),
                    escape(line.description or ''),
                    escape(delivery),
                    line.students,
                    escape(formatLang(
                        self.env,
                        line.price_before_vat,
                        currency_obj=currency,
                    )),
                    ('%g' % (line.vat_rate or 0.0)),
                    escape(formatLang(
                        self.env,
                        line.vat_amount,
                        currency_obj=currency,
                    )),
                    escape(formatLang(
                        self.env,
                        line.total,
                        currency_obj=currency,
                    )),
                )
            )

        body = Markup(
            '<p><strong>Pricing ready for Account Manager</strong></p>'
            '<p>Account Manager: %s</p>'
            '<table style="border-collapse:collapse;width:100%%;">'
            '<thead><tr>'
            '<th style="padding:6px;border:1px solid #ddd;text-align:left;">Training</th>'
            '<th style="padding:6px;border:1px solid #ddd;text-align:left;">Description</th>'
            '<th style="padding:6px;border:1px solid #ddd;text-align:left;">Delivery Type</th>'
            '<th style="padding:6px;border:1px solid #ddd;">Students</th>'
            '<th style="padding:6px;border:1px solid #ddd;">Price Before VAT</th>'
            '<th style="padding:6px;border:1px solid #ddd;">VAT</th>'
            '<th style="padding:6px;border:1px solid #ddd;">VAT Amount</th>'
            '<th style="padding:6px;border:1px solid #ddd;">Total</th>'
            '</tr></thead><tbody>%s</tbody></table>'
            '<p><strong>Subtotal:</strong> %s<br/>'
            '<strong>VAT:</strong> %s<br/>'
            '<strong>Total:</strong> %s</p>'
        ) % (
            escape(self.account_manager_id.name),
            Markup(''.join(rows)),
            escape(formatLang(
                self.env,
                pricing.subtotal,
                currency_obj=currency,
            )),
            escape(formatLang(
                self.env,
                pricing.vat_amount,
                currency_obj=currency,
            )),
            escape(formatLang(
                self.env,
                pricing.total,
                currency_obj=currency,
            )),
        )

        self.lead_id.message_post(
            body=body,
            partner_ids=[self.account_manager_id.partner_id.id],
            subtype_xmlid='mail.mt_note',
        )

        self.lead_id.activity_schedule(
            'mail.mail_activity_data_todo',
            user_id=self.account_manager_id.id,
            summary=_('Pricing ready for customer'),
            note=_(
                'Pricing was prepared for %s selected training(s). '
                'Open the opportunity and review the AM Pricing tab.'
            ) % len(selected),
        )

        return {
            'type': 'ir.actions.act_window',
            'name': _('AM Pricing'),
            'res_model': 'am.pricing',
            'res_id': pricing.id,
            'view_mode': 'form',
            'target': 'current',
        }


class AmPricingWizardLine(models.TransientModel):
    """
    Legacy transient model kept only for upgrade compatibility.

    The live AM Pricing wizard no longer uses this model, so Training Source
    validation can no longer block selecting or sending trainings.
    """
    _name = 'am.pricing.wizard.line'
    _description = 'Legacy AM Pricing Wizard Line'

    wizard_id = fields.Many2one(
        'am.pricing.wizard',
        ondelete='cascade',
    )
    selected = fields.Boolean(string='Select')
    course_id = fields.Many2one(
        'training.course',
        string='Training Source',
        readonly=True,
    )
    training_name = fields.Char(string='Training')
    description = fields.Text(string='Description')
    delivery_type = fields.Selection(
        [('Online', 'Online'), ('On site', 'On site')],
        string='Delivery Type',
    )
    students = fields.Integer(string='Students')
    currency_id = fields.Many2one('res.currency', string='Currency')
    cost_amount = fields.Monetary(
        string='LCP Total Cost',
        currency_field='currency_id',
    )
    vat_rate = fields.Float(string='VAT %', digits=(16, 2))
    price_before_vat = fields.Monetary(
        string='Price Before VAT',
        currency_field='currency_id',
    )
    vat_amount = fields.Monetary(
        string='VAT Amount',
        currency_field='currency_id',
    )
    total = fields.Monetary(
        string='Total',
        currency_field='currency_id',
    )


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    am_pricing_ids = fields.One2many(
        'am.pricing',
        'lead_id',
        string='AM Pricing History',
        readonly=True,
    )

    def action_open_am_pricing_wizard(self):
        self.ensure_one()

        if not self.training_course_ids.filtered(
            lambda course: course.payment_method == 'cash'
        ):
            raise UserError(_('This opportunity has no Cash trainings to send.'))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Send Pricing to Account Manager'),
            'res_model': 'am.pricing.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_model': 'crm.lead',
                'active_id': self.id,
            },
        }
