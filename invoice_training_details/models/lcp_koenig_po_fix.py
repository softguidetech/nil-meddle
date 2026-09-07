# -*- coding: utf-8 -*-

from odoo import fields, models, _
from odoo.exceptions import UserError


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    def action_new_purchase_order(self):
        self.ensure_one()

        cash_courses = self.training_course_ids.filtered(
            lambda course: course.payment_method == 'cash'
        )
        if not cash_courses:
            return super().action_new_purchase_order()

        code = self._lcp_partner_code(cash_courses)
        if code != 'Koenig':
            return super().action_new_purchase_order()

        # Koenig Cash PO must not calculate, fill, overwrite, or otherwise
        # touch Training Price on the CRM training records. The PO value is
        # exclusively the already-computed Partner Share from the LCP.
        partner = self._lcp_partner('Koenig')
        lines = []

        for course in cash_courses:
            product = course.training_id
            if not product:
                raise UserError(_('Every Cash Training must have a Training Name.'))

            lines.append((0, 0, {
                'product_id': product.id,
                'name': product.display_name or course.name or self.name,
                'product_qty': 1,
                'product_uom': product.uom_po_id.id or product.uom_id.id,
                'price_unit': course.lcp_partner_share or 0.0,
                'date_planned': fields.Datetime.now(),
            }))

        return {
            'type': 'ir.actions.act_window',
            'name': _('New PO'),
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_crm_lead_id': self.id,
                'default_origin': self.name,
                'default_partner_id': partner.id,
                'default_currency_id': self.env.ref('base.USD').id,
                'default_is_training_order': True,
                'default_po_training_type': 'training_vendor',
                'default_payment_method': 'cash',
                'default_training_course_ids': [(6, 0, cash_courses.ids)],
                'default_order_line': lines,
                'default_term_and_cond': self._lcp_koenig_po_terms(cash_courses),
                'default_display_training_table': True,
                'default_display_total': True,
            }
        }
