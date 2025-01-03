# -*- coding: utf-8 -*-
{
    'name': 'PO/SO Dynamic Approval Process',
    'version': '17.0.0.1',
    'summary': """
    Dynamic, Customizable and flexible approval cycle for purchase orders
    , Purchase dynamic approval 
    , PO dynamic approval 
    , RFQ dynamic approval 
    , purchase approval 
    , PO approval process
    , purchase order approval cycle 
    , purchase order approval process
    , purchase order approval workflow
    , flexible approve purchase order
    , dynamic approve PO
    , dynamic purchase approval
    , purchase multi approval
    , purchase multi-level approval
    , purchase order multiple approval
    
    , Sale dynamic approval 
    , SO dynamic approval 
    , Quotation dynamic approval 
    , Sale approval 
    , SO approval process
    , Sale order approval cycle 
    , Sale order approval process
    , Sale order approval workflow
    , flexible approve purchase order
    , dynamic approve SO
    , dynamic purchase approval
    , Sale multi approval
    , Sale multi-level approval
    , Sale order multiple approval
    """,
    'category': 'Purchases',
    'author': 'SGT',
    'support': 'support@softguidetech.com',
    'website': 'https://softguidetech.com',
    'license': 'OPL-1',
    'price': 19,
    'currency': 'EUR',
    'description':
        """
Purchase Order Approval Cycle
Sale Order Approval Cycle
=============================
This module helps to create multiple custom, flexible and dynamic approval route
for purchase orders/ Sale order based on team settings.

 
        """,
    'data': [
        'security/ir.model.access.csv',
        'security/purchase_security.xml',
        'security/sale_security.xml',
        'data/purchase_approval_route.xml',
        'data/sale_approval_route.xml',
        'views/purchase_approval_route.xml',
        'views/sale_approval_route.xml',
        'views/res_config_settings_views.xml',
    ],
    'depends': ['purchase','sale','sales_team','sale_management'],
    'qweb': [],
    'images': [
        'static/description/icon.gif',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
