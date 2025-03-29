from odoo import models, fields

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    checkin_comment = fields.Text(string="Check-in Comment")
