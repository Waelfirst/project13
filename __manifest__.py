# -*- coding: utf-8 -*-
{
    'name': 'Project Product Planning & Costing Management',
    'version': '17.0.3.3.0',
    'category': 'Project',
    'summary': 'Manage projects, product costing, and material planning with enhanced work order operations',
    'description': """
        Project Product Planning & Costing Management
        ==============================================
        * Define projects with finished products
        * Version-based product pricing and components
        * Material and production planning
        * BOM integration and work order generation
        * Enhanced work order operations with:
          - Additional Code and Specifications from Pricing
          - Search by Project and Product
          - Batch resource assignment (Workers & Machines)
          - Excel export/import for actual data
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': [
        'base',
        'project',
        'product',
        'stock',
        'mrp',
        'purchase',
        'sale_management',
    ],
    'data': [
        # Stage 1: Core model security (loaded first)
        'security/ir.model.access.csv',
        
        # Stage 2: Data and Views
        'data/sequence_data.xml',
        'views/project_definition_views.xml',
        'views/project_product_pricing_views.xml',
        'views/material_production_planning_views.xml',
        'views/work_order_execution_views.xml',
        'views/production_report_views.xml',
        'views/component_specification_views.xml',
        'views/excel_import_manager_views.xml',
        'views/import_wizard_views.xml',
        'views/import_separate_wizards_views.xml',
        'views/work_order_wizard_views.xml',
        'views/operation_resource_wizard_views.xml',
        'views/operations_excel_wizard_views.xml',
        'views/menu_views.xml',
        
        # Stage 3: Secondary and Wizard security (loaded after views)
        'security/ir.model.access.secondary.csv',
        'security/ir.model.access.wizard.csv',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'post_init_hook': 'post_init_hook',
}
