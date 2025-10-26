# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class OperationResourceWizard(models.TransientModel):
    """معالج تعيين الموارد للعمليات"""
    _name = 'operation.resource.wizard'
    _description = 'Operation Resource Assignment Wizard'

    operation_ids = fields.Many2many(
        'work.order.operation.line',
        string='Operations',
        required=True,
        readonly=True
    )
    operation_name = fields.Char(
        string='Operation Name',
        readonly=True
    )
    operations_count = fields.Integer(
        string='Operations Count',
        compute='_compute_operations_count'
    )

    # Resource fields
    workers_assigned = fields.Integer(
        string='Number of Workers',
        default=1,
        required=True,
        help='Number of workers to assign to each operation'
    )
    machines_assigned = fields.Integer(
        string='Number of Machines',
        default=1,
        required=True,
        help='Number of machines to assign to each operation'
    )
    actual_duration = fields.Float(
        string='Actual Duration (minutes)',
        help='Actual time taken for each operation (optional)'
    )

    notes = fields.Text(
        string='Notes',
        help='Additional notes for these operations'
    )

    @api.depends('operation_ids')
    def _compute_operations_count(self):
        for wizard in self:
            wizard.operations_count = len(wizard.operation_ids)

    def action_assign_resources(self):
        """Assign workers and machines to all selected operations"""
        self.ensure_one()

        if not self.operation_ids:
            raise UserError(_('No operations selected!'))

        # Update all selected operations
        vals = {
            'workers_assigned': self.workers_assigned,
            'machines_assigned': self.machines_assigned,
        }

        if self.actual_duration:
            vals['actual_duration'] = self.actual_duration

        self.operation_ids.write(vals)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('%s operations updated with:\n%s workers\n%s machines') % (
                    len(self.operation_ids),
                    self.workers_assigned,
                    self.machines_assigned
                ),
                'type': 'success',
                'sticky': False,
            }
        }