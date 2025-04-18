# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Attendance Auto Checkout',
    'version': '1.0',
    'category': 'Human Resources',
    'sequence': 335,
    "summary": "Automatically check out if employee forgets to check out",
    'description': """
        Automatically check out if employee forgets to check out
    """,
    'website': 'https://www.odoo.com/app/employees',
    'depends': ['hr_attendance'],
    'data': [
        'views/attendance_auto_checkout.xml',
        'data/attendance_data.xml',
    ],
    'license': 'LGPL-3',
    'images': ['static/description/banner.png'],
    # Author
    'author': 'Bac Ha Software',
    'website': 'https://bachasoftware.com',
    'maintainer': 'Bac Ha Software',

    'installable': True,
    'application': True,
    'auto_install': False,
}
