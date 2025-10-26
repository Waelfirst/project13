# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class MaterialPlanningComponent(models.Model):
    _name = 'material.planning.component'
    _description = 'Material Planning Component'
    _order = 'sequence, id'

    sequence = fields.Integer(string='Sequence', default=10)
    planning_id = fields.Many2one(
        'material.production.planning',
        string='Planning',
        required=True,
        ondelete='cascade'
    )
    component_id = fields.Many2one(
        'product.product',
        string='Component Product',
        required=True
    )
    quantity = fields.Float(
        string='Quantity',
        required=True,
        digits='Product Unit of Measure'
    )
    weight = fields.Float(
        string='Weight',
        digits='Stock Weight'
    )
    cost_price = fields.Float(
        string='Cost Price',
        digits='Product Price'
    )
    bom_id = fields.Many2one(
        'mrp.bom',
        string='Bill of Materials'
    )
    specification_ids = fields.One2many(
        'component.specification.value',
        'planning_component_id',
        string='Specifications'
    )
    spec_count = fields.Integer(
        string='Specifications',
        compute='_compute_spec_count'
    )
    uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of Measure',
        related='component_id.uom_id',
        readonly=True
    )
    
    # NEW: Additional Code field
    additional_code = fields.Text(
        string='Additional Code / Specifications',
        compute='_compute_additional_code',
        store=True,
        help='Component specifications formatted as code'
    )
    
    @api.depends('specification_ids', 'specification_ids.value', 'specification_ids.specification_name')
    def _compute_additional_code(self):
        """Compute additional code from specifications"""
        for record in self:
            if record.specification_ids:
                specs = []
                for spec in record.specification_ids.sorted('sequence'):
                    if spec.value:
                        specs.append('%s: %s' % (spec.specification_name, spec.value))
                record.additional_code = '\n'.join(specs) if specs else ''
            else:
                record.additional_code = ''
    
    @api.depends('specification_ids')
    def _compute_spec_count(self):
        for record in self:
            record.spec_count = len(record.specification_ids)
    
    def action_component_specifications(self):
        """Open specifications wizard"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Component Specifications: %s') % self.component_id.name,
            'res_model': 'component.specification.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_component_id': self.component_id.id,
                'source_model': 'material.planning.component',
                'source_id': self.id,
                'component_id': self.component_id.id,
            }
        }
