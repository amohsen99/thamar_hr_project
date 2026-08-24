# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class HrLeave(models.Model):
    _inherit = 'hr.leave'

    supervisor_id = fields.Many2one('hr.employee', related='employee_id.supervisor_id', string='Supervisor', store=True, readonly=True)
    supervisor_approved = fields.Boolean(string='Supervisor Approved', default=False, copy=False)
    can_supervisor_approve = fields.Boolean(compute='_compute_can_supervisor_approve')

    requires_clinical_approval = fields.Boolean(related='holiday_status_id.requires_clinical_approval', readonly=True)
    clinical_approved = fields.Boolean(string='Clinical Approved', default=False, copy=False)
    can_clinical_approve = fields.Boolean(compute='_compute_can_clinical_approve')

    @api.depends('state', 'supervisor_id', 'supervisor_approved')
    def _compute_can_supervisor_approve(self):
        for leave in self:
            is_supervisor = leave.supervisor_id and leave.supervisor_id.user_id == self.env.user
            leave.can_supervisor_approve = leave.state == 'confirm' and is_supervisor and not leave.supervisor_approved

    @api.depends('state', 'supervisor_id', 'supervisor_approved', 'requires_clinical_approval', 'clinical_approved')
    def _compute_can_clinical_approve(self):
        for leave in self:
            is_clinical_manager = leave.company_id.clinical_manager_id and leave.company_id.clinical_manager_id.user_id == self.env.user
            # Clinical manager can approve if it's in confirm state, requires clinical approval, not yet clinical approved, 
            # and (if there is a supervisor) the supervisor has already approved.
            supervisor_ok = not leave.supervisor_id or leave.supervisor_approved
            leave.can_clinical_approve = leave.state == 'confirm' and leave.requires_clinical_approval and is_clinical_manager and not leave.clinical_approved and supervisor_ok

    def action_supervisor_approve(self):
        for leave in self:
            if not leave.can_supervisor_approve:
                raise UserError(_('You are not authorized to perform this action or the leave is not in the correct state.'))
            leave.write({'supervisor_approved': True})
            leave.message_post(body=_("Supervisor approved the leave request."))
        return True

    def action_supervisor_refuse(self):
        for leave in self:
            if not leave.can_supervisor_approve:
                raise UserError(_('You are not authorized to perform this action or the leave is not in the correct state.'))
            leave.action_refuse()
            leave.message_post(body=_("Supervisor refused the leave request."))
        return True

    def action_clinical_approve(self):
        for leave in self:
            if not leave.can_clinical_approve:
                raise UserError(_('You are not authorized to perform this action or the leave is not in the correct state.'))
            leave.write({'clinical_approved': True})
            leave.message_post(body=_("Clinical Manager approved the ill leave request."))
        return True

    def action_clinical_refuse(self):
        for leave in self:
            if not leave.can_clinical_approve:
                raise UserError(_('You are not authorized to perform this action or the leave is not in the correct state.'))
            leave.action_refuse()
            leave.message_post(body=_("Clinical Manager refused the ill leave request."))
        return True

    @api.depends('state', 'employee_id', 'department_id', 'supervisor_id', 'supervisor_approved', 'requires_clinical_approval', 'clinical_approved')
    def _compute_can_approve(self):
        super()._compute_can_approve()
        for holiday in self:
            if holiday.supervisor_id and not holiday.supervisor_approved:
                holiday.can_approve = False
            if holiday.requires_clinical_approval and holiday.company_id.clinical_manager_id and not holiday.clinical_approved:
                holiday.can_approve = False

    @api.depends('state', 'employee_id', 'department_id', 'supervisor_id', 'supervisor_approved', 'requires_clinical_approval', 'clinical_approved')
    def _compute_can_validate(self):
        super()._compute_can_validate()
        for holiday in self:
            if holiday.supervisor_id and not holiday.supervisor_approved:
                holiday.can_validate = False
            if holiday.requires_clinical_approval and holiday.company_id.clinical_manager_id and not holiday.clinical_approved:
                holiday.can_validate = False
