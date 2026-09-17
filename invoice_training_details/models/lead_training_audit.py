# -*- coding: utf-8 -*-

from odoo import Command, api, fields, models, _
from odoo.exceptions import AccessError


class TrainingCourseAudit(models.Model):
    _inherit = 'training.course.audit'

    lead_id = fields.Many2one(
        'crm.lead',
        string='Lead',
        readonly=True,
        index=True,
        ondelete='set null',
    )

    @api.model
    def _nil_setup_ruba_access(self):
        """Grant audit visibility only to the exact Odoo user base.user_admin."""
        group = self.env.ref(
            'invoice_training_details.group_training_audit_ruba',
            raise_if_not_found=False,
        )
        ruba_user = self.env.ref(
            'base.user_admin',
            raise_if_not_found=False,
        )
        if not group or not ruba_user:
            return True

        members = (
            self.env['res.users']
            .sudo()
            .with_context(active_test=False)
            .search([('groups_id', 'in', group.id)])
        )
        for user in members:
            if user.id != ruba_user.id:
                user.sudo().write({
                    'groups_id': [Command.unlink(group.id)],
                })

        ruba_user.sudo().write({
            'groups_id': [Command.link(group.id)],
        })
        return True


class TrainingCourse(models.Model):
    _inherit = 'training.course'

    def _nil_create_audit(self, values):
        for rec in self:
            payload = dict(values)
            root = rec.source_training_course_id or rec
            lead = root.lead_id or rec.lead_id
            if lead:
                payload['lead_id'] = lead.id
            super(TrainingCourse, rec)._nil_create_audit(payload)
        return True


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    training_audit_count = fields.Integer(
        string='Change Log',
        compute='_compute_training_audit_count',
    )
    training_audit_visible = fields.Boolean(
        compute='_compute_training_audit_visible',
    )

    @api.model
    def _nil_is_ruba_user(self):
        ruba_user = self.env.ref('base.user_admin', raise_if_not_found=False)
        return bool(ruba_user and self.env.user.id == ruba_user.id)

    @api.depends_context('uid')
    def _compute_training_audit_visible(self):
        allowed = self._nil_is_ruba_user()
        for lead in self:
            lead.training_audit_visible = allowed

    def _nil_training_audit_domain(self):
        self.ensure_one()
        source_ids = self.training_course_ids.ids
        return [
            '|',
            ('lead_id', '=', self.id),
            '|',
            '&',
            ('document_model', '=', 'crm.lead'),
            ('document_name', '=', self.display_name),
            ('source_training_course_id', 'in', source_ids or [0]),
        ]

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

        if not self._nil_is_ruba_user():
            raise AccessError(_('You are not allowed to view the Training Change Log.'))

        self.env['training.course.audit'].sudo()._nil_setup_ruba_access()

        action = self.env['ir.actions.actions']._for_xml_id(
            'invoice_training_details.action_training_course_audit'
        )
        action['name'] = _('Change Log - %s') % self.display_name
        action['domain'] = self._nil_training_audit_domain()
        action['context'] = {}
        return action
