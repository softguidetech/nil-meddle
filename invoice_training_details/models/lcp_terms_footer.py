# -*- coding: utf-8 -*-

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

    def _lcp_enterone_so_terms(self, courses):
        return super()._lcp_enterone_so_terms(courses) + TERMS_FOOTER

    def _lcp_koenig_po_terms(self, courses):
        return super()._lcp_koenig_po_terms(courses) + TERMS_FOOTER
