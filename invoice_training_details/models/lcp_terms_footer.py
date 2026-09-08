# -*- coding: utf-8 -*-

from odoo import models


TERMS_FOOTER = (
    '<div style="font-family:Arial,Helvetica,sans-serif;font-size:16px;'
    'line-height:1.45;margin-top:14px;">'
    '<div><strong>Payment Terms:</strong> Net60 after delivery.</div>'
    '<div>Please notify us immediately if you are unable to deliver as specified.</div>'
    '</div>'
)


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    def _lcp_enterone_so_terms(self, courses):
        return super()._lcp_enterone_so_terms(courses) + TERMS_FOOTER

    def _lcp_koenig_po_terms(self, courses):
        return super()._lcp_koenig_po_terms(courses) + TERMS_FOOTER
