# Excel Import Template Guide

## Overview
This guide explains how to prepare an Excel file to import product components and their Bills of Materials (BOMs) into the Product Pricing screen.

## Excel File Structure

Your Excel file should contain up to 3 sheets:

### Sheet 1: Components (Required)
This sheet contains the main component products.

**Column Headers:**
1. **Component Name** - The product name or internal reference (must exist in Odoo)
2. **Quantity** - Quantity required (numeric)
3. **Weight** - Weight in kg (numeric, optional)
4. **Cost Price** - Unit cost price (numeric)
5. **BOM Code** - Unique code to link with BOM data (text, optional)

**Example:**
```
Component Name    | Quantity | Weight | Cost Price | BOM Code
Steel Sheet       | 2        | 5.5    | 50.00      | BOM-001
Plastic Housing   | 1        | 0.8    | 25.00      | BOM-002
Screws M6         | 10       | 0.05   | 0.50       | 
Motor Assembly    | 1        | 2.0    | 150.00     | BOM-003
```

### Sheet 2: BOM Materials (Optional)
This sheet contains the raw materials for each component's BOM.

**Column Headers:**
1. **BOM Code** - Must match the BOM Code from Components sheet
2. **Material Name** - Raw material product name (must exist in Odoo)
3. **Quantity** - Quantity of raw material needed (numeric)
4. **Unit** - Unit of measure (optional, text like "kg", "pcs", "meters")

**Example:**
```
BOM Code | Material Name      | Quantity | Unit
BOM-001  | Steel Raw Material | 6        | kg
BOM-001  | Coating Material   | 0.5      | kg
BOM-002  | Plastic Pellets    | 1        | kg
BOM-002  | Paint              | 0.1      | liter
BOM-003  | Electric Motor     | 1        | pcs
BOM-003  | Wiring Harness     | 1        | set
BOM-003  | Mounting Bracket   | 2        | pcs
```

### Sheet 3: BOM Operations (Optional)
This sheet contains the manufacturing operations for each component's BOM.

**Column Headers:**
1. **BOM Code** - Must match the BOM Code from Components sheet
2. **Operation Name** - Name of the operation
3. **Workcenter** - Workcenter name (must exist in Odoo, optional)
4. **Duration** - Time in minutes (numeric)

**Example:**
```
BOM Code | Operation Name    | Workcenter        | Duration
BOM-001  | Cutting           | CNC Machine       | 15
BOM-001  | Bending           | Press Machine     | 10
BOM-001  | Coating           | Coating Line      | 30
BOM-002  | Injection Molding | Molding Machine 1 | 5
BOM-002  | Painting          | Paint Booth       | 10
BOM-002  | Quality Check     | QC Station        | 5
BOM-003  | Assembly          | Assembly Line A   | 20
BOM-003  | Testing           | Test Station      | 15
```

## Import Process

### Step 1: Prepare Your Data
1. Open Excel or LibreOffice Calc
2. Create sheets named exactly: "Components", "BOM Materials", "BOM Operations"
3. Add column headers in the first row
4. Fill in your data starting from row 2

### Step 2: Upload to Odoo
1. Go to **Project Costing → Product Pricing**
2. Open a pricing record (or create new one)
3. Select Customer, Project, and Product
4. Click **"Import from Excel"** button
5. Select import type:
   - **Components Only**: Imports only components without BOM data
   - **Components with BOM Data**: Imports components and creates BOMs
6. Click "Choose File" and select your Excel file
7. Click **"Import"** button

### Step 3: Verify Import
After import:
- Check the **Product Components** tab to see imported components
- Click the BOM icon next to each component to view/edit the created BOM
- Verify quantities, prices, and BOM details

## Important Notes

### Product Names
- **Must Match Exactly**: Product names in Excel must exactly match product names in Odoo
- **Or Use Internal Reference**: You can use product internal reference codes instead
- **Case Sensitive**: "Steel Sheet" ≠ "steel sheet"

### BOM Codes
- Can be any text (e.g., "BOM-001", "STEEL-BOM", "Motor-123")
- Must be unique for each component
- Used to link components with their materials and operations
- If empty, component will be imported without BOM

### Workcenters
- Must exist in Odoo Manufacturing module
- Create workcenters before import if they don't exist
- If workcenter not found, operation will be created without workcenter

### Numeric Values
- Use decimal point (.) not comma (,)
- Example: 10.5 ✅  |  10,5 ❌
- Empty cells will use default values (0 or 1)

### File Format
- Supported: .xlsx (Excel 2007+) and .xls (Excel 97-2003)
- Recommended: .xlsx format

## Common Errors and Solutions

### Error: "Product not found: [Product Name]"
**Solution**: 
- Check product exists in Odoo
- Verify spelling matches exactly
- Try using product internal reference code

### Error: "Workcenter not found: [Workcenter Name]"
**Solution**:
- Create the workcenter in Odoo first
- Or leave workcenter column empty
- Check spelling matches exactly

### Error: "Invalid quantity value"
**Solution**:
- Make sure quantities are numbers
- Use decimal point (.) not comma (,)
- Remove any text or special characters

### Error: "Excel library not installed"
**Solution**:
- Contact your Odoo administrator
- Need to install Python libraries: openpyxl or xlrd

## Example Use Case

**Scenario**: You're manufacturing a "Widget A" product that requires:
- Steel Sheet (needs cutting and bending)
- Plastic Housing (needs injection molding and painting)
- Screws (no BOM needed)

**Your Excel file would have:**

**Components Sheet:**
```
Component Name    | Quantity | Weight | Cost Price | BOM Code
Steel Sheet       | 2        | 5.5    | 50.00      | STL-001
Plastic Housing   | 1        | 0.8    | 25.00      | PLS-001
Screws M6         | 10       | 0.05   | 0.50       | 
```

**BOM Materials Sheet:**
```
BOM Code | Material Name      | Quantity | Unit
STL-001  | Steel Raw Material | 6        | kg
STL-001  | Coating Material   | 0.5      | kg
PLS-001  | Plastic Pellets    | 1        | kg
PLS-001  | Paint              | 0.1      | liter
```

**BOM Operations Sheet:**
```
BOM Code | Operation Name    | Workcenter      | Duration
STL-001  | Cutting           | CNC Machine     | 15
STL-001  | Bending           | Press Machine   | 10
STL-001  | Coating           | Coating Line    | 30
PLS-001  | Injection Molding | Molding Machine | 5
PLS-001  | Painting          | Paint Booth     | 10
```

## Tips for Large Imports

1. **Start Small**: Test with 2-3 components first
2. **Backup Data**: Always backup before large imports
3. **Verify Products**: Check all products exist in Odoo
4. **Create Workcenters**: Set up all workcenters beforehand
5. **Use Templates**: Save your Excel template for future use

## Need Help?

If you encounter issues:
1. Check the Odoo logs for detailed error messages
2. Verify your Excel file structure matches this guide
3. Test with a small sample file first
4. Contact your Odoo administrator for technical issues

## Download Template

A sample Excel template with all sheets and headers is recommended to be created and saved for reference. You can copy the column headers from this guide to create your own template.
