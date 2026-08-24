# -*- coding: utf-8 -*-
from odoo import fields, models

class ResCompany(models.Model):
    _inherit = 'res.company'

    clinical_manager_id = fields.Many2one('hr.employee', string='Clinical Manager')
