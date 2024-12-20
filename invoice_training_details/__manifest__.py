# -*- coding: utf-8 -*
{
    "name": "Invoice Training Details",
    "version": "17.0",
    "summary": "Invoice Training Details",
    "description": """
       Invoice Training Details.
    """,
    "category": 'Customization',

    # Author
    "author": "",
    "website": "https://www.example.com",
    "license": "LGPL-3",

    # Dependency
    "depends": ['account', 'crm', 'sale_management','hr','product'],

    "data": [
        "data/report_paperformat.xml",
        "security/ir.model.access.csv",
        "views/account_move_views.xml",
        "views/crm_lead_views.xml",
        "views/sale_order_views.xml",
        "views/res_company_views.xml",
        # Report
        "reports/custom_invoice_layout.xml",
        "reports/report_invoice.xml",
        "reports/report_quotation.xml",
        "reports/report_action.xml",
    ],

    "installable": True,
    "application": False,
    "auto_install": False
}
