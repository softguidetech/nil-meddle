/** @odoo-module **/

import { Component, onMounted, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

class NilTermsEditor extends Component {
    static template = "invoice_training_details.NilTermsEditor";
    static props = { ...standardFieldProps };

    setup() {
        this.editor = useRef("editor");

        onMounted(() => {
            this.editor.el.innerHTML =
                this.props.record.data[this.props.name] || "";
        });
    }

    save() {
        this.props.record.update({
            [this.props.name]: this.editor.el.innerHTML,
        });
    }

    cmd(ev) {
        ev.preventDefault();

        this.editor.el.focus();

        document.execCommand(
            "styleWithCSS",
            false,
            true
        );

        document.execCommand(
            ev.currentTarget.dataset.cmd,
            false,
            null
        );

        this.save();
    }

    block(ev) {
        if (!ev.target.value) {
            return;
        }

        this.editor.el.focus();

        document.execCommand(
            "formatBlock",
            false,
            ev.target.value
        );

        ev.target.value = "";

        this.save();
    }

    fontSize(ev) {
        if (!ev.target.value) {
            return;
        }

        this.editor.el.focus();

        document.execCommand(
            "styleWithCSS",
            false,
            true
        );

        document.execCommand(
            "fontSize",
            false,
            ev.target.value
        );

        ev.target.value = "";

        this.save();
    }

    color(ev) {
        this.editor.el.focus();

        document.execCommand(
            "styleWithCSS",
            false,
            true
        );

        document.execCommand(
            "foreColor",
            false,
            ev.target.value
        );

        this.save();
    }

    selectedBlocks() {
        const sel = window.getSelection();

        if (!sel || !sel.rangeCount) {
            return [];
        }

        const range = sel.getRangeAt(0);

        let node =
            range.startContainer.nodeType === 1
                ? range.startContainer
                : range.startContainer.parentElement;

        const block =
            node &&
            node.closest(
                "p,div,li,td,th,h1,h2,h3,h4"
            );

        return (
            block &&
            this.editor.el.contains(block)
        )
            ? [block]
            : [];
    }

    lineHeight(ev) {
        const value = ev.target.value;

        if (!value) {
            return;
        }

        for (const el of this.selectedBlocks()) {
            el.style.lineHeight = value;
        }

        ev.target.value = "";

        this.save();
    }

    paragraphSpace(ev) {
        const value = ev.target.value;

        if (value === "") {
            return;
        }

        for (const el of this.selectedBlocks()) {
            el.style.marginBottom =
                `${value}px`;
        }

        ev.target.value = "";

        this.save();
    }

    insertTable() {
        this.editor.el.focus();

        const rows = Math.max(
            1,
            Math.min(
                20,
                parseInt(
                    prompt(
                        "Rows",
                        "3"
                    ) || "3"
                )
            )
        );

        const cols = Math.max(
            1,
            Math.min(
                12,
                parseInt(
                    prompt(
                        "Columns",
                        "3"
                    ) || "3"
                )
            )
        );

        let html =
            '<table class="nil-edit-table"><tbody>';

        for (
            let row = 0;
            row < rows;
            row++
        ) {
            html += "<tr>";

            for (
                let col = 0;
                col < cols;
                col++
            ) {
                html += "<td><br/></td>";
            }

            html += "</tr>";
        }

        html +=
            "</tbody></table><p><br/></p>";

        document.execCommand(
            "insertHTML",
            false,
            html
        );

        this.save();
    }

    cell() {
        const sel = window.getSelection();

        if (!sel || !sel.rangeCount) {
            return null;
        }

        let node =
            sel
                .getRangeAt(0)
                .startContainer;

        node =
            node.nodeType === 1
                ? node
                : node.parentElement;

        const cell =
            node &&
            node.closest("td,th");

        return (
            cell &&
            this.editor.el.contains(cell)
        )
            ? cell
            : null;
    }

    addRow() {
        const cell = this.cell();

        if (!cell) {
            return;
        }

        const row = cell.parentElement;

        const clone =
            row.cloneNode(true);

        clone
            .querySelectorAll(
                "td,th"
            )
            .forEach(
                (item) =>
                    item.innerHTML =
                        "<br/>"
            );

        row.after(clone);

        this.save();
    }

    delRow() {
        const cell = this.cell();

        if (!cell) {
            return;
        }

        cell
            .parentElement
            .remove();

        this.save();
    }

    addCol() {
        const cell = this.cell();

        if (!cell) {
            return;
        }

        const table =
            cell.closest("table");

        const index =
            cell.cellIndex;

        table
            .querySelectorAll("tr")
            .forEach((row) => {
                const ref =
                    row.cells[index];

                const newCell =
                    document.createElement(
                        ref &&
                        ref.tagName === "TH"
                            ? "th"
                            : "td"
                    );

                newCell.innerHTML =
                    "<br/>";

                if (ref) {
                    ref.after(
                        newCell
                    );
                } else {
                    row.appendChild(
                        newCell
                    );
                }
            });

        this.save();
    }

    delCol() {
        const cell = this.cell();

        if (!cell) {
            return;
        }

        const table =
            cell.closest("table");

        const index =
            cell.cellIndex;

        table
            .querySelectorAll("tr")
            .forEach((row) => {
                if (
                    row.cells[index]
                ) {
                    row
                        .cells[index]
                        .remove();
                }
            });

        this.save();
    }

    cellPadding() {
        const cell = this.cell();

        if (!cell) {
            return;
        }

        const value =
            prompt(
                "Cell padding (px)",
                "8"
            );

        if (value !== null) {
            cell
                .closest("table")
                .querySelectorAll(
                    "td,th"
                )
                .forEach(
                    (item) => {
                        item.style.padding =
                            `${parseInt(value) || 0}px`;
                    }
                );
        }

        this.save();
    }

    border() {
        const cell = this.cell();

        if (!cell) {
            return;
        }

        const value =
            prompt(
                "Border width (px)",
                "1"
            );

        if (value !== null) {
            cell
                .closest("table")
                .querySelectorAll(
                    "td,th"
                )
                .forEach(
                    (item) => {
                        item.style.border =
                            `${parseInt(value) || 0}px solid #999`;
                    }
                );
        }

        this.save();
    }

    cellBg() {
        const cell = this.cell();

        if (!cell) {
            return;
        }

        const value =
            prompt(
                "Cell background color",
                "#ffffff"
            );

        if (value) {
            cell.style.backgroundColor =
                value;
        }

        this.save();
    }
}

NilTermsEditor.template =
    "invoice_training_details.NilTermsEditor";

registry
    .category("fields")
    .add(
        "nil_terms_editor",
        {
            component:
                NilTermsEditor,

            supportedTypes: [
                "html",
                "text",
            ],
        }
    );
