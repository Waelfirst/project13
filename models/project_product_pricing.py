# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProjectProductPricing(models.Model):
    """Main pricing model"""
    _name = 'project.product.pricing'
    _description = 'Project Product Pricing'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string='Pricing Code',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        tracking=True
    )
    pricing_date = fields.Date(
        string='Pricing Date',
        required=True,
        default=fields.Date.context_today,
        tracking=True
    )
    version = fields.Integer(
        string='Version',
        default=1,
        tracking=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        domain=[('customer_rank', '>', 0)],
        tracking=True
    )
    project_id = fields.Many2one(
        'project.definition',
        string='Project',
        required=True,
        tracking=True
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        tracking=True
    )
    quantity = fields.Float(
        string='Product Quantity',
        digits='Product Unit of Measure',
        compute='_compute_product_data',
        store=True,
        readonly=False
    )
    weight = fields.Float(
        string='Product Weight',
        digits='Stock Weight',
        compute='_compute_product_data',
        store=True,
        readonly=False
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('approved', 'Approved'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    component_line_ids = fields.One2many(
        'project.product.component',
        'pricing_id',
        string='Component Lines'
    )

    total_component_cost = fields.Float(
        string='Total Component Cost',
        compute='_compute_total_cost',
        store=True
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )

    notes = fields.Text(string='Notes')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('project.product.pricing') or _('New')
        return super(ProjectProductPricing, self).create(vals)

    @api.depends('component_line_ids.total_cost')
    def _compute_total_cost(self):
        for record in self:
            record.total_component_cost = sum(record.component_line_ids.mapped('total_cost'))

    @api.depends('project_id', 'product_id')
    def _compute_product_data(self):
        for record in self:
            if record.product_id and record.project_id:
                product_line = record.project_id.product_line_ids.filtered(
                    lambda l: l.product_id == record.product_id
                )
                if product_line:
                    record.quantity = product_line[0].quantity
                    record.weight = product_line[0].weight
                else:
                    record.quantity = 0.0
                    record.weight = 0.0
            else:
                record.quantity = 0.0
                record.weight = 0.0

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        # Filter projects by customer
        if self.partner_id:
            return {'domain': {'project_id': [('partner_id', '=', self.partner_id.id)]}}
        return {'domain': {'project_id': []}}

    @api.onchange('project_id')
    def _onchange_project_id(self):
        # Filter products by project
        self.product_id = False
        if self.project_id:
            product_ids = self.project_id.product_line_ids.mapped('product_id').ids
            return {'domain': {'product_id': [('id', 'in', product_ids)]}}
        return {'domain': {'product_id': []}}

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_create_new_version(self):
        """Create a new version of this pricing"""
        self.ensure_one()

        # Get max version for this project and product
        max_version = self.search([
            ('project_id', '=', self.project_id.id),
            ('product_id', '=', self.product_id.id),
        ], order='version desc', limit=1).version

        # Copy with new version
        new_pricing = self.copy({
            'version': max_version + 1,
            'state': 'draft',
            'pricing_date': fields.Date.context_today(self),
        })

        return {
            'type': 'ir.actions.act_window',
            'name': _('New Pricing Version'),
            'res_model': 'project.product.pricing',
            'view_mode': 'form',
            'res_id': new_pricing.id,
            'target': 'current',
        }

    def action_import_components_excel(self):
        """Open wizard to import components from Excel"""
        self.ensure_one()

        wizard = self.env['import.components.wizard'].create({
            'pricing_id': self.id,
            'product_id': self.product_id.id,
        })

        return {
            'type': 'ir.actions.act_window',
            'name': _('Import Components from Excel'),
            'res_model': 'import.components.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_import_components_only(self):
        """Open wizard to import components only - Step 1"""
        self.ensure_one()

        wizard = self.env['import.components.only.wizard'].create({
            'pricing_id': self.id,
        })

        return {
            'type': 'ir.actions.act_window',
            'name': _('Import Components - Step 1'),
            'res_model': 'import.components.only.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_import_bom_materials(self):
        """Open wizard to import BOM materials - Step 2"""
        self.ensure_one()

        wizard = self.env['import.bom.materials.wizard'].create({
            'pricing_id': self.id,
        })

        return {
            'type': 'ir.actions.act_window',
            'name': _('Import BOM Materials - Step 2'),
            'res_model': 'import.bom.materials.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_import_bom_operations(self):
        """Open wizard to import BOM operations - Step 3"""
        self.ensure_one()

        wizard = self.env['import.bom.operations.wizard'].create({
            'pricing_id': self.id,
        })

        return {
            'type': 'ir.actions.act_window',
            'name': _('Import BOM Operations - Step 3'),
            'res_model': 'import.bom.operations.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }


class ProjectProductComponent(models.Model):
    _name = 'project.product.component'
    _description = 'Project Product Component'
    _order = 'sequence, id'

    sequence = fields.Integer(string='Sequence', default=10)
    pricing_id = fields.Many2one(
        'project.product.pricing',
        string='Pricing',
        required=True,
        ondelete='cascade'
    )
    component_id = fields.Many2one(
        'product.product',
        string='Component Product',
        required=True,
        domain=[('type', 'in', ['product', 'consu'])]
    )
    quantity = fields.Float(
        string='Quantity',
        required=True,
        default=1.0,
        digits='Product Unit of Measure'
    )
    weight = fields.Float(
        string='Weight',
        digits='Stock Weight'
    )
    cost_price = fields.Float(
        string='Cost Price',
        required=True,
        digits='Product Price'
    )
    uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of Measure',
        related='component_id.uom_id',
        readonly=True
    )
    total_cost = fields.Float(
        string='Total Cost',
        compute='_compute_total_cost',
        store=True,
        digits='Product Price'
    )
    bom_id = fields.Many2one(
        'mrp.bom',
        string='Bill of Materials'
    )
    specification_ids = fields.One2many(
        'component.specification.value',
        'pricing_component_id',
        string='Specifications'
    )
    spec_count = fields.Integer(
        string='Specifications',
        compute='_compute_spec_count'
    )

    # Additional Code field - shows all specifications as formatted text
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

    @api.depends('quantity', 'cost_price')
    def _compute_total_cost(self):
        for line in self:
            line.total_cost = line.quantity * line.cost_price

    @api.onchange('component_id')
    def _onchange_component_id(self):
        if self.component_id:
            self.cost_price = self.component_id.standard_price
            self.weight = self.component_id.weight
            # Try to find existing BOM
            bom = self.env['mrp.bom'].search([
                ('product_id', '=', self.component_id.id)
            ], limit=1)
            if bom:
                self.bom_id = bom.id

    def action_view_bom(self):
        self.ensure_one()
        if not self.bom_id:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Create Bill of Materials',
                'res_model': 'mrp.bom',
                'view_mode': 'form',
                'context': {
                    'default_product_id': self.component_id.id,
                    'default_product_tmpl_id': self.component_id.product_tmpl_id.id,
                },
                'target': 'new',
            }
        return {
            'type': 'ir.actions.act_window',
            'name': 'Bill of Materials',
            'res_model': 'mrp.bom',
            'view_mode': 'form',
            'res_id': self.bom_id.id,
            'target': 'current',
        }

    def action_create_bom(self):
        self.ensure_one()
        bom = self.env['mrp.bom'].create({
            'product_id': self.component_id.id,
            'product_tmpl_id': self.component_id.product_tmpl_id.id,
            'product_qty': 1.0,
            'type': 'normal',
        })
        self.bom_id = bom.id
        return self.action_view_bom()

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
                'source_model': 'project.product.component',
                'source_id': self.id,
                'component_id': self.component_id.id,
            }
        }