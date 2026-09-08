# -*- coding: utf-8 -*-

import json

from odoo import api, fields, models


LCP_NUMERIC_INPUT_FIELDS = (
    'lcp_vat_rate',
    'lcp_clcs_per_seat',
    'lcp_rate_card_per_seat',
    'lcp_partner_share_pct',
    'lcp_partner_cash_cost',
    'lcp_instructor_md_rate',
    'lcp_vendor_instructor_day',
    'lcp_uber_day_rate',
    'lcp_per_diem_rate',
    'lcp_per_diem_days',
    'lcp_venue_cost',
    'lcp_catering_cost',
)


class TrainingCourse(models.Model):
    _inherit = 'training.course'

    lcp_input_snapshot = fields.Text(
        string='LCP Input Snapshot',
        copy=False,
    )

    def _lcp_current_input_values(self):
        self.ensure_one()
        return {
            field_name: self[field_name] or 0.0
            for field_name in LCP_NUMERIC_INPUT_FIELDS
        }

    def _lcp_snapshot_values(self):
        self.ensure_one()
        if self.lcp_input_snapshot:
            try:
                values = json.loads(self.lcp_input_snapshot)
                if isinstance(values, dict):
                    return {
                        field_name: values.get(field_name, 0.0)
                        for field_name in LCP_NUMERIC_INPUT_FIELDS
                    }
            except (TypeError, ValueError):
                pass

        origin = self._origin
        if origin and origin.id:
            return {
                field_name: origin[field_name] or 0.0
                for field_name in LCP_NUMERIC_INPUT_FIELDS
            }

        return self._lcp_current_input_values()

    @api.onchange(*LCP_NUMERIC_INPUT_FIELDS)
    def _onchange_capture_lcp_inputs(self):
        for line in self:
            line.lcp_input_snapshot = json.dumps(
                line._lcp_current_input_values(),
                sort_keys=True,
            )

    @api.onchange('payment_method')
    def _onchange_preserve_lcp_inputs_on_payment_method(self):
        """Cash/CLC switching must not modify any manual LCP input."""
        for line in self:
            preserved = line._lcp_snapshot_values()
            for field_name, value in preserved.items():
                line[field_name] = value
            line.lcp_input_snapshot = json.dumps(
                preserved,
                sort_keys=True,
            )

    @api.model_create_multi
    def create(self, vals_list):
        prepared = []
        for vals in vals_list:
            vals = dict(vals)
            if not vals.get('lcp_input_snapshot'):
                snapshot = {
                    field_name: vals.get(field_name, 0.0) or 0.0
                    for field_name in LCP_NUMERIC_INPUT_FIELDS
                }
                vals['lcp_input_snapshot'] = json.dumps(
                    snapshot,
                    sort_keys=True,
                )
            prepared.append(vals)
        return super().create(prepared)

    def write(self, vals):
        protected_change = 'payment_method' in vals
        input_change = bool(set(LCP_NUMERIC_INPUT_FIELDS).intersection(vals))

        if not protected_change and not input_change:
            return super().write(vals)

        result = True
        for line in self:
            safe_vals = dict(vals)
            preserved = line._lcp_snapshot_values()

            if protected_change:
                # Payment Method may change. LCP inputs may not be zeroed or
                # replaced by onchange/default values at the same time.
                for field_name in LCP_NUMERIC_INPUT_FIELDS:
                    incoming = safe_vals.get(field_name)
                    if (
                        field_name in safe_vals
                        and incoming not in (False, None, 0, 0.0)
                    ):
                        preserved[field_name] = incoming
                    safe_vals[field_name] = preserved.get(field_name, 0.0)
            else:
                for field_name in LCP_NUMERIC_INPUT_FIELDS:
                    if field_name in safe_vals:
                        preserved[field_name] = safe_vals[field_name] or 0.0

            safe_vals['lcp_input_snapshot'] = json.dumps(
                preserved,
                sort_keys=True,
            )
            result = super(TrainingCourse, line).write(safe_vals) and result

        return result
