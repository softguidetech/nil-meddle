# -*- coding: utf-8 -*-

from odoo import fields, models, _
from odoo.exceptions import UserError


class TrainingCourse(models.Model):
    _inherit = 'training.course'

    lcp_auto_price_generated = fields.Boolean(
        string='Auto Training Price', default=False, copy=False
    )

    def _lcp_autofill_cash_price_if_blank(self):
        for line in self:
            if line.payment_method != 'cash':
                continue
            if line.price and not line.lcp_auto_price_generated:
                continue
            line._lcp_apply_country_vat()
            costs = line._lcp_cash_all_costs()
            if costs <= 0:
                continue
            line.price = costs * 1.5 * (1.0 + (line.lcp_vat_rate or 0.0) / 100.0)
            line.lcp_auto_price_generated = True

    def write(self, vals):
        manual_price = (
            'price' in vals
            and not self.env.context.get('skip_lcp_price_flag')
            and 'lcp_auto_price_generated' not in vals
        )
        result = super().write(vals)
        if manual_price:
            self.with_context(skip_lcp_price_flag=True).write({
                'lcp_auto_price_generated': False,
            })
        return result


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    def _lcp_sale_company(self, courses):
        self.ensure_one()
        ordering = self.ordering_partner_id.commercial_partner_id
        saudi_cash = bool(
            ordering
            and ordering.country_id.code == 'SA'
            and any(course.payment_method == 'cash' for course in courses)
        )
        if not saudi_cash:
            return self.company_id or self.env.company

        companies = self.env.user.company_ids.filtered(
            lambda company: (
                company.country_id.code == 'SA'
                or 'saudi' in (company.name or '').lower()
                or 'ksa' in (company.name or '').lower()
            )
        )
        if not companies:
            raise UserError(_(
                'Ordering Party is Saudi, but your user has no Saudi company/branch available. '
                'No UAE quotation was created.'
            ))
        preferred = companies.filtered(
            lambda company: company.country_id.code == 'SA'
        )
        return preferred[:1] or companies[:1]

    def _lcp_instructor_partner(self, instructor):
        employee = instructor.sudo()
        partner = employee.work_contact_id or employee.address_home_id
        if partner:
            return partner.commercial_partner_id
        partner = self.env['res.partner'].search([
            ('name', '=ilike', instructor.name),
            ('active', '=', True),
        ], limit=1)
        if partner:
            return partner.commercial_partner_id
        return self.env['res.partner'].create({
            'name': instructor.name,
            'company_type': 'person',
            'supplier_rank': 1,
        })

    def _lcp_marco_bill(self, course):
        self.ensure_one()
        company = self.company_id or self.env.company
        account = self.env['account.account'].with_company(company).search([
            ('name', 'ilike', 'Incentive'),
            ('company_ids', 'in', [company.id]),
        ], limit=1)
        if not account:
            raise UserError(_(
                'No Incentive account was found in %s.'
            ) % company.display_name)

        instructor = course.instructor_id
        partner = self._lcp_instructor_partner(instructor)
        rate = (
            course.lcp_instructor_md_rate
            if course.lcp_instructor_source == 'nil_me'
            else course.lcp_vendor_instructor_day
        ) or 0.0
        total = (
            course.lcp_total_instructor_md
            if course.lcp_instructor_source == 'nil_me'
            else course.lcp_total_vendor_instructor
        ) or 0.0
        if total <= 0:
            raise UserError(_('Marco Instructor Total is zero. Fill the rate first.'))

        customer = self.training_name or self.ordering_partner_id
        training = course.training_id.display_name or course.name or self.name
        description = 'Training: %s | Dates: %s - %s | Customer: %s' % (
            training,
            course.training_date_start or '',
            course.training_date_end or '',
            customer.display_name if customer else '',
        )
        bill = self.env['account.move'].with_company(company).create({
            'move_type': 'in_invoice',
            'company_id': company.id,
            'partner_id': partner.id,
            'currency_id': (course.lcp_currency_id or self.env.ref('base.USD')).id,
            'invoice_date': fields.Date.context_today(self),
            'invoice_origin': self.name,
            'ref': training,
            'crm_lead_id': self.id,
            'purchase_training_type': 'instructor',
            'instructor_training_course_id': course.id,
            'instructor_id': instructor.id,
            'instructor_from': course.training_date_start,
            'instructor_to': course.training_date_end,
            'instructor_days': course.lcp_days,
            'instructor_daily_rate': rate,
            'instructor_total': total,
            'invoice_line_ids': [(0, 0, {
                'name': description,
                'account_id': account.id,
                'quantity': 1.0,
                'price_unit': total,
            })],
        })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Marco Incentive Vendor Bill'),
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': bill.id,
            'target': 'current',
        }
