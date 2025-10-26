# Project Product Planning & Costing Management

## Overview
This Odoo 17 module provides comprehensive project management with product costing, material planning, and production order generation capabilities.

## Features

### 1. Project Definition (Screen 1)
- Create and manage projects with customer information
- Define project timelines (start and end dates)
- Add multiple finished products to each project
- Track product quantities, weights, cost prices, and sale prices
- Calculate total costs, sales, and profits
- Project workflow: Draft → Confirmed → In Progress → Done

### 2. Product Pricing (Screen 2)
- Version-based pricing system for products
- Link pricing to specific projects and customers
- Define product components with quantities and costs
- Integrate with Odoo Bill of Materials (BOM)
- Create or link BOMs for each component
- Support for multiple pricing versions
- Workflow: Draft → Confirmed → Approved

### 3. Material & Production Planning (Screen 3)
- Load components from approved pricing
- Automatic material requirement calculation
- Stock availability checking (free stock vs. requirements)
- Shortage calculation and RFQ generation
- Work order creation for:
  - Main finished product
  - Semi-finished components with BOMs
- Track RFQs and work orders

## Installation

1. Copy the `project_product_costing` folder to your Odoo addons directory
2. Restart the Odoo server
3. Update the Apps list (Apps → Update Apps List)
4. Search for "Project Product Planning & Costing Management"
5. Click Install

## Dependencies

This module requires the following Odoo modules:
- base
- project
- product
- stock
- mrp (Manufacturing)
- purchase
- sale_management

## Usage

### Creating a Project
1. Go to Project Costing → Project Definitions
2. Click "Create"
3. Fill in project details (name, customer, dates)
4. Add project products in the "Project Products" tab
5. Confirm the project

### Creating Product Pricing
1. Go to Project Costing → Product Pricing
2. Click "Create"
3. Select customer (projects will be filtered automatically)
4. Select project (products will be filtered automatically)
5. Select product (quantity and weight auto-filled)
6. Add component products
7. Link or create BOMs for components
8. Confirm and approve the pricing

### Material & Production Planning
1. Go to Project Costing → Material & Production Planning
2. Click "Create"
3. Select project and product
4. Click "Load Components" to import from pricing
5. Click "Material Planning" to:
   - View material requirements
   - Check stock availability
   - See shortages
   - Create RFQs for shortage items
6. Click "Create Work Orders" to generate production orders

## Technical Details

### Models
- `project.definition` - Project header information
- `project.product.line` - Project products (one-to-many)
- `project.product.pricing` - Pricing header with versioning
- `project.product.component` - Product components with BOM links
- `material.production.planning` - Planning header
- `material.planning.component` - Loaded components
- `material.requirement.line` - Material requirements with stock info

### Sequences
- Project Code: PROJ/00001
- Pricing Code: PRICE/00001
- Planning Reference: PLAN/00001

## Configuration

### Access Rights
All users in the "User: All Documents" group have full access to all features.

### Customization
You can customize:
- Sequence prefixes and padding
- Field validations
- Workflow states
- View layouts

## Support

For issues or questions, please contact: support@yourcompany.com

## Credits

**Author**: Your Company
**Version**: 17.0.1.0.0
**License**: LGPL-3

## Changelog

### Version 17.0.1.0.0
- Initial release
- Project definition with multiple products
- Version-based product pricing
- BOM integration
- Material planning with stock checking
- Work order generation
- RFQ creation for shortages
