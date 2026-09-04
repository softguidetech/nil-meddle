/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { FormCompiler } from "@web/views/form/form_compiler";

/*
 * Force Odoo form chatter to stay below the form
 * at every screen width / zoom level.
 */
patch(FormCompiler.prototype, {
    compile(node, params) {
        const result = super.compile(node, params);

        const formRenderer =
            result?.matches?.(".o_form_renderer")
                ? result
                : result?.querySelector?.(".o_form_renderer");

        if (!formRenderer) {
            return result;
        }

        const chatters = result.querySelectorAll(
            ".o-mail-Form-chatter"
        );

        if (!chatters.length) {
            return result;
        }

        formRenderer.classList.add(
            "o_nil_force_bottom_chatter"
        );

        for (const chatter of chatters) {

            /*
             * Odoo normally adds "o-aside" on wide screens.
             * Remove the dynamic class so zoom / breakpoints
             * cannot move chatter back to the right.
             */
            chatter.removeAttribute(
                "t-attf-class"
            );

            chatter.classList.remove(
                "o-aside"
            );

            chatter.classList.add(
                "o_nil_bottom_chatter"
            );

            /*
             * Tell the Chatter component explicitly
             * that it is NOT an aside.
             */
            const chatterComponent =
                chatter.querySelector(
                    "t[t-component='__comp__.mailComponents.Chatter']"
                );

            if (chatterComponent) {
                chatterComponent.setAttribute(
                    "isChatterAside",
                    "false"
                );

                /*
                 * Normal external chatter should not
                 * behave as if it lives inside the sheet.
                 */
                if (
                    !chatter.closest(
                        ".o_form_sheet_bg"
                    )
                ) {
                    chatterComponent.setAttribute(
                        "isInFormSheetBg",
                        "false"
                    );
                }
            }
        }

        return result;
    },
});
