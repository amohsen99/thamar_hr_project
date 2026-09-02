# -*- coding: utf-8 -*-
{
    'name': 'Thamar HR Leaves',
    'summary': 'Egyptian Labor Law Leave Management – Dynamic entitlements, auto-allocation & yearly cron',
    'description': """
        Comprehensive leave management module for Thamar:
        - Casual Leave (7 days/year, non-carryover, expires Dec 31)
        - Annual Leave (dynamic computation based on service year, age, experience, hazardous location)
        - Monthly accrual for annual leave
        - Auto-allocation on employee creation
        - Yearly cron job (Jan 1) for recalculation and carryover
        - Transparent readonly entitlement fields on employee form
    """,
    'license': 'Other proprietary',
    'author': 'Thamar',
    'category': 'Human Resources/Time Off',
    'version': '19.0.1.0.0',
    'depends': [
        'hr',
        'hr_holidays',
        'thamar_hr_custom',
    ],
    'data': [
        'data/leave_type_data.xml',
        'data/ir_cron_data.xml',
        'views/hr_employee_views.xml',
        'views/hr_leave_type_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
