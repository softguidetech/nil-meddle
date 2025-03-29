from odoo import models, fields

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    checkin_comment_ids = fields.One2many('hr.checkin.comment', 'attendance_id', string="Check-in Comments")
