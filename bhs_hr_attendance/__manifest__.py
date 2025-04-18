# -*- encoding: utf-8 -*-
{
    'name': "HR Attendance Management",
    'version': '1.0',
    'summary': 'HR Attendance Management',
    'category': 'HR',
    'description': """
        A product of Bac Ha Software allows to check in with location, multi workingtime, 
        tracking late minutes, restrict attendance with IP.
    """,
    "depends": ['web', 'web_editor', 'resource', 'hr', 'hr_attendance', 'hr_holidays'],
    'data': [
        'security/ir.model.access.csv',
        'data/attendance_location_data.xml',
        'data/attendance_data.xml',
        'views/attendance_late_time_view.xml',
        'views/attendance_location_view.xml',
        'views/res_config_settings_views.xml',
        'views/res_users_view.xml',
        'views/resource_calendar_view.xml',
        'views/search_name_attendances_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'bhs_hr_attendance/static/src/**/*',
        ],
    },
    'license': 'LGPL-3',
    'images': ['static/description/banner.png'],

    # Author
    'author': 'Bac Ha Software',
    'website': 'https://bachasoftware.com',
    'maintainer': 'Bac Ha Software',
    
    'installable': True,
    'application': True,
    'auto_install': False
}
