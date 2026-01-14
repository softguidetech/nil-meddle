/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";


export class CurrentLocation extends Component {
    setup() {
        this.state = useState({
            loading: false,
        });
        this.orm = useService("orm");
        this.action = useService("action");

        this.companyId = this.props.action.context.active_id;
        this.getLocation();
        debugger
    }

    async getLocation() {
        if (!navigator.geolocation) {
            alert("Geolocation is not supported by your browser.");
            this.redirectToForm();
            return;
        }

        this.state.loading = true;

        navigator.geolocation.getCurrentPosition(
            async (position) => {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;

                try {
                    await this.orm.call(
                        'res.company',
                        'update_coordinates',
                        [[this.companyId], lat, lon],
                        { context: this.env.context }
                    );

                    alert(`Location updated successfully`);
                } catch (e) {
                    alert("Failed to update location on server.");
                } finally {
                    this.state.loading = false;
                    this.redirectToForm();
                }
            },
            async (error) => {
                alert(`Error getting location: ${error.message}`);
                this.state.loading = false;
                this.redirectToForm();
            }
        );
    }

    redirectToForm() {
        this.env.config.historyBack();
    }
        
}

CurrentLocation.template = "attendance_location_validator.CurrentLocationTemplate";

registry.category("actions").add("attendance_location_validator.current_location_action", CurrentLocation);
