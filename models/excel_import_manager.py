# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
import io
import logging

_logger = logging.getLogger(__name__)

try:
    import openpyxl
    from openpyxl import load_workbook, Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
except ImportError:
    _logger.warning('openpyxl library not found')
    openpyxl = None


class ExcelImportManager(models.Model):
    """إدارة رفع بيانات Excel - ثلاث مراحل"""
    _name = 'excel.import.manager'
    _description = 'Excel Import Manager'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string='Import Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        tracking=True
    )

    pricing_id = fields.Many2one(
        'project.product.pricing',
        string='Pricing Reference',
        required=True,
        tracking=True
    )

    partner_id = fields.Many2one(
        related='pricing_id.partner_id',
        string='Customer',
        store=True,
        readonly=True
    )

    project_id = fields.Many2one(
        related='pricing_id.project_id',
        string='Project',
        store=True,
        readonly=True
    )

    product_id = fields.Many2one(
        related='pricing_id.product_id',
        string='Product',
        store=True,
        readonly=True
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('step1_done', 'Step 1: Components Imported'),
        ('step2_done', 'Step 2: Materials Imported'),
        ('step3_done', 'Step 3: Operations Imported'),
        ('completed', 'Completed'),
    ], string='Status', default='draft', tracking=True)

    # Step 1: Components
    step1_file = fields.Binary(string='Step 1: Components File')
    step1_filename = fields.Char(string='Components Filename')
    step1_date = fields.Datetime(string='Step 1 Date', readonly=True)
    step1_components_count = fields.Integer(string='Components Imported', readonly=True)
    step1_products_created = fields.Integer(string='Products Auto-Created', readonly=True)

    # Step 2: Materials
    step2_file = fields.Binary(string='Step 2: Materials File')
    step2_filename = fields.Char(string='Materials Filename')
    step2_date = fields.Datetime(string='Step 2 Date', readonly=True)
    step2_boms_created = fields.Integer(string='BOMs Created', readonly=True)
    step2_materials_created = fields.Integer(string='Materials Auto-Created', readonly=True)

    # Step 3: Operations
    step3_file = fields.Binary(string='Step 3: Operations File')
    step3_filename = fields.Char(string='Operations Filename')
    step3_date = fields.Datetime(string='Step 3 Date', readonly=True)
    step3_routings_created = fields.Integer(string='Routings Created', readonly=True)
    step3_workcenters_created = fields.Integer(string='Workcenters Auto-Created', readonly=True)

    notes = fields.Text(string='Notes')

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('excel.import.manager') or _('New')
        return super(ExcelImportManager, self).create(vals)

    def action_download_step1_template(self):
        """تحميل Template المرحلة الأولى - placeholder for now"""
        raise UserError(_('Template download feature coming soon. Please create Excel file manually for now.'))

    def action_import_step1(self):
        """استيراد المرحلة الأولى - placeholder for now"""
        raise UserError(_('Import feature coming soon.'))

    def action_download_step2_template(self):
        """تحميل Template المرحلة الثانية - placeholder for now"""
        raise UserError(_('Template download feature coming soon.'))

    def action_import_step2(self):
        """استيراد المرحلة الثانية - placeholder for now"""
        raise UserError(_('Import feature coming soon.'))

    def action_download_step3_template(self):
        """تحميل Template المرحلة الثالثة - placeholder for now"""
        raise UserError(_('Template download feature coming soon.'))

    def action_import_step3(self):
        """استيراد المرحلة الثالثة - placeholder for now"""
        raise UserError(_('Import feature coming soon.'))

    def action_reset(self):
        """إعادة تعيين لبدء من جديد"""
        self.ensure_one()
        self.write({
            'state': 'draft',
            'step1_date': False,
            'step1_components_count': 0,
            'step1_products_created': 0,
            'step2_date': False,
            'step2_boms_created': 0,
            'step2_materials_created': 0,
            'step3_date': False,
            'step3_routings_created': 0,
            'step3_workcenters_created': 0,
        })