# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from datetime import datetime, timedelta
import pytz
class ResConfigSettings(models.TransientModel):

    _inherit = 'res.config.settings'
    hr_attendance_start_time = fields.Char(string="Start Time", readonly=False)
    hr_attendance_end_time = fields.Char(string="End Time", readonly=False)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        hr_attendance_start_time = self.env['ir.config_parameter'].sudo().get_param('hr_attendance_start_time') or False
        hr_attendance_end_time = self.env.ref('bhs_attendance_auto_checkout.ir_cron_data_checkout').nextcall.astimezone(
            pytz.timezone(self.env.user.employee_id.tz or 'UTC')).replace(tzinfo=None).time()
        res.update({
            'hr_attendance_start_time': hr_attendance_start_time,
            'hr_attendance_end_time': hr_attendance_end_time,
        })

        return res

    def set_values(self):
        def utc_dt(dt):
            local = pytz.timezone(self.env.user.tz or 'UTC')
            return local.localize(dt, is_dst=None).astimezone(pytz.utc).replace(tzinfo=None)

        super(ResConfigSettings, self).set_values()
        time_check_out = datetime.strptime(self.hr_attendance_end_time or '', "%H:%M:%S").replace(
            year=datetime.now().year,
            month=datetime.now().month,
            day=datetime.now().day)
        if datetime.strptime(self.hr_attendance_end_time, "%H:%M:%S").time() < datetime.now(pytz.timezone(self.env.user.tz or 'UTC')).time():
            time_check_out = time_check_out + timedelta(days=1)
        else:
            time_check_out = time_check_out
        self.env.ref('bhs_attendance_auto_checkout.ir_cron_data_checkout').write({
            'nextcall': utc_dt(time_check_out),
        })
        self.env['ir.config_parameter'].sudo().set_param("hr_attendance_start_time", self.hr_attendance_start_time)


class BHHrAttendance(models.Model):
    _inherit = 'hr.attendance'

    # Auto Check Out
    @api.model
    def auto_checkout(self):
        try:
            attendances = self.sudo().search([('check_out', '=', None)])
            attendances.write({
                'check_out': fields.Datetime.now(),
            })
        except:
            pass