# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

import logging

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # ── Custom input fields ──
    external_experience_years = fields.Float(
        string='External Insured Experience (Years)',
        default=0.0,
        help="Previous insured service years that count towards total service "
             "for annual leave bonus calculation.",
        tracking=True,
    )
    is_hazardous_location = fields.Boolean(
        string='Hazardous / Remote Location',
        default=False,
        help="If enabled, the employee receives an additional 7 days of annual "
             "leave on top of their base entitlement.",
        tracking=True,
    )

    # ── Computed entitlement detail fields (readonly, for transparency) ──
    leave_employee_age = fields.Integer(
        string='Employee Age',
        compute='_compute_leave_entitlement_details',
        store=True,
        help="Current age of the employee based on the birthday field.",
    )
    leave_current_service_years = fields.Float(
        string='Current Service Years',
        compute='_compute_leave_entitlement_details',
        store=True,
        help="Years of service at the current company (based on contract start date).",
    )
    leave_total_service_years = fields.Float(
        string='Total Service Years',
        compute='_compute_leave_entitlement_details',
        store=True,
        help="Current service years + external insured experience years.",
    )
    leave_base_annual_days = fields.Float(
        string='Base Annual Days',
        compute='_compute_leave_entitlement_details',
        store=True,
        help="Base annual leave entitlement: 21 days (standard), "
             "14 days (first year, hired before Sep), 8 days (first year, hired Sep onwards).",
    )
    leave_age_bonus = fields.Float(
        string='Age 50+ Bonus',
        compute='_compute_leave_entitlement_details',
        store=True,
        help="9 extra days if employee is 50 years old or older.",
    )
    leave_experience_bonus = fields.Float(
        string='10+ Years Experience Bonus',
        compute='_compute_leave_entitlement_details',
        store=True,
        help="9 extra days if total service years >= 10.",
    )
    leave_hazardous_bonus = fields.Float(
        string='Hazardous Location Bonus',
        compute='_compute_leave_entitlement_details',
        store=True,
        help="7 extra days if employee works in a hazardous/remote location.",
    )
    leave_total_annual_entitlement = fields.Float(
        string='Total Annual Entitlement',
        compute='_compute_leave_entitlement_details',
        store=True,
        help="Sum of base + age bonus + experience bonus + hazardous bonus.",
    )
    leave_casual_entitlement = fields.Float(
        string='Casual Leave Entitlement',
        compute='_compute_leave_entitlement_details',
        store=True,
        help="Casual leave entitlement: always 7 days per year.",
    )

    # ── Monthly Accrual Status (live, non-stored) ──
    leave_annual_monthly_rate = fields.Float(
        string='Monthly Accrual Rate',
        compute='_compute_accrual_status',
        help="Annual entitlement / 12 — the number of days that accrue each month.",
    )
    leave_annual_months_accrued = fields.Integer(
        string='Months Accrued',
        compute='_compute_accrual_status',
        help="Number of months of accrual elapsed this year (from hire month or January).",
    )
    leave_annual_accrual_cap = fields.Float(
        string='Annual Accrual Cap (Current Month)',
        compute='_compute_accrual_status',
        help="Maximum annual leave days available as of the current month.",
    )
    leave_annual_accrued_remaining = fields.Float(
        string='Accrued Balance Remaining',
        compute='_compute_accrual_status',
        help="Accrual cap minus leaves already taken/pending this year.",
    )

    @api.depends('birthday', 'contract_date_start', 'external_experience_years', 'is_hazardous_location')
    def _compute_leave_entitlement_details(self):
        """Compute all leave entitlement breakdown fields for transparency."""
        today = fields.Date.today()
        for emp in self:
            details = self.env['hr.leave.allocation']._compute_employee_entitlement(emp, today)
            emp.leave_employee_age = details['age']
            emp.leave_current_service_years = details['current_service_years']
            emp.leave_total_service_years = details['total_service_years']
            emp.leave_base_annual_days = details['base_days']
            emp.leave_age_bonus = details['age_bonus']
            emp.leave_experience_bonus = details['experience_bonus']
            emp.leave_hazardous_bonus = details['hazardous_bonus']
            emp.leave_total_annual_entitlement = details['total_annual']
            emp.leave_casual_entitlement = details['casual_days']

    def _compute_accrual_status(self):
        """Compute the live monthly accrual status for annual leave."""
        today = fields.Date.today()
        year = today.year
        month = today.month

        Allocation = self.env['hr.leave.allocation'].sudo()
        Leave = self.env['hr.leave'].sudo()
        annual_type_cache = {}

        for emp in self:
            # Default values
            emp.leave_annual_monthly_rate = 0.0
            emp.leave_annual_months_accrued = 0
            emp.leave_annual_accrual_cap = 0.0
            emp.leave_annual_accrued_remaining = 0.0

            # Find the annual leave type for this employee's company
            company_id = emp.company_id.id if emp.company_id else False
            if company_id not in annual_type_cache:
                annual_type_cache[company_id] = Allocation._get_annual_leave_type(emp.company_id)
            annual_type = annual_type_cache[company_id]

            if not annual_type or not annual_type.use_monthly_accrual:
                continue

            # Total allocation for this year
            allocations = Allocation.search([
                ('employee_id', '=', emp.id),
                ('holiday_status_id', '=', annual_type.id),
                ('state', '=', 'validate'),
                ('leave_year', '=', year),
            ])
            total_allocated = sum(allocations.mapped('number_of_days'))
            if not total_allocated:
                continue

            monthly_rate = total_allocated / 12.0

            # Determine start month for accrual
            contract_start = emp.contract_date_start
            if contract_start and contract_start.year == year:
                start_month = contract_start.month
            else:
                start_month = 1

            months_accrued = max(0, month - start_month + 1)
            accrual_cap = min(round(monthly_rate * months_accrued, 2), total_allocated)

            # Leaves taken/pending this year
            from datetime import datetime as dt
            existing_leaves = Leave.search([
                ('employee_id', '=', emp.id),
                ('holiday_status_id', '=', annual_type.id),
                ('state', 'not in', ('refuse', 'cancel')),
                ('date_from', '>=', dt(year, 1, 1)),
                ('date_from', '<', dt(year + 1, 1, 1)),
            ])
            total_taken = sum(existing_leaves.mapped('number_of_days'))

            emp.leave_annual_monthly_rate = round(monthly_rate, 2)
            emp.leave_annual_months_accrued = months_accrued
            emp.leave_annual_accrual_cap = accrual_cap
            emp.leave_annual_accrued_remaining = round(max(0.0, accrual_cap - total_taken), 2)

    @api.model_create_multi
    def create(self, vals_list):
        """Auto-generate leave allocations when a new employee is created."""
        employees = super().create(vals_list)
        for employee in employees:
            try:
                self.env['hr.leave.allocation']._generate_employee_allocations(employee)
            except Exception as e:
                _logger.warning(
                    "Failed to auto-generate leave allocations for employee %s (ID: %s): %s",
                    employee.name, employee.id, e,
                )
        return employees

    def action_regenerate_leave_allocations(self):
        """Manual button action to regenerate leave allocations for the current year."""
        for employee in self:
            self.env['hr.leave.allocation']._generate_employee_allocations(employee)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Leave Allocations"),
                'message': _("Leave allocations have been regenerated successfully."),
                'type': 'success',
                'sticky': False,
            },
        }


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    # Mirror input fields as related (readonly by nature on public model)
    external_experience_years = fields.Float(
        string='External Insured Experience (Years)',
        related='employee_id.external_experience_years',
        readonly=True,
    )
    is_hazardous_location = fields.Boolean(
        string='Hazardous / Remote Location',
        related='employee_id.is_hazardous_location',
        readonly=True,
    )

    # Mirror computed fields as related from the real employee
    leave_employee_age = fields.Integer(
        string='Employee Age',
        related='employee_id.leave_employee_age',
    )
    leave_current_service_years = fields.Float(
        string='Current Service Years',
        related='employee_id.leave_current_service_years',
    )
    leave_total_service_years = fields.Float(
        string='Total Service Years',
        related='employee_id.leave_total_service_years',
    )
    leave_base_annual_days = fields.Float(
        string='Base Annual Days',
        related='employee_id.leave_base_annual_days',
    )
    leave_age_bonus = fields.Float(
        string='Age 50+ Bonus',
        related='employee_id.leave_age_bonus',
    )
    leave_experience_bonus = fields.Float(
        string='10+ Years Experience Bonus',
        related='employee_id.leave_experience_bonus',
    )
    leave_hazardous_bonus = fields.Float(
        string='Hazardous Location Bonus',
        related='employee_id.leave_hazardous_bonus',
    )
    leave_total_annual_entitlement = fields.Float(
        string='Total Annual Entitlement',
        related='employee_id.leave_total_annual_entitlement',
    )
    leave_casual_entitlement = fields.Float(
        string='Casual Leave Entitlement',
        related='employee_id.leave_casual_entitlement',
    )
