# -*- coding: utf-8 -*-
{
    'name': 'Thamar HR Custom',
    'summary': 'Custom HR fields and modifications for Thamar',
    'description': """
        Custom HR module for Thamar:
        - Adds Hire Date field to employee payroll page
    """,
    'license': 'Other proprietary',
    'author': 'Thamar',
    'category': 'Human Resources',
    'version': '19.0.1.0.0',
    'depends': ['hr'],
    'data': [
        'views/hr_employee_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
