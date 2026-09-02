# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    is_annual_leave = fields.Boolean(
        string='Is Annual Leave (إجازة اعتيادية)',
        default=False,
        help="Mark this leave type as the Annual Leave type. "
             "Used by the auto-allocation system to identify the correct leave type.",
    )
    is_casual_leave = fields.Boolean(
        string='Is Casual Leave (إجازة عارضة)',
        default=False,
        help="Mark this leave type as the Casual Leave type. "
             "Used by the auto-allocation system to identify the correct leave type.",
    )
    use_monthly_accrual = fields.Boolean(
        string='Monthly Accrual Policy (سياسة الاستحقاق الشهري)',
        default=False,
        help="If enabled, the annual leave balance accrues monthly at "
             "(Total Days / 12) per month. Employees cannot take more "
             "than their accrued balance up to the leave request month. "
             "Unused accrued days roll over automatically within the year.",
    )

    @api.constrains('is_annual_leave')
    def _check_single_annual_leave(self):
        """Ensure only one leave type is marked as Annual Leave per company."""
        for leave_type in self:
            if leave_type.is_annual_leave:
                domain = [
                    ('is_annual_leave', '=', True),
                    ('id', '!=', leave_type.id),
                ]
                if leave_type.company_id:
                    domain.append(('company_id', '=', leave_type.company_id.id))
                else:
                    domain.append(('company_id', '=', False))
                existing = self.search_count(domain)
                if existing:
                    raise ValidationError(_(
                        "Only one leave type can be marked as Annual Leave per company."
                    ))

    @api.constrains('is_casual_leave')
    def _check_single_casual_leave(self):
        """Ensure only one leave type is marked as Casual Leave per company."""
        for leave_type in self:
            if leave_type.is_casual_leave:
                domain = [
                    ('is_casual_leave', '=', True),
                    ('id', '!=', leave_type.id),
                ]
                if leave_type.company_id:
                    domain.append(('company_id', '=', leave_type.company_id.id))
                else:
                    domain.append(('company_id', '=', False))
                existing = self.search_count(domain)
                if existing:
                    raise ValidationError(_(
                        "Only one leave type can be marked as Casual Leave per company."
                    ))
