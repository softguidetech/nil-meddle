# -*- coding: utf-8 -*-
{
    'name': 'PO/SO Approval Route',
    'version': '1.0',
    'category': 'Purchase',
    'summary': 'Purchase and Sale Order Approval Routes',
    'description': """
        This module adds approval routes for purchase and sale orders.
        Features:
        - Custom approval workflow
        - Training details integration
        - Cost tracking
    """,
    'depends': ['base', 'purchase', 'sale', 'training'],
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_order_views.xml',
        'views/sale_order_views.xml',
        'views/purchase_training_details_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
