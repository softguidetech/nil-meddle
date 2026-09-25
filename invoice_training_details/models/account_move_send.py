# -*- coding: utf-8 -*-

from odoo import api, models


class AccountMoveSend(models.AbstractModel):
    _inherit = 'account.move.send'

    @api.model
    def _get_default_pdf_report_id(self, move):
        """Use NIL ME custom invoice PDFs in Odoo's Send & Print flow."""
        if move.move_type in ('out_invoice', 'out_refund'):
            report_xmlid = (
                'invoice_training_details.account_invoices_pro_training_report'
                if move.pro_service_ids and not move.training_course_ids
                else 'invoice_training_details.account_invoices_training_report'
            )
            report = self.env.ref(report_xmlid, raise_if_not_found=False)
            if report:
                return report

        return super()._get_default_pdf_report_id(move)
