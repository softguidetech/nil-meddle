from odoo import models, fields, api
from datetime import datetime, timedelta

class Attendance(models.Model):
    _inherit = 'hr.attendance'

    # Field to store the late arrival time in minutes
    late_minutes = fields.Integer(string='Late Arrival (Minutes)', compute='_compute_late_minutes')

    @api.depends('check_in')
    def _compute_late_minutes(self):
        for record in self:
            if record.check_in:
                # Assuming the expected arrival time is 9:00 AM
                expected_time = datetime.combine(record.check_in.date(), datetime.min.time()) + timedelta(hours=9)
                
                # Allowing a grace period of 15 minutes
                grace_period = timedelta(minutes=15)
                grace_time = expected_time + grace_period

                # If the check_in time is later than the expected time plus the grace period
                if record.check_in > grace_time:
                    # Calculate the difference in minutes
                    late_duration = record.check_in - grace_time
                    record.late_minutes = late_duration.total_seconds() / 60  # Convert seconds to minutes
                else:
                    record.late_minutes = 0  # No late arrival
