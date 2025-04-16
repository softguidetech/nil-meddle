from odoo import models, fields, api
from datetime import datetime, timedelta

class Attendance(models.Model):
    _inherit = 'hr.attendance'

    grace_period_minutes = fields.Integer(string='Grace Period (Minutes)', default=15)
    late_minutes = fields.Integer(string='Late Minutes', compute='_compute_late_minutes', store=True)

    @api.depends('check_in', 'grace_period_minutes')
    def _compute_late_minutes(self):
        for record in self:
            if record.check_in:
                # Assuming expected arrival is 9:00 AM
                check_in_date = record.check_in.date()
                expected_time = datetime.combine(check_in_date, datetime.min.time()) + timedelta(hours=9)

                # Apply grace period
                grace_time = expected_time + timedelta(minutes=record.grace_period_minutes)

                # Calculate late minutes if check-in is beyond grace time
                if record.check_in > grace_time:
                    late_duration = (record.check_in - grace_time).total_seconds() / 60
                    record.late_minutes = int(late_duration)
                else:
                    record.late_minutes = 0
            else:
                record.late_minutes = 0
