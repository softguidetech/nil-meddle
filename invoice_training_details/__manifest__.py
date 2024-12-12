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
    "depends": ['account'],

    "data": [
        "data/report_paperformat.xml",
        "security/ir.model.access.csv",
        "views/account_move_views.xml",
        # Report
        "reports/custom_invoice_layout.xml",
        "reports/report_invoice.xml",
        "reports/report_action.xml",
    ],

    "installable": True,
    "application": False,
    "auto_install": False
}
