# -*- coding: utf-8 -*-

from odoo import models, fields, tools, api, _
from datetime import datetime, timedelta
import pytz
from odoo.http import request
from odoo.exceptions import AccessError
import operator


time_format = "%H:%M:%S"

def utc_dt(dt, tz=None):
    local = pytz.timezone(tz or 'UTC')
    return local.localize(dt, is_dst=None).astimezone(pytz.utc)


class BHHrLeave(models.Model):
    _inherit = 'hr.leave'

    def action_validate(self):
        res = super(BHHrLeave, self).action_validate()

        for leave in self:
            tz = leave.employee_id.tz
            attendance = self.env['hr.attendance'].sudo().search([
                ('employee_id', '=', leave.employee_id.id),
                ('check_in', '<=', utc_dt(leave.date_to.replace(minute=59, hour=23, second=0), tz)),
                ('check_in', '>=', utc_dt(leave.date_from.replace(minute=00, hour=0, second=0), tz)),
            ])
            # print(attendance)
            if attendance:
                attendance.write({'attendance_time_off': leave.id})

        return res


class BHHrAttendance(models.Model):
    _inherit = 'hr.attendance'

    attendance_location = fields.Many2one(
        'hr.attendance.location', 'Check in location',
        default=lambda self: self.env.ref('bhs_hr_attendance.attendance_location_company', raise_if_not_found=False)
    )
    minutes_late = fields.Integer(string="Minutes Late ", compute='_compute_minutes_late',
                                  search='_search_late_employee', readonly=True, store=True)
    # số phút tính là muộn sau khi đã trừ duyệt vắng mặt (=giờ check in - timeoff.dateto)
    late_minutes_approved = fields.Integer(compute='_compute_late_minutes_approved', store=True)
    time_check_in = fields.Char(string="Time Check In", compute='_compute_check_in', store=True)
    attendance_time_off = fields.Many2one('hr.leave', store=True)

    in_device = fields.Char(string="Device")
    out_device = fields.Char(string="Device")

    @api.model
    def create(self, values):
        res = super(BHHrAttendance, self).create(values)
        leave_emp = self.env['hr.leave'].sudo().search([('employee_id', '=', res.employee_id.id),
                                                        ('request_date_from', '=', res.check_in.date()),
                                                        ('state', '=', 'validate')], limit=1)
        if leave_emp:
            res.attendance_time_off = leave_emp.id
        return res

    @api.depends('check_in', 'attendance_time_off.state')
    def _compute_late_minutes_approved(self):

        for attendance in self:
            attendance.late_minutes_approved = 0

            working_days = []
            for att in attendance.employee_id.resource_calendar_id.attendance_ids:
                if att.dayofweek not in working_days:
                    working_days.append(att.dayofweek)

            if attendance.attendance_time_off and attendance.attendance_time_off.state == 'validate':
                tz = attendance.employee_id.tz

                # Giờ vào làm buổi sáng (utc, str)
                attendance_start_time = str(timedelta(hours=attendance.employee_id.working_hour_from))
                attendance_start_time = datetime.strptime(attendance_start_time, time_format).replace(
                    year=datetime.today().year)
                utc_hour_start = utc_dt(attendance_start_time, tz).strftime(time_format)

                # Giờ bắt đầu nghỉ trưa (utc, str)
                attendance_break_time = str(timedelta(hours=attendance.employee_id.break_from))
                attendance_break_time = datetime.strptime(attendance_break_time, time_format).replace(
                    year=datetime.today().year)
                utc_attendance_break = utc_dt(attendance_break_time, tz).strftime(time_format)

                # Giờ vào làm buổi chiều (utc, str)
                afternoon_start_time = str(timedelta(hours=attendance.employee_id.break_to))
                afternoon_start_time = datetime.strptime(afternoon_start_time, time_format).replace(
                    year=datetime.today().year)
                utc_afternoon_start = utc_dt(afternoon_start_time, tz).strftime(time_format)

                # Giờ tan làm (utc, str)
                attendance_end_time = str(timedelta(hours=attendance.employee_id.working_hour_to))
                attendance_end_time = datetime.strptime(attendance_end_time, time_format).replace(
                    year=datetime.today().year)
                utc_hour_end = utc_dt(attendance_end_time, tz).strftime(time_format)

                # Giờ xin vắng mặt (utc, str)
                hour_from = attendance.attendance_time_off.date_from.strftime(time_format)
                hour_to = attendance.attendance_time_off.date_to.strftime(time_format)

                """
                Không tính late_minutes nếu làm bù ngoài giờ (trước giờ checkin, sau giờ checkout, t7, cn) 
                Không tính late minute cho lần checkin thứ 2 trong ngày
                Tính late_minutes_approved khi timeoff nằm trong các trường hợp sau:
                - TH1: Xin vắng mặt từ đầu giờ, giờ kết thúc vắng mặt là trước giờ nghỉ trưa
                    --> số phút muộn = check_in - timeoff.date_to
                - TH2: Xin vắng mặt lưng chừng (ví dụ giờ chấm công policy là 8h, nhưng xin vắng mặt 10h-11h)
                    --> số phút muộn = check_in - working_hour_from
                - TH3: Xin nghỉ buổi sáng, check_in muộn vào buổi chiều
                    --> số phút muộn = check_in - giờ chấm công policy buổi chiều
                """
                if str(attendance.check_in.weekday()) not in working_days:  # check-in cuối tuần
                    pass

                elif utc_hour_start < attendance.time_check_in < utc_attendance_break:  # check-in sáng
                    # TH1
                    if hour_from <= utc_hour_start and hour_to < attendance.time_check_in < utc_attendance_break:
                        check_in = attendance.check_in
                        hour_start = attendance.attendance_time_off.date_to
                        attendance.late_minutes_approved = (check_in - hour_start).total_seconds() // 60

                    # TH2
                    elif hour_from > utc_hour_start:
                        check_in = datetime.strptime(attendance.check_in.strftime(time_format), time_format)
                        hour_start = datetime.strptime(utc_hour_start, time_format)
                        attendance.late_minutes_approved = (check_in - hour_start).total_seconds() // 60

                elif utc_afternoon_start < attendance.time_check_in < utc_hour_end:  # check-in chiều
                    # TH3
                    if hour_from <= utc_hour_start and utc_attendance_break <= hour_to <= utc_afternoon_start:
                        check_in = datetime.strptime(attendance.check_in.strftime(time_format), time_format)
                        hour_start = datetime.strptime(utc_afternoon_start, time_format)
                        attendance.late_minutes_approved = (check_in - hour_start).total_seconds() // 60

    @api.depends('check_in', 'attendance_time_off.state')
    def _compute_minutes_late(self):

        for attendance in self:
            tz = attendance.employee_id.tz
            attendance.minutes_late = 0

            working_days = []
            for att in attendance.employee_id.resource_calendar_id.attendance_ids:
                if att.dayofweek not in working_days:
                    working_days.append(att.dayofweek)

            # Convert float to datetime
            attendance_start_time_str = str(timedelta(hours=attendance.employee_id.working_hour_from))
            attendance_start_time = datetime.strptime(attendance_start_time_str, time_format).replace(
                                                        year=datetime.today().year)

            attendance_end_time_str = str(timedelta(hours=attendance.employee_id.working_hour_to))
            attendance_end_time = datetime.strptime(attendance_end_time_str, time_format).replace(
                                                        year=datetime.today().year)

            attendance_break_time_str = str(timedelta(hours=attendance.employee_id.break_from))
            attendance_break_time = datetime.strptime(attendance_break_time_str, time_format).replace(
                                                        year=datetime.today().year)

            afternoon_start_time_str = str(timedelta(hours=attendance.employee_id.break_to))
            afternoon_start_time = datetime.strptime(afternoon_start_time_str, time_format).replace(
                                                        year=datetime.today().year)

            # Convert to string - only time, utc
            utc_attendance_start = utc_dt(attendance_start_time, tz).strftime(time_format)
            utc_attendance_break = utc_dt(attendance_break_time, tz).strftime(time_format)
            utc_afternoon_start = utc_dt(afternoon_start_time, tz).strftime(time_format)
            utc_attendance_end = utc_dt(attendance_end_time, tz).strftime(time_format)

            check_in = attendance.time_check_in

            if attendance.attendance_time_off and attendance.attendance_time_off.state == 'validate':
                attendance.minutes_late = attendance.late_minutes_approved
            else:
                if str(attendance.check_in.weekday()) not in working_days:  # check-in cuối tuần
                    pass
                elif utc_attendance_start < check_in < utc_attendance_break:  # check-in sáng
                    delta = datetime.strptime(check_in, time_format) - datetime.strptime(utc_attendance_start, time_format)
                    attendance.minutes_late = delta.total_seconds() // 60
                elif utc_afternoon_start < check_in < utc_attendance_end:  # check-in chiều
                    delta = datetime.strptime(check_in, time_format) - datetime.strptime(utc_afternoon_start, time_format)
                    attendance.minutes_late = delta.total_seconds() // 60

    @api.depends('check_in')
    def _compute_check_in(self):
        for attendance in self:
            attendance.time_check_in = attendance.check_in.time()

    @api.depends('time_check_in', 'attendance_time_off')
    def _search_late_employee(self, opt, value):
        attendances = self.env['hr.attendance'].sudo().search([])

        if opt == '!=' and value == False and type(value) == bool:
            return [('id', 'in', attendances.ids)]

        if opt == '=' and value == False and type(value) == bool:
            return [('id', 'in', False)]

        def cmp(arg1, op, arg2):
            ops = {
                '<': operator.lt,
                '<=': operator.le,
                '=': operator.eq,
                '!=': operator.ne,
                '>=': operator.ge,
                '>': operator.gt
            }
            return ops.get(op)(arg1, arg2)

        res = []

        for rec in attendances:
            if cmp(rec.minutes_late, opt, value):
                res.append(int(rec.id))

        return [('id', 'in', res)]

    # Tổng số phút đi muộn theo group by
    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        res = super(BHHrAttendance, self).read_group(domain, fields, groupby, offset=offset, limit=limit,
                                                     orderby=orderby, lazy=lazy)
        lines = self.env['hr.attendance']
        for line in res:
            if '__domain' in line:
                lines = self.search(line['__domain'])
            if 'minutes_late' in fields:
                line['minutes_late'] = sum(lines.mapped('minutes_late'))

        return res

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

    # Auto Check Out by working time
    @api.model
    def auto_checkout_by_working_time(self, time):
        try:
            attendances = self.sudo().search([('check_out', '=', None)]).filtered(
                lambda r: r.employee_id.working_hour_to == time
            )
            attendances.write({'check_out': fields.Datetime.now()})

        except:
            pass

    # @api.depends('check_in', 'check_out')
    # def _compute_worked_hours(self):
    #     res = super(BHHrAttendance, self)._compute_worked_hours()
    #     for rec in self:
    #         employee = rec.employee_id
    #         time_zone = employee.tz
    #         employee_attendance_ids = employee.resource_calendar_id.attendance_ids
    #         morning_work_to = 0
    #         afternoon_work_from = 0
    #         if rec.check_in and rec.check_out:
    #             # đổi thời gian utc về thời gian theo timezone
    #             if time_zone:
    #                 check_out = rec.check_out.astimezone(pytz.timezone(time_zone)).replace(tzinfo=None)
    #                 check_in = rec.check_in.astimezone(pytz.timezone(time_zone)).replace(tzinfo=None)
    #             else:
    #                 check_out = rec.check_out
    #                 check_in = rec.check_in
    #             for attend in employee_attendance_ids:
    #                 if int(attend.dayofweek) == check_in.weekday():
    #                     if attend.day_period == 'morning':
    #                         morning_work_to = attend.hour_to
    #                     if attend.day_period == 'afternoon':
    #                         afternoon_work_from = attend.hour_from
    #
    #             hour_compare_with_check_in = int(morning_work_to)
    #             hour_compare_with_check_out = int(afternoon_work_from)
    #             minute_compare_with_check_in = int((morning_work_to - int(morning_work_to)) * 60.00)
    #             minute_compare_with_check_out = int((afternoon_work_from - int(afternoon_work_from)) * 60.00)
    #             different_time = afternoon_work_from - morning_work_to
    #             hour_break = int(different_time)
    #             minute_break = int((different_time - int(different_time)) * 60.00)
    #
    #             # so sánh thời gian check_in, check_out với ca làm việc của user.
    #             if check_in < check_in.replace(hour=hour_compare_with_check_in,
    #                                            minute=minute_compare_with_check_in, second=0) \
    #                     and check_out > check_in.replace(hour=hour_compare_with_check_out,
    #                                                      minute=minute_compare_with_check_out, second=0):
    #                 delta = rec.check_out - rec.check_in - timedelta(
    #                     hours=hour_break, minutes=minute_break)
    #                 rec.worked_hours = delta.total_seconds() / 3600.0
    #
    #     return res


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    whitelist_ip = fields.Char(string="Whitelist IP")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        whitelist_ip = self.env['ir.config_parameter'].sudo().get_param('whitelist_ip') or []
        res.update({'whitelist_ip': whitelist_ip,})
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param("whitelist_ip", self.whitelist_ip)

