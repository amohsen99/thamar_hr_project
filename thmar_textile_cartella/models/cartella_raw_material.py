# -*- coding: utf-8 -*-
from odoo import models, fields


class CartellaMaterialCategory(models.Model):
    """فئة الخامة - Raw Material Category"""
    _name = 'cartella.material.category'
    _description = 'فئة الخامة'
    _rec_name = 'name'
    _order = 'name'

    name = fields.Char(
        string='اسم الفئة',
        required=True,
    )
    code = fields.Char(
        string='كود الفئة',
        required=True,
    )

    _code_unique = models.Constraint(
        'unique(code)',
        'كود الفئة يجب أن يكون فريداً!',
    )


class CartellaRawMaterial(models.Model):
    """الخامة - Raw Material"""
    _name = 'cartella.raw.material'
    _description = 'الخامة'
    _rec_name = 'name'
    _order = 'name'

    name = fields.Char(
        string='اسم الخامة',
        required=True,
    )
    category_id = fields.Many2one(
        comodel_name='cartella.material.category',
        string='فئة الخامة',
        required=True,
        ondelete='restrict',
    )
    category_code = fields.Char(
        string='كود الفئة',
        related='category_id.code',
        store=True,
        readonly=True,
    )
