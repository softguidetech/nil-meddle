# -*- coding: utf-8 -*-

from html import escape

from odoo import models


TERMS_FOOTER = (
    '<div style="font-family:Arial,Helvetica,sans-serif;font-size:18px;'
    'line-height:1.45;margin-top:16px;">'
    '<div style="font-weight:700;margin-bottom:4px;">Payment Terms:</div>'
    '<ul style="margin:0;padding-left:22px;">'
    '<li style="margin:0 0 3px 0;">Net60 after delivery.</li>'
    '<li style="margin:0;">Please notify us immediately if you are unable to deliver as specified.</li>'
    '</ul>'
    '</div>'
)


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    def _lcp_end_customer_html(self):
        self.ensure_one()
        end_customer = self.training_name.display_name if self.training_name else ''
        return (
            '<div style="font-family:Arial,Helvetica,sans-serif;font-size:18px;'
            'line-height:1.4;margin-bottom:10px;">'
            '<strong>End Customer:</strong> %s'
            '</div>'
        ) % escape(end_customer)

    def _lcp_enterone_so_terms(self, courses):
        html = super()._lcp_enterone_so_terms(courses)
        html = html.replace('font-size:16px', 'font-size:18px')
        html = html.replace('padding:8px 11px', 'padding:10px 14px')
        html = html.replace(
            'width:auto;display:inline-table;',
            'width:auto;min-width:520px;display:inline-table;'
        )
        return html + TERMS_FOOTER

    def _lcp_koenig_po_terms(self, courses):
        return (
            self._lcp_end_customer_html()
            + super()._lcp_koenig_po_terms(courses)
            + TERMS_FOOTER
        )
