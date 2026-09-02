# -*- coding: utf-8 -*-
"""Monthly accrual validation for leave requests.

Enforces the rule: employees can only take leave up to their
accrued monthly balance (Total Days / 12 × months elapsed).
"""
import logging
from datetime import datetime, date

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    @api.constrains('date_from', 'date_to', 'holiday_status_id', 'employee_id', 'number_of_days')
    def _check_monthly_accrual_cap(self):
        """Block leave requests that exceed the monthly rate unless HR overrides."""
        for leave in self:
            if leave.state in ('refuse', 'cancel'):
                continue

            leave_type = leave.holiday_status_id
            if not leave_type.use_monthly_accrual:
                continue

            if not leave.employee_id or not leave.date_from:
                continue

            year = leave.date_from.year

            allocations = self.env['hr.leave.allocation'].sudo().search([
                ('employee_id', '=', leave.employee_id.id),
                ('holiday_status_id', '=', leave_type.id),
                ('state', '=', 'validate'),
                ('leave_year', '=', year),
            ])
            total_allocated = sum(allocations.mapped('number_of_days'))
            if not total_allocated:
                continue

            leave_id = leave._origin.id if leave._origin else leave.id
            domain = [
                ('employee_id', '=', leave.employee_id.id),
                ('holiday_status_id', '=', leave_type.id),
                ('state', 'not in', ('refuse', 'cancel')),
                ('date_from', '>=', datetime(year, 1, 1)),
                ('date_from', '<', datetime(year + 1, 1, 1)),
            ]
            if leave_id:
                domain.append(('id', '!=', leave_id))

            total_taken = sum(self.sudo().search(domain).mapped('number_of_days'))

            today = fields.Date.today()
            contract_start = leave.employee_id.contract_date_start
            if contract_start and contract_start.year == year:
                start_month = contract_start.month
            else:
                start_month = 1

            months_elapsed = max(1, today.month - start_month + 1)
            annual_entitlement = leave.employee_id.leave_total_annual_entitlement or total_allocated
            monthly_rate = annual_entitlement / 12.0
            accrued_balance = monthly_rate * months_elapsed
            available = max(0, accrued_balance - total_taken)

            requested = leave.number_of_days or 0
            if requested > available and not leave.accrual_limit_override:
                raise ValidationError(_(
                    "Monthly Accrual Limit Exceeded!\n\n"
                    "%(employee)s cannot take %(requested).2f day(s) of %(leave_type)s.\n\n"
                    "• Monthly accrual rate: %(rate).2f days/month (annual entitlement ÷ 12)\n"
                    "• Annual entitlement: %(annual).2f days\n"
                    "• Months elapsed (from %(start_month)s): %(months)d\n"
                    "• Accrued balance: %(accrued).2f days\n"
                    "• Already taken/pending: %(taken).2f days\n"
                    "• Available: %(available).2f days",
                    employee=leave.employee_id.name,
                    requested=requested,
                    leave_type=leave_type.name,
                     rate=round(monthly_rate, 2),
                     annual=round(annual_entitlement, 2),
                     start_month=date(today.year, start_month, 1).strftime('%B %Y'),
                     months=months_elapsed,
                     accrued=round(accrued_balance, 2),
                     taken=round(total_taken, 2),
                     available=round(available, 2),
                ))

            _logger.info(
                "Monthly accrual check passed for %s: %.2f requested, %.2f available, %.2f rate",
                leave.employee_id.name, requested, available, monthly_rate,
            )
