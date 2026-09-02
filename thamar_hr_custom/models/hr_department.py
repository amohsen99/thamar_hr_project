# -*- coding: utf-8 -*-
from odoo import fields, models, api


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    supervisor_id = fields.Many2one('hr.employee', string='Department Supervisor', help="The supervisor responsible for initial time off approvals within the department.")

    def write(self, vals):
        res = super().write(vals)
        if 'supervisor_id' in vals:
            supervisor_group = self.env.ref('thamar_hr_custom.group_hr_holidays_department_supervisor')
            time_off_groups = [
                self.env.ref('hr_holidays.group_hr_holidays_user', raise_if_not_found=False),
                self.env.ref('hr_holidays.group_hr_holidays_manager', raise_if_not_found=False),
                self.env.ref('hr_holidays.group_hr_holidays_responsible', raise_if_not_found=False),
            ]
            time_off_groups = [g for g in time_off_groups if g]
            for department in self:
                old_supervisor = department._origin.supervisor_id
                new_supervisor = department.supervisor_id
                if old_supervisor and old_supervisor.user_id:
                    old_supervisor.user_id.write({'groups_id': [(3, supervisor_group.id)]})
                    if time_off_groups:
                        old_supervisor.user_id.write({'groups_id': [(3, g.id) for g in time_off_groups]})
                if new_supervisor and new_supervisor.user_id:
                    new_supervisor.user_id.write({'groups_id': [(4, supervisor_group.id)]})
                    if time_off_groups:
                        new_supervisor.user_id.write({'groups_id': [(3, g.id) for g in time_off_groups]})
        if 'manager_id' in vals:
            manager_group = self.env.ref('thamar_hr_custom.group_hr_holidays_department_manager')
            time_off_groups = [
                self.env.ref('hr_holidays.group_hr_holidays_user', raise_if_not_found=False),
                self.env.ref('hr_holidays.group_hr_holidays_manager', raise_if_not_found=False),
                self.env.ref('hr_holidays.group_hr_holidays_responsible', raise_if_not_found=False),
            ]
            time_off_groups = [g for g in time_off_groups if g]
            for department in self:
                old_manager = department._origin.manager_id
                new_manager = department.manager_id
                if old_manager and old_manager.user_id:
                    old_manager.user_id.write({'groups_id': [(3, manager_group.id)]})
                    if time_off_groups:
                        old_manager.user_id.write({'groups_id': [(3, g.id) for g in time_off_groups]})
                if new_manager and new_manager.user_id:
                    new_manager.user_id.write({'groups_id': [(4, manager_group.id)]})
                    if time_off_groups:
                        new_manager.user_id.write({'groups_id': [(3, g.id) for g in time_off_groups]})
        return res
