/* @odoo-module */

import { Component, useState } from "@odoo/owl";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { deserializeDateTime } from "@web/core/l10n/dates";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { useDebounced } from "@web/core/utils/timing";
import { session } from "@web/session";
const { DateTime } = luxon;


export class ActivityMenu extends Component {
    static components = {Dropdown, DropdownItem};
    static props = [];
    static template = "bhs_hr_attendance.attendance_menu";

    setup() {
        this.rpc = useService("rpc");
        this.orm = useService("orm");
        this.ui = useState(useService("ui"));
        this.userService = useService("user");
        this.employee = false;
        this.state = useState({
            checkedIn: false,
            isDisplayed: false
        });
        this.date_formatter = registry.category("formatters").get("float_time")
        this.onClickSignInOut = useDebounced(this.signInOut, 200, true);
        // load data but do not wait for it to render to prevent from delaying the whole webclient
        this.searchReadEmployee();
        this.searchReadAttendanceLocation();
    }

    async searchReadEmployee(){
        const result = await this.rpc("/bhs_hr_attendance/attendance_user_data");
        this.employee = result;
        if (this.employee.id) {
            this.hoursToday = this.date_formatter(
                this.employee.hours_today
            );
            this.hoursPreviouslyToday = this.date_formatter(
                this.employee.hours_previously_today
            );
            this.lastAttendanceWorkedHours = this.date_formatter(
                this.employee.last_attendance_worked_hours
            );
            this.lastCheckIn = deserializeDateTime(this.employee.last_check_in).toLocaleString(DateTime.TIME_SIMPLE);
            this.state.checkedIn = this.employee.attendance_state === "checked_in";
            this.isFirstAttendance = this.employee.hours_previously_today === 0;
            this.state.isDisplayed = this.employee.display_systray;

            // Compute late minutes and working until time
            const referenceDate = new Date('2000-01-01T00:00:00');

            // Calculate the corresponding milliseconds from the float time
            const working_hour_from_milliseconds = this.employee.working_hour_from * 3600000;
            const working_hour_to_milliseconds = this.employee.working_hour_to * 3600000;
            const break_from_milliseconds = this.employee.break_from * 3600000;
            const break_to_milliseconds = this.employee.break_to * 3600000;

            // Create a new Date object by adding the milliseconds to the reference date
            const working_hour_from = new Date(referenceDate.getTime() + working_hour_from_milliseconds).toLocaleTimeString();
            const working_hour_to = new Date(referenceDate.getTime() + working_hour_to_milliseconds).toLocaleTimeString();
            const break_from = new Date(referenceDate.getTime() + break_from_milliseconds).toLocaleTimeString();
            const break_to = new Date(referenceDate.getTime() + break_to_milliseconds).toLocaleTimeString();

            const [hour_from_str, minutes_from_str,seconds_from_str] = working_hour_from.split(':');
            const [hours_to_str, minutes_to_str,seconds_to_str] = working_hour_to.split(':');
            const [hour_break_from_str, minutes_break_from_str, seconds_break_from_str] = break_from.split(':');
            const [hour_break_to_str, minutes_break_to_str, seconds_break_to_str] = break_to.split(':');

            // Convert work_from hours, minutes to integers
            let hours_from = parseInt(hour_from_str);
            const minutes_from = parseInt(minutes_from_str);

            // Convert work_to hours, minutes to integers
            let hours_to = parseInt(hours_to_str);
            const minutes_to = parseInt(minutes_to_str);

            // Convert break_from hours, minutes to integers
            let break_from_hours = parseInt(hour_break_from_str);
            const break_from_minutes = parseInt(minutes_break_from_str);

            // Convert break_to hours, minutes to integers
            let break_to_hours = parseInt(hour_break_to_str);
            const break_to_minutes = parseInt(minutes_break_to_str);

            // Adjust the hours if it's in the 12-hour format and in the PM
            if (seconds_from_str.includes('PM') && hours_from <= 11) {
                hours_from += 12;
            }
            if (seconds_to_str.includes('PM') && hours_to <= 11) {
                hours_to += 12;
            }
            if (seconds_break_from_str.includes('PM') && break_from_hours <= 11) {
                break_from_hours += 12
            }
            if (seconds_break_to_str.includes('PM') && break_to_hours <= 11) {
                break_to_hours += 12
            }

            this.working_hour_from = `${String(hours_from).padStart(2, '0')}:${String(minutes_from).padStart(2, '0')}`;
            this.working_hour_to = `${String(hours_to).padStart(2, '0')}:${String(minutes_to).padStart(2, '0')}`;
            this.break_from = `${String(break_from_hours).padStart(2, '0')}:${String(break_from_minutes).padStart(2, '0')}`;
            this.break_to = `${String(break_to_hours).padStart(2, '0')}:${String(break_to_minutes).padStart(2, '0')}`;

            // Last attendees check in
            if (this.employee.attendance.check_in) {
                let last_attendance_time = new Date(this.employee.attendance.check_in + "Z");
                this.last_attendance_time = last_attendance_time.toLocaleTimeString()
                const [hours_str, minutes_str,seconds_str] = this.last_attendance_time.split(':');

                // Convert the hours and minutes, seconds to integers
                let last_hours = parseInt(hours_str);
                const last_minutes = parseInt(minutes_str);

                // Adjust the hours if it's in the 12-hour format and in the PM
                if (seconds_str.includes('PM') && last_hours <= 11) {
                    last_hours += 12;
                }

                this.last_attendance_time = `${String(last_hours).padStart(2, '0')}:${String(last_minutes).padStart(2, '0')}`;

                // compute late time
                if (this.last_attendance_time < this.break_from) {
                    var late_hours = last_hours - hours_from;
                    var late_minutes = last_minutes - minutes_from;

                } else if (this.last_attendance_time < this.working_hour_to) {
                    var late_hours = last_hours - break_to_hours;
                    var late_minutes = last_minutes - break_to_minutes;
                }

                if (late_minutes < 0) {
                    late_minutes += 60;
                    late_hours--;
                }
                if (late_hours < 0) {
                    late_hours += 24;
                }

                var hours_ot = hours_to + late_hours;
                var minutes_ot = minutes_to + late_minutes;

                if (minutes_ot >= 60) {
                    hours_ot++;
                    minutes_ot -= 60;
                }

                if (hours_ot >= 24) {
                    hours_ot -= 24;
                }

                this.workingTo = `${String(hours_ot).padStart(2, '0')}:${String(minutes_ot).padStart(2, '0')}`;
                this.lateMinutes = late_hours * 60 + late_minutes

                if ((this.last_attendance_time > this.working_hour_from && this.last_attendance_time < this.break_from) ||
                    (this.last_attendance_time > this.break_to && this.last_attendance_time < this.working_hour_to)) {
                    this.isLate = true;
                } else {
                    this.isLate = false;
                }
            } else {
                this.isLate = false;
            }
        }
    }

    async searchReadAttendanceLocation(){
        const locations = await this.orm.searchRead(
            'hr.attendance.location', [],
            ['id', 'code', 'name','loc_class_name','main_location'],
        );
        this.locations = locations;
    }

    async signInOut(loc_id) {
        $(".checkinButton").prop('disabled', true);

        if (loc_id) {
            var id_location = parseInt(loc_id);
        }

        if (!navigator.geolocation) {
            this.displayNotification({ title: 'Geolocation is not supported by this browser.', type: 'danger' });
        }

        navigator.geolocation.getCurrentPosition(
            async ({coords: {latitude, longitude}}) => {
                await this.rpc(
                    "/bhs_hr_attendance/systray_check_in_out",
                    {latitude, longitude, id_location}
                )

                await this.searchReadEmployee();
                await this.searchReadAttendanceLocation();
            },
            async err => {

                switch(err.code) {
                    case err.PERMISSION_DENIED:
                        this.displayNotification({ title: 'User denied the request for Geolocation.', type: 'danger' });
                        break;
                    case err.POSITION_UNAVAILABLE:
                      this.displayNotification({ title: 'Location information is unavailable.', type: 'danger' });
                      break;
                    case err.TIMEOUT:
                      this.displayNotification({ title: 'The request to get user location timed out.', type: 'danger' });
                      break;
                    case err.UNKNOWN_ERROR:
                      this.displayNotification({ title: 'An unknown error occurred.', type: 'danger' });
                      break;
                }
                await this.searchReadEmployee();
                await this.searchReadAttendanceLocation();
            }
        )

    }
}

export const systrayAttendance = {
    Component: ActivityMenu,
};

registry.category("systray").remove("hr_attendance.attendance_menu")
registry.category("systray").add("bhs_hr_attendance.attendance_menu", systrayAttendance, { sequence: 101 });
