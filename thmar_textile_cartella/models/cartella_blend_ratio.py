# -*- coding: utf-8 -*-
from odoo import models, fields, api


class CartellaBlendRatio(models.Model):
    """نسب الخلط - Blend Ratio"""
    _name = 'cartella.blend.ratio'
    _description = 'نسب الخلط'
    _rec_name = 'name'
    _order = 'material_id'

    name = fields.Char(
        string='اسم نسبة الخلط',
        compute='_compute_name',
        store=True,
    )
    material_id = fields.Many2one(
        comodel_name='cartella.raw.material',
        string='الخامة',
        required=True,
        ondelete='restrict',
    )

    @api.depends('material_id', 'material_id.name')
    def _compute_name(self):
        for rec in self:
            if rec.material_id:
                rec.name = rec.material_id.name
            else:
                rec.name = ''
