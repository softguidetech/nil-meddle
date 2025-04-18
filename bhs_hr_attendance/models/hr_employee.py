# -*- coding: utf-8 -*-

from odoo import _, api, fields, models, exceptions
from datetime import datetime
from odoo.http import request
from odoo.exceptions import AccessError


class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"

    is_attending = fields.Boolean('Attending', compute='_compute_attend_status', search='_search_attending_employee')
    working_hour_from = fields.Float(string='Work from', required=True, index=True, related='resource_calendar_id.hour_from',
                             help="Start and End time of working.\n"
                                  "A specific value of 24:00 is interpreted as 23:59:59.999999.")
    working_hour_to = fields.Float(string='Work to', related='resource_calendar_id.hour_to', required=True)
    break_from = fields.Float(string='Morning End Time', related='resource_calendar_id.break_from', required=True)
    break_to = fields.Float(string='Afternoon Start Time', related='resource_calendar_id.break_to', required=True)
    is_late = fields.Boolean(string='Is late', default=False)

    def _compute_attend_status(self):
        attendances = self.env['hr.attendance'].search([('check_out', '=', False)])
        for rec in self:
            rec.is_attending = attendances.filtered(lambda a: a.employee_id == rec)

    def _search_attending_employee(self, operator, value):
        attendances = self.env['hr.attendance'].search([('check_out', '=', False)])
        alter_operator = 'in' if ((operator == '=' and value is True) or (operator == '!=' and value is False)) else 'not in'
        return [('id', alter_operator, attendances.mapped('employee_id').ids)]

    def _bhs_attendance_action_change(self, geo_information=None):
        """ Check In/Check Out action
            Check In: create a new attendance record
            Check Out: modify check_out field of appropriate attendance record
        """

        self.ensure_one()
        action_date = fields.Datetime.now()

        if self.attendance_state != 'checked_in':
            if geo_information:

                # Check location
                comp_location = self.env['hr.attendance.location'].sudo().browse(geo_information['location_id'])
                if not comp_location:
                    raise ValueError(_('Location attendance not found!'))

                # Check IP
                if comp_location.main_location and self.env.user.restrict_attendance:
                    whitelist_ip = self.env['ir.config_parameter'].sudo().get_param("whitelist_ip", [])
                    if request.httprequest.environ['REMOTE_ADDR'] not in whitelist_ip:
                        raise AccessError(_("You are not allowed to check in outside the company's IP range!"))

                vals = {
                    'employee_id': self.id,
                    'attendance_location': comp_location.id,
                    'check_in': action_date,
                    **{'in_%s' % key: geo_information[key]
                        for key in geo_information if key not in ["location_id"]}
                }

            else:
                vals = {
                    'employee_id': self.id,
                    'check_in': action_date,
                }

            return self.env['hr.attendance'].create(vals)

        attendance = self.env['hr.attendance'].search([('employee_id', '=', self.id), ('check_out', '=', False)], limit=1)
        if attendance:
            if geo_information:
                attendance.write({
                    'check_out': action_date,
                    **{'out_%s' % key: geo_information[key]
                        for key in geo_information if key not in ["location_id"]}
                })
            else:
                attendance.write({'check_out': action_date})

        else:
            raise exceptions.UserError(_(
                'Cannot perform check out on %(empl_name)s, could not find corresponding check in. '
                'Your attendances have probably been modified manually by human resources.',
                empl_name=self.sudo().name))

        return attendance
