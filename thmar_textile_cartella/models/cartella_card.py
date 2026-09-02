# -*- coding: utf-8 -*-
from odoo import models, fields, api


class CartellaCard(models.Model):
    """الكارتيلات - Textile Cartella Card (Core Model)"""
    _name = 'cartella.card'
    _description = 'الكارتيلات'
    _rec_name = 'sequence_number'
    _order = 'sequence_number desc'

    # ─── Primary Fields ────────────────────────────────────────────────────────

    raw_material_detail = fields.Char(
        string='اسم المنتج الخام بالتفصيل',
    )
    finished_product_id = fields.Many2one(
        comodel_name='cartella.finished.product',
        string='اسم المنتج التام',
        required=True,
        ondelete='restrict',
    )
    blend_ratio_id = fields.Many2one(
        comodel_name='cartella.blend.ratio',
        string='نسب الخلط',
        ondelete='set null',
    )

    # ─── Finished Product Specifications ───────────────────────────────────────

    finished_weight = fields.Float(
        string='وزن المنتج التام',
        digits=(10, 3),
    )
    finished_width = fields.Float(
        string='عرض المنتج التام',
        digits=(10, 2),
    )

    # ─── Raw Material Specifications ───────────────────────────────────────────

    raw_weight = fields.Float(
        string='وزن المنتج الخام',
        digits=(10, 3),
    )
    raw_width = fields.Float(
        string='عرض المنتج الخام',
        digits=(10, 2),
    )
    yarn_count = fields.Char(
        string='نمرة الخيط',
    )

    # ─── Reference / Code ──────────────────────────────────────────────────────

    reference = fields.Char(
        string='المرجع / الكود',
    )
    sequence_number = fields.Char(
        string='رقم تسلسلي',
        readonly=True,
        copy=False,
        default='جديد',
    )

    # ─── Computed Fields ───────────────────────────────────────────────────────

    barcode = fields.Char(
        string='الباركود المولد',
        compute='_compute_barcode',
        store=True,
        index=True,
        copy=False,
    )
    # Non-stored: recomputed on every read - no @api.depends needed since id never changes
    record_url = fields.Char(
        string='رابط السجل',
        compute='_compute_record_url',
        store=False,
    )

    # ─── Compute: Barcode ──────────────────────────────────────────────────────

    @api.depends(
        'finished_product_id',
        'finished_product_id.code',
        'blend_ratio_id',
        'blend_ratio_id.material_id',
        'blend_ratio_id.material_id.category_code',
        'sequence_number',
    )
    def _compute_barcode(self):
        for rec in self:
            parts = []
            # Part 1: Finished Product Code
            if rec.finished_product_id and rec.finished_product_id.code:
                parts.append(rec.finished_product_id.code.strip())
            # Part 2: Material Category Code (from blend ratio)
            if rec.blend_ratio_id and rec.blend_ratio_id.material_id:
                cat_code = rec.blend_ratio_id.material_id.category_code or ''
                if cat_code:
                    parts.append(cat_code.strip())
            # Part 3: Sequence number (skip placeholder)
            seq = rec.sequence_number or ''
            if seq and seq != 'جديد':
                parts.append(seq.strip())

            rec.barcode = '-'.join(parts) if parts else ''

    # ─── Compute: Record URL (absolute URL for QR scanning from mobile) ─────────

    def _compute_record_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url', ''
        ).rstrip('/')
        for rec in self:
            if rec.id:
                rec.record_url = f"{base_url}/cartella/view/{rec.id}"
            else:
                rec.record_url = ''

    # ─── ORM Overrides ─────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('sequence_number') or vals['sequence_number'] == 'جديد':
                vals['sequence_number'] = self.env['ir.sequence'].next_by_code(
                    'cartella.card.sequence'
                ) or 'جديد'
        return super().create(vals_list)

    def _compute_display_name(self):
        """Override display name — replaces deprecated name_get() in Odoo 17+."""
        for rec in self:
            seq = rec.sequence_number or ''
            prod = rec.finished_product_id.name or ''
            if seq and seq != 'جديد' and prod:
                rec.display_name = f"{seq} - {prod}"
            elif prod:
                rec.display_name = prod
            else:
                rec.display_name = seq or str(rec.id)
