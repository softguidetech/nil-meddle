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
    "website": "https://www.softguidetech.com",
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
        "views/training_costs_views.xml",  # Assuming this is the new view for the training costs model

        # Report
        "reports/custom_invoice_layout.xml",
        "reports/report_invoice.xml",
        "reports/report_quotation.xml",
        
        "reports/report_pro_invoice.xml",
        "reports/report_pro_quotation.xml",
        
        "reports/report_action.xml",
        # Add your training costs model view file here (if needed)
    ],

    "installable": True,
    "application": False,
    "auto_install": False
}
