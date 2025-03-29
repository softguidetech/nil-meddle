# -*- coding: utf-8 -*-
# Part of 4Minds. See LICENSE file for full copyright and licensing details.
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
        "views/hr_attendance_view.xml",  # Add this line to include the new view
        "security/ir.model.access.csv",  # Add this line to include access rights
    ],

    "installable": True,
    "application": False,
    "auto_install": False
}
