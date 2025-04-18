# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http, _
from odoo.http import request
from odoo.addons.hr_attendance.controllers.main import HrAttendance
from odoo.tools import float_round
import datetime
import json


class BHSHrAttendance(HrAttendance):

    @staticmethod
    def _bhs_get_geoip_response(mode, latitude=False, longitude=False, id_location=False):
        return {
            'city': request.geoip.city.name or _('Unknown'),
            'country_name': request.geoip.country.name or request.geoip.continent.name or _('Unknown'),
            'latitude': latitude or request.geoip.location.latitude or False,
            'longitude': longitude or request.geoip.location.longitude or False,
            'ip_address': request.geoip.ip,
            'browser': request.httprequest.user_agent.browser,
            'device': request.httprequest.user_agent.platform,
            'location_id': id_location,
            'mode': mode
        }

    @staticmethod
    def _get_employee_attendance_response(employee):
        response = {}
        if employee:
            response = {
                'id': employee.id,
                'employee_name': employee.name,
                'hours_today': float_round(employee.hours_today, precision_digits=2),
                'total_overtime': float_round(employee.total_overtime, precision_digits=2),
                'last_attendance_worked_hours': float_round(employee.last_attendance_worked_hours, precision_digits=2),
                'last_check_in': employee.last_check_in,
                'attendance_state': employee.attendance_state,
                'hours_previously_today': float_round(employee.hours_previously_today, precision_digits=2),
                'kiosk_delay': employee.company_id.attendance_kiosk_delay * 1000,
                'attendance': {'check_in': employee.last_attendance_id.check_in,
                               'check_out': employee.last_attendance_id.check_out},
                'use_pin': employee.company_id.attendance_kiosk_use_pin,
                'display_systray': employee.company_id.attendance_from_systray,
                'display_overtime': employee.company_id.hr_attendance_display_overtime,
                'working_hour_from': employee.working_hour_from,
                'working_hour_to': employee.working_hour_to,
                'break_from': employee.break_from,
                'break_to': employee.break_to,
            }
        return response

    @http.route('/bhs_hr_attendance/systray_check_in_out', type="json", auth="user", csrf_token=False)
    def systray_attendance(self, latitude=False, longitude=False, id_location=False):
        employee = request.env.user.employee_id
        geo_ip_response = self._bhs_get_geoip_response(mode='systray', id_location=id_location,
                                                       latitude=latitude, longitude=longitude)
        employee._bhs_attendance_action_change(geo_ip_response)
        return self._get_employee_info_response(employee)

    @http.route('/bhs_hr_attendance/attendance_user_data', type="json", auth="user")
    def user_attendance_data(self):
        employee = request.env.user.employee_id
        return self._get_employee_attendance_response(employee)
