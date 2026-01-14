from odoo import models, api, _
from odoo.exceptions import ValidationError
from math import radians, cos, sin, asin, sqrt


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    def _haversine_distance_km(self, lat1, lon1, lat2, lon2):
        lat1 = round(lat1, 7)
        lon1 = round(lon1, 7)
        lat2 = round(lat2, 7)
        lon2 = round(lon2, 7)

        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        r = 6371
        return c * r

    @api.model
    def create(self, vals):
        res = super().create(vals)
        res._validate_check_in_location(vals)
        return res

    def write(self, vals):
        result = super().write(vals)
        self._validate_check_out_location(vals)
        return result

    def _validate_check_in_location(self, vals):
        for record in self:
            if record.employee_id.allow_remote_checkin:
                continue
            
            if 'in_latitude' not in vals or 'in_longitude' not in vals:
                continue

            if vals.get('in_latitude') == 0.0 or vals.get('in_longitude') == 0.0:
                raise ValidationError(
                    _("Location permission is required to perform check-in. Please enable location services in your browser.")
                )

            company = record.employee_id.company_id
            try:
                lat = float(company.attendance_latitude)
                lon = float(company.attendance_longitude)
            except (ValueError, TypeError):
                raise ValidationError(_("Invalid latitude/longitude format in company settings."))


            radius = company.attendance_radius_km
            if not lat or not lon or not radius:
                return

            distance = self._haversine_distance_km(
                lat, lon,
                float(vals['in_latitude']), float(vals['in_longitude'])
            )


            if distance > radius:
                raise ValidationError(
                    _("Check-in location is outside the allowed radius. Distance: %.2f km (allowed: %.2f km)")
                    % (distance, radius)
                )

    def _validate_check_out_location(self, vals):
        for record in self:
            if record.employee_id.allow_remote_checkin:
                continue
            
            if 'out_latitude' not in vals or 'out_longitude' not in vals:
                continue

            if vals.get('out_latitude') == 0.0 or vals.get('out_longitude') == 0.0:
                raise ValidationError(
                    _("Location permission is required to perform check-out. Please enable location services in your browser.")
                )

            company = record.employee_id.company_id
            try:
                lat = float(company.attendance_latitude)
                lon = float(company.attendance_longitude)
            except (ValueError, TypeError):
                raise ValidationError(_("Invalid latitude/longitude format in company settings."))

            radius = company.attendance_radius_km
            if not lat or not lon or not radius:
                return

            distance = self._haversine_distance_km(
                lat, lon,
                float(vals['out_latitude']), float(vals['out_longitude'])
            )

            if distance > radius:
                raise ValidationError(
                    _("Check-out location is outside the allowed radius. Distance: %.2f km (allowed: %.2f km)")
                    % (distance, radius)
                )
