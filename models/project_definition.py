# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProjectDefinition(models.Model):
    _name = 'project.definition'
    _description = 'Project Definition'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string='Project Code',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        tracking=True
    )
    project_name = fields.Char(
        string='Project Name',
        required=True,
        tracking=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        domain=[('customer_rank', '>', 0)],
        tracking=True
    )
    start_date = fields.Date(
        string='Project Start Date',
        required=True,
        default=fields.Date.context_today,
        tracking=True
    )
    end_date = fields.Date(
        string='Expected End Date',
        required=True,
        tracking=True
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    
    product_line_ids = fields.One2many(
        'project.product.line',
        'project_id',
        string='Project Products'
    )
    
    total_cost = fields.Float(
        string='Total Cost',
        compute='_compute_totals',
        store=True
    )
    total_sale = fields.Float(
        string='Total Sale',
        compute='_compute_totals',
        store=True
    )
    total_profit = fields.Float(
        string='Total Profit',
        compute='_compute_totals',
        store=True
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('project.definition') or _('New')
        return super(ProjectDefinition, self).create(vals)
    
    @api.depends('product_line_ids.cost_price', 'product_line_ids.sale_price', 'product_line_ids.quantity')
    def _compute_totals(self):
        for record in self:
            total_cost = sum(line.cost_price * line.quantity for line in record.product_line_ids)
            total_sale = sum(line.sale_price * line.quantity for line in record.product_line_ids)
            record.total_cost = total_cost
            record.total_sale = total_sale
            record.total_profit = total_sale - total_cost
    
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.end_date and record.start_date and record.end_date < record.start_date:
                raise ValidationError(_('End date cannot be before start date!'))
    
    def action_confirm(self):
        self.write({'state': 'confirmed'})
    
    def action_start(self):
        self.write({'state': 'in_progress'})
    
    def action_done(self):
        self.write({'state': 'done'})
    
    def action_cancel(self):
        self.write({'state': 'cancelled'})
    
    def action_draft(self):
        self.write({'state': 'draft'})


class ProjectProductLine(models.Model):
    _name = 'project.product.line'
    _description = 'Project Product Line'
    _order = 'sequence, id'

    sequence = fields.Integer(string='Sequence', default=10)
    project_id = fields.Many2one(
        'project.definition',
        string='Project',
        required=True,
        ondelete='cascade'
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
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
    sale_price = fields.Float(
        string='Sale Price',
        required=True,
        digits='Product Price'
    )
    uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of Measure',
        related='product_id.uom_id',
        readonly=True
    )
    total_cost = fields.Float(
        string='Total Cost',
        compute='_compute_total',
        store=True,
        digits='Product Price'
    )
    total_sale = fields.Float(
        string='Total Sale',
        compute='_compute_total',
        store=True,
        digits='Product Price'
    )
    profit = fields.Float(
        string='Profit',
        compute='_compute_total',
        store=True,
        digits='Product Price'
    )
    
    @api.depends('quantity', 'cost_price', 'sale_price')
    def _compute_total(self):
        for line in self:
            line.total_cost = line.quantity * line.cost_price
            line.total_sale = line.quantity * line.sale_price
            line.profit = line.total_sale - line.total_cost
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.cost_price = self.product_id.standard_price
            self.sale_price = self.product_id.list_price
            self.weight = self.product_id.weight
