# Installation Guide - Project Product Planning & Costing Management

## Prerequisites

Before installing this module, ensure you have:

1. **Odoo 17 Enterprise** or Community Edition installed
2. Required dependencies installed:
   - Manufacturing (mrp)
   - Purchase
   - Sales Management
   - Project
   - Inventory (stock)

## Step-by-Step Installation

### 1. Prepare the Module

1. Extract the `project_product_costing.zip` file
2. You should see a folder named `project_product_costing`
3. Verify the folder structure:
   ```
   project_product_costing/
   ├── __init__.py
   ├── __manifest__.py
   ├── models/
   ├── views/
   ├── security/
   ├── data/
   ├── wizards/
   ├── static/
   └── README.md
   ```

### 2. Copy to Addons Directory

Copy the `project_product_costing` folder to your Odoo addons directory:

**For Linux:**
```bash
sudo cp -r project_product_costing /opt/odoo/addons/
sudo chown -R odoo:odoo /opt/odoo/addons/project_product_costing
```

**For Windows:**
```
Copy the folder to: C:\Program Files\Odoo 17\server\odoo\addons\
```

**For Development Environment:**
```
Copy to your custom addons path specified in odoo.conf
```

### 3. Update Addons Path (if needed)

Ensure your `odoo.conf` file includes the addons path:

```ini
[options]
addons_path = /opt/odoo/addons,/opt/odoo/custom_addons
```

### 4. Restart Odoo Server

**Linux (systemd):**
```bash
sudo systemctl restart odoo
```

**Linux (manual):**
```bash
sudo /etc/init.d/odoo restart
```

**Windows:**
```
Restart the Odoo service from Services panel
```

**Development:**
```bash
python odoo-bin -c odoo.conf
```

### 5. Update Apps List

1. Log in to Odoo as Administrator
2. Go to **Apps** (activate Developer Mode if needed)
3. Click **Update Apps List**
4. Confirm the update

### 6. Install the Module

1. In the Apps menu, search for: **"Project Product Planning"**
2. Click on the module card
3. Click **Install**
4. Wait for installation to complete

### 7. Verify Installation

After installation, verify by:

1. Check the main menu - you should see **"Project Costing"**
2. Navigate to: Project Costing → Project Definitions
3. Try creating a test project

## Activating Developer Mode

If you need to activate Developer Mode:

**Method 1: Via Settings**
1. Go to Settings
2. Scroll to bottom
3. Click "Activate the developer mode"

**Method 2: Via URL**
Add `?debug=1` to your URL:
```
http://localhost:8069/web?debug=1
```

## Configuration After Installation

### 1. Set Up Products
1. Go to **Inventory → Products**
2. Create or verify your products
3. Set product types (Storable Product / Consumable)
4. Set standard prices

### 2. Set Up BOMs (Optional)
1. Go to **Manufacturing → Products → Bills of Materials**
2. Create BOMs for semi-finished products
3. Define components and operations

### 3. Set Up Customers
1. Go to **Sales → Customers**
2. Create or verify customer records

### 4. Configure Suppliers (Optional)
1. Go to **Purchase → Vendors**
2. Add vendor information
3. Link vendors to products

## Usage Quick Start

### Create Your First Project

1. **Project Costing → Project Definitions → Create**
   - Project Name: "Q1 2025 Production"
   - Customer: Select a customer
   - Start Date: Today
   - End Date: Future date
   - Add products with quantities and prices

2. **Project Costing → Product Pricing → Create**
   - Select the customer
   - Select the project
   - Select a product
   - Add component products
   - Link BOMs

3. **Project Costing → Material & Production Planning → Create**
   - Select project and product
   - Click "Load Components"
   - Click "Material Planning"
   - Review material requirements
   - Create RFQs if needed
   - Create work orders

## Troubleshooting

### Module Not Appearing in Apps List

**Solution:**
1. Verify the module is in the correct addons directory
2. Check file permissions (Linux): `sudo chown -R odoo:odoo /path/to/module`
3. Restart Odoo server
4. Update Apps List again
5. Clear browser cache

### Installation Error: "Module not found"

**Solution:**
1. Check `__manifest__.py` file exists
2. Verify all dependencies are installed
3. Check Odoo logs: `/var/log/odoo/odoo-server.log`

### Import Error: "No module named..."

**Solution:**
1. Ensure all Python dependencies are installed
2. Check all `__init__.py` files exist in folders
3. Verify Python syntax in all files

### Access Rights Error

**Solution:**
1. Go to Settings → Users & Companies → Groups
2. Verify user has appropriate access rights
3. Check `security/ir.model.access.csv` is loaded

### Database Error

**Solution:**
1. Update the module: Apps → Select module → Upgrade
2. Or reinstall: Uninstall → Install
3. Check database logs for specific errors

## Uninstallation

To uninstall the module:

1. Go to **Apps**
2. Remove the "Apps" filter
3. Search for "Project Product"
4. Click **Uninstall**
5. Confirm uninstallation

**Note:** Uninstalling will remove all data created by this module!

## Backup Before Installation

**Always backup your database before installing new modules:**

```bash
# Odoo database backup
pg_dump -U odoo -d your_database_name -f backup_before_module.sql

# Or use Odoo interface:
# Settings → Database Manager → Backup
```

## Support

For technical support:
- Email: support@yourcompany.com
- Documentation: Check README.md
- Odoo Logs: `/var/log/odoo/odoo-server.log`

## Version Compatibility

- **Odoo Version:** 17.0
- **Python Version:** 3.10+
- **PostgreSQL Version:** 12+

## License

LGPL-3 (GNU Lesser General Public License v3.0)
