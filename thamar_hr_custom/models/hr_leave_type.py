# -*- coding: utf-8 -*-
from odoo import fields, models

class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    requires_clinical_approval = fields.Boolean(string='Requires Clinical Approval', default=False, help="If checked, leaves of this type will require approval from the company's Clinical Manager.")
