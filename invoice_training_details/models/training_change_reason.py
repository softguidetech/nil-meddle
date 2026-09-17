# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class TrainingCourseAudit(models.Model):
    _inherit = 'training.course.audit'

    change_reason = fields.Text(
        string='Reason',
        readonly=True,
    )


class TrainingCourse(models.Model):
    _inherit = 'training.course'

    nil_change_reason = fields.Char(
        string='Change Reason',
        copy=False,
        help=(
            'Enter why this training detail is being changed. '
            'The reason is stored in the private Training Change Audit log.'
        ),
    )

    def _nil_create_audit(self, values):
        payload = dict(values)
        reason = (
            self.env.context.get('nil_audit_change_reason')
            or payload.get('change_reason')
            or ''
        ).strip()

        if not reason:
            reason = (
                'Created'
                if payload.get('operation') == 'create'
                else 'System / automatic change'
            )

        payload['change_reason'] = reason
        return super()._nil_create_audit(payload)

    @api.model_create_multi
    def create(self, vals_list):
        reason = self.env.context.get('nil_audit_change_reason')
        if not reason:
            reason = (
                'Automatic document snapshot'
                if any(vals.get('source_training_course_id') for vals in vals_list)
                else 'Created'
            )

        return super(
            TrainingCourse,
            self.with_context(nil_audit_change_reason=reason),
        ).create(vals_list)

    def write(self, vals):
        if self.env.context.get('nil_internal_reason_reset'):
            return super().write(vals)

        tracked_names = set(self._nil_snapshot_field_names())
        changed_names = tracked_names.intersection(vals)

        if changed_names and not self.env.context.get('nil_skip_training_audit'):
            reason = (vals.get('nil_change_reason') or '').strip()

            if not reason:
                existing_reasons = {
                    (rec.nil_change_reason or '').strip()
                    for rec in self
                    if (rec.nil_change_reason or '').strip()
                }
                if len(existing_reasons) == 1:
                    reason = next(iter(existing_reasons))

            if not reason:
                raise UserError(_(
                    'Enter Change Reason before changing Training Details.'
                ))

            result = super(
                TrainingCourse,
                self.with_context(nil_audit_change_reason=reason),
            ).write(vals)

            # Consume the reason after one successful change so the next
            # manual change must have its own explanation.
            super(
                TrainingCourse,
                self.with_context(
                    nil_skip_training_audit=True,
                    nil_internal_reason_reset=True,
                ),
            ).write({'nil_change_reason': False})

            return result

        return super().write(vals)

    def unlink(self):
        if self.env.context.get('nil_skip_training_audit'):
            return super().unlink()

        # A deletion has no edit dialog, so the user must enter the reason
        # on the row first. Each deleted row keeps its own reason.
        for rec in self:
            reason = (rec.nil_change_reason or '').strip()
            if not reason:
                raise UserError(_(
                    'Enter Change Reason on the Training row before deleting it.'
                ))

        for rec in self:
            reason = (rec.nil_change_reason or '').strip()
            super(
                TrainingCourse,
                rec.with_context(nil_audit_change_reason=reason),
            ).unlink()

        return True
