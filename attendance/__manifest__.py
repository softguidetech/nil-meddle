{
    'name': 'Attendance Tracking',
    'version': '1.0',
    'depends': ['hr', 'base'],  # Ensure this includes any dependencies for HR and base modules
    'author': 'RK',
    'category': 'Human Resources',
    'description': 'Module to track and calculate late arrivals with grace period',
    'data': [
        # Views for attendance (form view, tree view)
        'views/attendance_view.xml',  # Add the path to your XML views here
    ],
    'installable': True,
    'auto_install': False,
}
