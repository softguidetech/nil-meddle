from odoo import models, fields, api

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    checkin_comment = fields.Text(string="Check-in Comment")

    @api.model
    def create(self, vals):
        if 'check_in' in vals:
            vals['checkin_comment'] = vals.get('checkin_comment', 'No comment')
        return super(HrAttendance, self).create(vals)
