# -*- coding: utf-8 -*-
{
    "name": "Invoice Training Details",
    "version": "17.0.1.8",
    "summary": "Enhancements for Invoice Training Details",
    "description": "Customizations for invoicing related to training services, including improved reporting and CRM integration.",
    "category": "Customization",

    "author": "SoftGuide Tech",
    "website": "https://www.softguidetech.com",
    "license": "LGPL-3",

    "depends": [
        "account",
        "crm",
        "sale_management",
        "hr",
        "product"
    ],

    "data": [
        "data/report_paperformat.xml",
        "security/ir.model.access.csv",
        "views/account_move_views.xml",

        # IMPORTANT: LCP before CRM main inherited view.
        "views/lcp_details_views.xml",
        "views/crm_lead_views.xml",

        "views/sale_order_views.xml",
        "views/res_company_views.xml",

        "reports/custom_invoice_layout.xml",
        "reports/report_invoice.xml",
        "reports/report_quotation.xml",
        "reports/report_pro_invoice.xml",
        "reports/report_po_document.xml",
        "reports/report_action.xml",
        "reports/report_invoice_KSA.xml",
    ],

    "assets": {
        "web.assets_backend": [
            "invoice_training_details/static/src/css/lcp_details.css",
        ],
    },

    "installable": True,
    "application": False,
    "auto_install": False,
}
