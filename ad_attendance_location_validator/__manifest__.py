{
    'name': 'Attendance Location Validator',
    'version': '17.0.1.0',
    'summary': 'Enforce office location check-in with remote check-in exceptions for attendance',
    'description': """
        This module enforces attendance check-in only from configured office location using GPS validation.
        ✔ Supports remote check-in exceptions based on employee or admin configuration.
        ✔ Seamlessly integrates with Odoo Attendance to enhance accuracy and compliance.
    """,
    'category': 'Human Resources/Attendance',
    'website': 'https://adreaminnovations.github.io/freelance_portfolio',
    'author': 'ADream Innovations',
    'license': 'LGPL-3',
    'depends': [
        'hr_attendance',
        'web',
    ],
    'data': [
        'views/actions.xml',
        'views/res_company_views.xml',
        'views/hr_employee_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ad_attendance_location_validator/static/src/client_actions/current_location_action.js',
            'ad_attendance_location_validator/static/src/client_actions/current_location_action.xml'
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'images': ['static/description/banner.png'],
}
