# -*- coding: utf-8 -*-
{
    "name": "HR Custom",
    "version": "17.0",
    "summary": "HR Management",
    "description": """
       HR Management
    """,
    "category": 'Customization',

    # Author
    "author": "Bahelim Munafkhan",
    "website": "https://www.softguidetech.com",
    "license": "LGPL-3",

    # Dependency
    "depends": ['web', 'base', 'hr_contract', 'hr_attendance'],

    "data": [
        "views/contract_view.xml",
        "views/hr_attendance_view.xml",
        "security/ir.model.access.csv",
    ],

    "installable": True,
    "application": False,
    "auto_install": False
}
