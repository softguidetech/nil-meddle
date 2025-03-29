from odoo import models, fields, api

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    checkin_comment = fields.Text(string="Check-in Comment")

    @api.model
    def create(self, vals):
        if 'check_in' in vals:
            vals['checkin_comment'] = vals.get('checkin_comment', 'No comment')
        return super(HrAttendance, self).create(vals)

    def submit_checkin_comment(self):
        # Logic to handle the comment submission
        # For example, you can add validation or processing here
        if not self.checkin_comment:
            raise ValidationError("Please add a comment before submitting.")
        # Additional logic can be added here
