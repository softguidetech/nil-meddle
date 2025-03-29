from odoo import models, fields

class HrCheckinComment(models.Model):
    _name = 'hr.checkin.comment'
    _description = 'Check-in Comment'

    attendance_id = fields.Many2one('hr.attendance', string="Attendance", required=True)
    comment = fields.Text(string="Comment", required=True)
