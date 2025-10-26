# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class WorkOrderExecution(models.Model):
    _name = 'work.order.execution'
    _description = 'Work Order Execution'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string='Execution Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
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
    state = fields.Selection([
        ('draft', 'Draft'),
        ('loaded', 'Work Orders Loaded'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    work_order_line_ids = fields.One2many(
        'work.order.execution.line',
        'execution_id',
        string='Work Order Lines'
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )

    notes = fields.Text(string='Notes')

    total_components = fields.Integer(
        string='Total Components',
        compute='_compute_totals',
        store=True
    )
    completed_components = fields.Integer(
        string='Completed Components',
        compute='_compute_totals',
        store=True
    )
    in_progress_components = fields.Integer(
        string='In Progress',
        compute='_compute_totals',
        store=True
    )

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('work.order.execution') or _('New')
        return super(WorkOrderExecution, self).create(vals)

    @api.depends('work_order_line_ids.production_state')
    def _compute_totals(self):
        for record in self:
            record.total_components = len(record.work_order_line_ids)
            record.completed_components = len(record.work_order_line_ids.filtered(
                lambda l: l.production_state == 'done'
            ))
            record.in_progress_components = len(record.work_order_line_ids.filtered(
                lambda l: l.production_state in ('confirmed', 'progress', 'to_close')
            ))

    @api.onchange('project_id')
    def _onchange_project_id(self):
        self.product_id = False
        if self.project_id:
            product_ids = self.project_id.product_line_ids.mapped('product_id').ids
            return {'domain': {'product_id': [('id', 'in', product_ids)]}}
        return {'domain': {'product_id': []}}

    def action_load_work_orders(self):
        self.ensure_one()

        if not self.product_id or not self.project_id:
            raise UserError(_('Please select Project and Product first!'))

        # Clear existing lines
        self.work_order_line_ids.unlink()

        # Find material planning for this project and product
        planning = self.env['material.production.planning'].search([
            ('project_id', '=', self.project_id.id),
            ('product_id', '=', self.product_id.id),
            ('state', 'in', ['work_orders_created', 'done'])
        ], limit=1, order='create_date desc')

        if not planning:
            draft_planning = self.env['material.production.planning'].search([
                ('project_id', '=', self.project_id.id),
                ('product_id', '=', self.product_id.id),
            ], limit=1, order='create_date desc')

            if draft_planning:
                raise UserError(_(
                    'Material Planning exists but no work orders created yet!\n\n'
                    'Planning: %s\n'
                    'State: %s\n\n'
                    'Please go to Material Planning and create work orders first'
                ) % (draft_planning.name, dict(draft_planning._fields['state'].selection).get(draft_planning.state)))
            else:
                raise UserError(_(
                    'No Material Planning found for this project and product!\n\n'
                    'Please create a Material Planning first'
                ))

        if not planning.production_order_ids:
            raise UserError(_('Material Planning exists but no production orders found!'))

        # Get pricing reference to fetch additional code and specifications
        pricing = self.env['project.product.pricing'].search([
            ('project_id', '=', self.project_id.id),
            ('product_id', '=', self.product_id.id),
            ('state', 'in', ['confirmed', 'approved'])
        ], limit=1, order='create_date desc')

        # Get all production orders from planning
        productions = planning.production_order_ids

        # Create lines for each production order
        total_operations = 0
        for production in productions:
            # Confirm production if in draft state
            if production.state == 'draft':
                production.action_confirm()

            # Create workorders if they don't exist
            if not production.workorder_ids and production.state in ('confirmed', 'progress'):
                try:
                    production._create_workorder()
                    _logger.info('Created workorders for production %s', production.name)
                except Exception as e:
                    _logger.warning('Could not create workorders for %s: %s', production.name, str(e))

            # Get additional code and specifications from pricing
            additional_code = ''
            specification_ids = []

            if pricing:
                pricing_component = pricing.component_line_ids.filtered(
                    lambda c: c.component_id == production.product_id
                )
                if pricing_component:
                    additional_code = pricing_component[0].additional_code or ''
                    specification_ids = pricing_component[0].specification_ids.ids

            # Create execution line
            line = self.env['work.order.execution.line'].create({
                'execution_id': self.id,
                'component_id': production.product_id.id,
                'quantity': production.product_qty,
                'weight': production.product_id.weight * production.product_qty,
                'production_id': production.id,
                'additional_code': additional_code,
            })

            # Create operation lines for each workorder
            ops_created = self._load_operations_for_line(line, specification_ids)
            total_operations += ops_created

        self.state = 'loaded'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('%s work orders loaded with %s operations!') % (len(productions), total_operations),
                'type': 'success',
                'sticky': False,
            }
        }

    def _load_operations_for_line(self, execution_line, specification_ids):
        """Load operations for a production order into operation lines"""
        if not execution_line.production_id.workorder_ids:
            _logger.warning('No workorders found for production %s', execution_line.production_id.name)
            return 0

        operation_vals = []
        sequence = 10
        for workorder in execution_line.production_id.workorder_ids.sorted(lambda w: w.id):
            # Get operation name
            op_name = workorder.name
            if not op_name and workorder.operation_id:
                op_name = workorder.operation_id.name
            if not op_name:
                op_name = 'Operation %s' % workorder.id

            operation_vals.append({
                'execution_line_id': execution_line.id,
                'workorder_id': workorder.id,
                'name': op_name,
                'workcenter_id': workorder.workcenter_id.id if workorder.workcenter_id else False,
                'duration_expected': workorder.duration_expected or 0.0,
                'sequence': sequence,
                'additional_code': execution_line.additional_code,
                'specification_ids': [(6, 0, specification_ids)],
            })
            sequence += 10

        # Create operation lines
        if operation_vals:
            self.env['work.order.operation.line'].create(operation_vals)
            _logger.info('Created %d operation lines for %s', len(operation_vals), execution_line.component_id.name)
            return len(operation_vals)

        return 0

    def action_start_selected(self):
        """Start selected work orders"""
        selected_lines = self.work_order_line_ids.filtered(lambda l: l.selected)

        if not selected_lines:
            raise UserError(_('Please select at least one work order to start!'))

        for line in selected_lines:
            line.action_start_production()

        self.state = 'in_progress'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('%s work orders started!') % len(selected_lines),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_done(self):
        self.write({'state': 'done'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_export_operations_excel(self):
        """Export operations tracking to Excel - EXISTING METHOD"""
        self.ensure_one()

        if not self.work_order_line_ids:
            raise UserError(_('No work orders loaded yet!'))

        all_operations = self.env['work.order.operation.line'].search([
            ('execution_id', '=', self.id)
        ])

        if not all_operations:
            raise UserError(_('No operations found!'))

        # Prepare data with additional code and specifications
        operations_data = []
        for op_line in all_operations:
            # Get specification values as text
            spec_text = ''
            if op_line.specification_ids:
                specs = []
                for spec in op_line.specification_ids.sorted('sequence'):
                    specs.append('%s: %s' % (spec.specification_name, spec.value))
                spec_text = ' | '.join(specs)

            operations_data.append({
                'production_order': op_line.production_id.name if op_line.production_id else '',
                'component': op_line.component_id.display_name if op_line.component_id else '',
                'quantity': op_line.execution_line_id.quantity if op_line.execution_line_id else 0,
                'additional_code': op_line.additional_code or '',
                'specifications': spec_text,
                'operation': op_line.name or '',
                'workcenter': op_line.workcenter_id.name if op_line.workcenter_id else '',
                'state': dict(self.env['mrp.workorder']._fields['state'].selection).get(op_line.state,
                                                                                        op_line.state or 'pending'),
                'qty_to_produce': op_line.qty_production or 0,
                'qty_produced': op_line.qty_produced or 0,
                'progress': op_line.progress_percentage or 0,
                'expected_duration': op_line.duration_expected or 0,
                'real_duration': op_line.duration_real or 0,
                'actual_duration': op_line.actual_duration or 0,
                'workers_assigned': op_line.workers_assigned or 0,
                'machines_assigned': op_line.machines_assigned or 0,
                'start_date': op_line.date_start.strftime('%Y-%m-%d %H:%M') if op_line.date_start else '',
                'finish_date': op_line.date_finished.strftime('%Y-%m-%d %H:%M') if op_line.date_finished else '',
            })

        if not operations_data:
            raise UserError(_('No operation data to export!'))

        # Create workbook
        try:
            import xlsxwriter
            import io
            import base64

            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            worksheet = workbook.add_worksheet('Operations Tracking')

            # Formats
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#4CAF50',
                'font_color': 'white',
                'border': 1,
                'align': 'center',
                'valign': 'vcenter'
            })

            cell_format = workbook.add_format({
                'border': 1,
                'align': 'left',
                'valign': 'vcenter'
            })

            number_format = workbook.add_format({
                'border': 1,
                'align': 'right',
                'num_format': '0.00'
            })

            percent_format = workbook.add_format({
                'border': 1,
                'align': 'right',
                'num_format': '0.00"%"'
            })

            # Status colors
            status_formats = {
                'Done': workbook.add_format({'border': 1, 'bg_color': '#C8E6C9', 'align': 'center'}),
                'In Progress': workbook.add_format({'border': 1, 'bg_color': '#FFF9C4', 'align': 'center'}),
                'Progress': workbook.add_format({'border': 1, 'bg_color': '#FFF9C4', 'align': 'center'}),
                'Ready': workbook.add_format({'border': 1, 'bg_color': '#B3E5FC', 'align': 'center'}),
                'Pending': workbook.add_format({'border': 1, 'bg_color': '#F5F5F5', 'align': 'center'}),
                'Waiting': workbook.add_format({'border': 1, 'bg_color': '#F5F5F5', 'align': 'center'}),
                'Cancelled': workbook.add_format({'border': 1, 'bg_color': '#FFCDD2', 'align': 'center'}),
                'Cancel': workbook.add_format({'border': 1, 'bg_color': '#FFCDD2', 'align': 'center'}),
            }

            # Headers
            headers = [
                'Production Order', 'Component', 'Quantity', 'Additional Code', 'Specifications',
                'Operation', 'Work Center', 'State', 'Qty to Produce', 'Qty Produced',
                'Progress %', 'Expected Duration (min)', 'Real Duration (min)', 'Actual Duration (min)',
                'Workers Assigned', 'Machines Assigned', 'Start Date', 'Finish Date'
            ]

            for col, header in enumerate(headers):
                worksheet.write(0, col, header, header_format)

            # Data
            row = 1
            for data in operations_data:
                worksheet.write(row, 0, data['production_order'], cell_format)
                worksheet.write(row, 1, data['component'], cell_format)
                worksheet.write(row, 2, data['quantity'], number_format)
                worksheet.write(row, 3, data['additional_code'], cell_format)
                worksheet.write(row, 4, data['specifications'], cell_format)
                worksheet.write(row, 5, data['operation'], cell_format)
                worksheet.write(row, 6, data['workcenter'], cell_format)

                status = data['state']
                status_fmt = status_formats.get(status, cell_format)
                worksheet.write(row, 7, status, status_fmt)

                worksheet.write(row, 8, data['qty_to_produce'], number_format)
                worksheet.write(row, 9, data['qty_produced'], number_format)
                worksheet.write(row, 10, data['progress'], percent_format)
                worksheet.write(row, 11, data['expected_duration'], number_format)
                worksheet.write(row, 12, data['real_duration'], number_format)
                worksheet.write(row, 13, data['actual_duration'], number_format)
                worksheet.write(row, 14, data['workers_assigned'], number_format)
                worksheet.write(row, 15, data['machines_assigned'], number_format)
                worksheet.write(row, 16, data['start_date'], cell_format)
                worksheet.write(row, 17, data['finish_date'], cell_format)

                row += 1

            # Column widths
            worksheet.set_column('A:A', 20)
            worksheet.set_column('B:B', 25)
            worksheet.set_column('C:C', 10)
            worksheet.set_column('D:D', 30)
            worksheet.set_column('E:E', 40)
            worksheet.set_column('F:F', 20)
            worksheet.set_column('G:G', 15)
            worksheet.set_column('H:H', 15)
            worksheet.set_column('I:J', 12)
            worksheet.set_column('K:K', 12)
            worksheet.set_column('L:P', 15)
            worksheet.set_column('Q:R', 18)

            workbook.close()
            output.seek(0)

            # Create attachment
            file_data = base64.b64encode(output.read())
            filename = 'Operations_Tracking_%s.xlsx' % self.name.replace('/', '_')

            attachment = self.env['ir.attachment'].create({
                'name': filename,
                'datas': file_data,
                'res_model': self._name,
                'res_id': self.id,
                'type': 'binary',
            })

            return {
                'type': 'ir.actions.act_url',
                'url': '/web/content/%s?download=true' % attachment.id,
                'target': 'new',
            }

        except ImportError:
            raise UserError(_('Please install xlsxwriter library: pip install xlsxwriter'))
        except Exception as e:
            raise UserError(_('Error creating Excel file: %s') % str(e))

    def action_open_operations_view(self):
        """Open operations view with additional code and specifications"""
        self.ensure_one()

        total_ops = self.env['work.order.operation.line'].search_count([
            ('execution_id', '=', self.id),
        ])

        if total_ops == 0:
            raise UserError(_('No operations found!'))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Work Order Operations'),
            'res_model': 'work.order.operation.line',
            'view_mode': 'tree,form',
            'domain': [
                ('execution_id', '=', self.id),
            ],
            'context': {
                'default_execution_id': self.id,
                'search_default_filter_not_completed': 1,
                'search_default_group_by_project': 1,
            },
            'target': 'current',
        }

    def action_open_production_report(self):
        """Open production progress report"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Production Progress Report'),
            'res_model': 'production.progress.report',
            'view_mode': 'pivot,graph,tree',
            'context': {
                'search_default_project_id': self.project_id.id,
                'search_default_product_id': self.product_id.id,
            },
            'target': 'current',
        }


class WorkOrderExecutionLine(models.Model):
    _name = 'work.order.execution.line'
    _description = 'Work Order Execution Line'
    _order = 'sequence, id'

    sequence = fields.Integer(string='Sequence', default=10)
    execution_id = fields.Many2one(
        'work.order.execution',
        string='Execution',
        required=True,
        ondelete='cascade'
    )
    selected = fields.Boolean(
        string='Select',
        help='Select this line to execute'
    )
    component_id = fields.Many2one(
        'product.product',
        string='Component',
        required=True
    )
    quantity = fields.Float(
        string='Quantity',
        digits='Product Unit of Measure'
    )
    weight = fields.Float(
        string='Weight',
        digits='Stock Weight'
    )
    production_id = fields.Many2one(
        'mrp.production',
        string='Production Order',
        required=True
    )
    production_state = fields.Selection(
        related='production_id.state',
        string='Production State',
        store=True
    )

    # NEW: Additional Code field
    additional_code = fields.Text(
        string='Additional Code',
        help='Component specifications from pricing'
    )

    operation_line_ids = fields.One2many(
        'work.order.operation.line',
        'execution_line_id',
        string='Operations'
    )

    current_operation = fields.Char(
        string='Current Operation',
        compute='_compute_current_operation'
    )
    progress_percentage = fields.Float(
        string='Progress %',
        compute='_compute_progress'
    )

    @api.depends('production_id', 'production_id.workorder_ids', 'production_id.workorder_ids.state')
    def _compute_current_operation(self):
        for line in self:
            if line.production_id and line.production_id.workorder_ids:
                current_wo = line.production_id.workorder_ids.filtered(
                    lambda w: w.state in ('ready', 'progress')
                )
                if current_wo:
                    line.current_operation = current_wo[0].name
                else:
                    done_count = len(line.production_id.workorder_ids.filtered(lambda w: w.state == 'done'))
                    total_count = len(line.production_id.workorder_ids)
                    if done_count == total_count:
                        line.current_operation = _('All Operations Complete')
                    else:
                        line.current_operation = _('Not Started')
            else:
                line.current_operation = _('No Operations')

    @api.depends('production_id', 'production_id.workorder_ids.state')
    def _compute_progress(self):
        for line in self:
            if line.production_id and line.production_id.workorder_ids:
                total = len(line.production_id.workorder_ids)
                done = len(line.production_id.workorder_ids.filtered(
                    lambda w: w.state == 'done'
                ))
                line.progress_percentage = (done / total * 100) if total > 0 else 0
            else:
                line.progress_percentage = 0

    def action_start_production(self):
        """Start production order"""
        self.ensure_one()

        if self.production_id.state == 'draft':
            self.production_id.action_confirm()

        if self.production_id.state == 'confirmed':
            self.production_id.action_assign()

            if self.production_id.workorder_ids:
                first_wo = self.production_id.workorder_ids.filtered(
                    lambda w: w.state in ('pending', 'ready', 'waiting')
                )
                if first_wo:
                    first_wo[0].button_start()

    def action_next_operation(self):
        """Move to next operation"""
        self.ensure_one()

        if not self.production_id.workorder_ids:
            raise UserError(_('No work orders found for this production!'))

        current_wo = self.production_id.workorder_ids.filtered(
            lambda w: w.state == 'progress'
        )

        if current_wo:
            current_wo[0].button_finish()

            next_wo = self.production_id.workorder_ids.filtered(
                lambda w: w.state in ('ready', 'waiting')
            )
            if next_wo:
                next_wo[0].button_start()
        else:
            raise UserError(_('No work order in progress!'))

    def action_view_production(self):
        """View production order"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Production Order'),
            'res_model': 'mrp.production',
            'view_mode': 'form',
            'res_id': self.production_id.id,
            'target': 'current',
        }


class WorkOrderOperationLine(models.Model):
    _name = 'work.order.operation.line'
    _description = 'Work Order Operation Line'
    _order = 'sequence, id'

    sequence = fields.Integer(string='Sequence', default=10)
    execution_line_id = fields.Many2one(
        'work.order.execution.line',
        string='Execution Line',
        required=True,
        ondelete='cascade'
    )

    # CHANGED: Use computed fields instead of related fields
    execution_id = fields.Many2one(
        'work.order.execution',
        string='Execution',
        compute='_compute_execution_relations',
        store=True,
        readonly=True,
        index=True
    )

    project_id = fields.Many2one(
        'project.definition',
        string='Project',
        compute='_compute_execution_relations',
        store=True,
        readonly=True,
        index=True
    )

    product_id = fields.Many2one(
        'product.product',
        string='Product',
        compute='_compute_execution_relations',
        store=True,
        readonly=True,
        index=True
    )

    component_id = fields.Many2one(
        'product.product',
        string='Component',
        compute='_compute_execution_relations',
        store=True,
        readonly=True
    )

    production_id = fields.Many2one(
        'mrp.production',
        string='Production Order',
        compute='_compute_execution_relations',
        store=True,
        readonly=True,
        index=True
    )

    @api.depends('execution_line_id', 'execution_line_id.execution_id',
                 'execution_line_id.execution_id.project_id',
                 'execution_line_id.execution_id.product_id',
                 'execution_line_id.component_id',
                 'execution_line_id.production_id')
    def _compute_execution_relations(self):
        """Compute all related fields from execution_line_id"""
        for record in self:
            if record.execution_line_id:
                record.execution_id = record.execution_line_id.execution_id
                record.component_id = record.execution_line_id.component_id
                record.production_id = record.execution_line_id.production_id

                if record.execution_line_id.execution_id:
                    record.project_id = record.execution_line_id.execution_id.project_id
                    record.product_id = record.execution_line_id.execution_id.product_id
                else:
                    record.project_id = False
                    record.product_id = False
            else:
                record.execution_id = False
                record.project_id = False
                record.product_id = False
                record.component_id = False
                record.production_id = False

    workorder_id = fields.Many2one(
        'mrp.workorder',
        string='Work Order',
        index=True
    )
    name = fields.Char(string='Operation', required=True)
    operation_id = fields.Many2one(
        'mrp.routing.workcenter',
        string='Operation',
        related='workorder_id.operation_id',
        store=True,
        readonly=True
    )
    workcenter_id = fields.Many2one(
        'mrp.workcenter',
        string='Work Center'
    )
    state = fields.Selection(
        related='workorder_id.state',
        string='State',
        store=True,
        readonly=True
    )
    duration_expected = fields.Float(
        string='Expected Duration (minutes)'
    )
    duration_real = fields.Float(
        related='workorder_id.duration',
        string='Real Duration (minutes)',
        readonly=True
    )

    # NEW: Actual fields for execution
    actual_duration = fields.Float(
        string='Actual Duration (minutes)',
        help='Actual time taken for this operation'
    )
    workers_assigned = fields.Integer(
        string='Workers Assigned',
        help='Number of workers assigned to this operation'
    )
    machines_assigned = fields.Integer(
        string='Machines Assigned',
        help='Number of machines assigned to this operation'
    )

    qty_production = fields.Float(
        related='workorder_id.qty_production',
        string='Quantity to Produce',
        store=True,
        readonly=True
    )
    qty_produced = fields.Float(
        related='workorder_id.qty_produced',
        string='Quantity Produced',
        store=True,
        readonly=True
    )

    # NEW: Additional Code and Specifications from pricing
    additional_code = fields.Text(
        string='Additional Code',
        help='Component specifications from pricing'
    )
    specification_ids = fields.Many2many(
        'component.specification.value',
        'operation_specification_rel',
        'operation_id',
        'specification_id',
        string='Specifications',
        help='Component specifications from pricing'
    )
    specification_text = fields.Text(
        string='Specifications Text',
        compute='_compute_specification_text',
        store=True,
        help='Formatted text of all specifications'
    )

    @api.depends('specification_ids', 'specification_ids.value', 'specification_ids.specification_name')
    def _compute_specification_text(self):
        for record in self:
            if record.specification_ids:
                specs = []
                for spec in record.specification_ids.sorted('sequence'):
                    if spec.value:
                        specs.append('%s: %s' % (spec.specification_name, spec.value))
                record.specification_text = ' | '.join(specs) if specs else ''
            else:
                record.specification_text = ''

    selected = fields.Boolean(
        string='Select',
        help='Select this operation for batch update'
    )
    is_completed = fields.Boolean(
        string='Completed',
        compute='_compute_is_completed',
        store=True,
        index=True
    )
    progress_percentage = fields.Float(
        string='Progress %',
        compute='_compute_progress',
        store=True
    )
    date_start = fields.Datetime(
        related='workorder_id.date_start',
        string='Start Date',
        store=True,
        readonly=True
    )
    date_finished = fields.Datetime(
        related='workorder_id.date_finished',
        string='Finish Date',
        store=True,
        readonly=True
    )

    @api.depends('state')
    def _compute_is_completed(self):
        for record in self:
            record.is_completed = record.state in ('done', 'cancel')

    @api.depends('qty_production', 'qty_produced')
    def _compute_progress(self):
        for record in self:
            if record.qty_production:
                record.progress_percentage = (record.qty_produced / record.qty_production) * 100
            else:
                record.progress_percentage = 0.0

    def action_open_workorder(self):
        """Open the work order"""
        self.ensure_one()
        if not self.workorder_id:
            raise UserError(_('No work order linked to this operation!'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Work Order'),
            'res_model': 'mrp.workorder',
            'res_id': self.workorder_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_start(self):
        """Start the work order"""
        for record in self:
            if record.workorder_id and record.state in ('pending', 'ready', 'waiting'):
                record.workorder_id.button_start()

    def action_finish(self):
        """Finish the work order"""
        for record in self:
            if record.workorder_id and record.state in ('progress', 'to_close'):
                record.workorder_id.button_finish()

    def action_assign_resources(self):
        """Open wizard to assign workers and machines to selected operations"""
        selected_ops = self.env['work.order.operation.line'].browse(self.env.context.get('active_ids', []))

        if not selected_ops:
            raise UserError(_('Please select operations first!'))

        # Check if all selected operations have the same name
        operation_names = selected_ops.mapped('name')
        if len(set(operation_names)) > 1:
            raise UserError(_(
                'All selected operations must have the same name!\n\n'
                'Selected operations:\n%s'
            ) % '\n'.join(set(operation_names)))

        # Create wizard
        wizard = self.env['operation.resource.wizard'].create({
            'operation_ids': [(6, 0, selected_ops.ids)],
            'operation_name': selected_ops[0].name,
        })

        return {
            'type': 'ir.actions.act_window',
            'name': _('Assign Resources: %s') % selected_ops[0].name,
            'res_model': 'operation.resource.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }