# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import AccessError


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    training_audit_count = fields.Integer(
        string='Change Log',
        compute='_compute_training_audit_count',
    )
    training_audit_visible = fields.Boolean(
        compute='_compute_training_audit_visible',
    )

    @api.depends_context('uid')
    def _compute_training_audit_visible(self):
        user = self.env.user
        normalized = ' '.join((user.name or '').split()).casefold()
        allowed = (
            normalized == 'ruba khattam'
            or user.has_group('base.group_system')
        )
        for lead in self:
            lead.training_audit_visible = allowed

    def _nil_training_audit_domain(self):
        self.ensure_one()
        source_ids = self.training_course_ids.ids
        domain = [
            '|',
            '&',
            ('document_model', '=', 'crm.lead'),
            ('document_name', '=', self.display_name),
            ('source_training_course_id', 'in', source_ids or [0]),
        ]
        return domain

    def _compute_training_audit_count(self):
        Audit = self.env['training.course.audit'].sudo()
        for lead in self:
            if not lead.training_audit_visible:
                lead.training_audit_count = 0
                continue
            lead.training_audit_count = Audit.search_count(
                lead._nil_training_audit_domain()
            )

    def action_view_training_audit(self):
        self.ensure_one()

        normalized = ' '.join((self.env.user.name or '').split()).casefold()
        if normalized == 'ruba khattam':
            # Ensure Ruba receives the private read group even if the module
            # upgrade did not run the setup hook on a previous deployment.
            self.env['training.course.audit'].sudo()._nil_setup_ruba_access()
        elif not self.env.user.has_group('base.group_system'):
            raise AccessError(_('You are not allowed to view the Training Change Log.'))

        action = self.env['ir.actions.actions']._for_xml_id(
            'invoice_training_details.action_training_course_audit'
        )
        action['name'] = _('Change Log - %s') % self.display_name
        action['domain'] = self._nil_training_audit_domain()
        action['context'] = {
            'search_default_group_by_document_model': 0,
        }
        return action
