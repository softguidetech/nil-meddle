# -*- coding: utf-8 -*-
{
    "name": "Invoice Training Details",
    "version": "17.0",
    "summary": "Enhancements for Invoice Training Details",
    "description": "Customizations for invoicing related to training services, including improved reporting and CRM integration.",
    "category": "Customization",
    
    # Author Information
    "author": "SoftGuide Tech",
    "website": "https://www.softguidetech.com",
    "license": "LGPL-3",
    
    # Dependencies
    "depends": [
        "account", 
        "crm", 
        "sale_management", 
        "hr", 
        "product"
    ],

    # Data Files
    "data": [
        "data/report_paperformat.xml",
        "security/ir.model.access.csv",
        "views/account_move_views.xml",
        "views/crm_lead_views.xml",
        "views/sale_order_views.xml",
        "views/res_company_views.xml",
        # Reports
        "reports/custom_invoice_layout.xml",
        "reports/report_invoice.xml",
        "reports/report_quotation.xml",
        "reports/report_pro_invoice.xml",
        "reports/report_pro_quotation.xml",
        "reports/report_action.xml",
    ],

    # Installation Settings
    "installable": True,
    "application": False,
    "auto_install": False,
}
