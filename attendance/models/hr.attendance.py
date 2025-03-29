from odoo import models, fields, api
from datetime import datetime, timedelta

class Attendance(models.Model):
    _inherit = 'hr.attendance'  # Inherit from hr.attendance model

    # Field to store the late arrival time in minutes
    late_minutes = fields.Integer(string='Late Arrival (Minutes)', compute='_compute_late_minutes')

    @api.depends('check_in')
    def _compute_late_minutes(self):
        for record in self:
            if record.check_in:
                # Set expected arrival time as 9:00 AM on the same day as the check_in time
                expected_time = datetime.combine(record.check_in.date(), datetime.min.time()) + timedelta(hours=9)
                
                # Grace period of 15 minutes
                grace_period = timedelta(minutes=15)
                grace_time = expected_time + grace_period

                # If the check-in is later than the expected time plus grace period
                if record.check_in > grace_time:
                    # Calculate late arrival time in minutes
                    late_duration = record.check_in - grace_time
                    record.late_minutes = int(late_duration.total_seconds() / 60)  # Convert seconds to minutes
                else:
                    record.late_minutes = 0  # No late arrival
            else:
                record.late_minutes = 0  # No check-in time provided
