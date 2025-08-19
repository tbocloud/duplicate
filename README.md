# Easy Duplicate Role

A comprehensive role duplication system for Frappe applications that allows you to easily duplicate roles with all their permissions, user permissions, and settings.

## Features

- **🔄 Complete Role Duplication**: Clone roles with all permissions, settings, and configurations
- **👥 User Permission Cloning**: Duplicate user-specific permissions and restrictions
- **🎯 Smart Permission Management**: Automatically handles complex permission structures
- **🔍 Real-time Validation**: Prevents duplicate role names and validates permissions
- **📊 Detailed Reporting**: Shows comprehensive results with success/failure counts
- **🖥️ Multiple Interfaces**: Web interface, form buttons, and programmatic access

## Quick Start

### 1. Role Duplication

#### Using the Role Form
1. Navigate to any **Role** document (e.g., HR Manager, Delivery Manager)
2. Click the **"Easy Duplicate Role"** button in the toolbar
3. Enter the new role name
4. The system will create a complete copy with all permissions

![Role Form with Easy Duplicate Role Button](screenshots/role-form.png)

#### Using the Role Duplicate DocType
1. Go to **Role Duplicate** list
2. Create a new **Role Duplicate** document
3. Select the **Source Role** (e.g., "Delivery Manager")
4. Enter the **New Role Name** (e.g., "Delivery Manager Copy")
5. Click **"Load Permissions"** to preview all permissions
6. Click **"Create New Role"** to complete the duplication

![Role Duplicate Form](screenshots/role-duplicate-form.png)

### 2. User Permission Management

#### Using User Permission Manager
1. Navigate to **User Permission Manager**
2. Create a new document with:
   - **Alias Name**: Friendly identifier
   - **Applied User**: Target user email
3. Add permission details in the **User Permission Details** table:
   - **Allow**: Document type (e.g., Customer Group, Warehouse)
   - **For Value**: Specific value (e.g., Commercial, Stores - GE)
   - Configure access levels (Apply To All Documents, Is Default, Hide Descendants)

![User Permission Manager](screenshots/user-permission-manager.png)

## Installation

1. Get the app from the repository:
```bash
bench get-app https://github.com/your-repo/duplicate
```

2. Install the app on your site:
```bash
bench --site [your-site] install-app duplicate
```

3. Build assets:
```bash
bench build --app duplicate
```

## Usage Examples

### Scenario 1: Creating Department-Specific Roles
```
Source Role: "HR Manager" 
New Role: "HR Manager - Mumbai Branch"
Result: Complete role with all HR permissions for Mumbai operations
```

### Scenario 2: Warehouse-Specific Access
```
User: warehouse.manager@company.com
Permissions: 
- Customer Group: Commercial (Apply to All Documents)
- Warehouse: Stores - GE (Default access)
```

### Scenario 3: Manager Role Variations
```
Source: "Delivery Manager"
Target: "Delivery Manager Copy"
Permissions Copied: Delivery Note, Delivery Settings, Delivery Trip, Driver, Serial and Batch Bundle
```

## Technical Details

### Role Permissions Handled
- ✅ **Read/Write/Create/Delete** permissions
- ✅ **Submit/Cancel/Amend** permissions  
- ✅ **Report/Export/Print** permissions
- ✅ **Email/Share** permissions
- ✅ **If Owner** restrictions
- ✅ **Set User Permissions** capabilities

### User Permission Types
- ✅ **Document-level restrictions** (Customer, Supplier, etc.)
- ✅ **Value-based access** (Warehouse, Cost Center, etc.)
- ✅ **Hierarchical permissions** with descendant control
- ✅ **Default permission assignment**
- ✅ **Apply to all documents** settings

### Validation Features
- 🔍 **Duplicate role name prevention**
- 🔍 **Permission consistency checks**
- 🔍 **User existence validation**
- 🔍 **Real-time conflict detection**

## API Reference

### Programmatic Usage

```python
import frappe

# Create role duplicate document
doc = frappe.new_doc('Role Duplicate')
doc.source_role = 'HR Manager'
doc.new_role_name = 'HR Manager Copy'
doc.description = 'Copy of HR Manager role for testing'

# Load permissions from source role
doc.load_source_role_permissions()
print(f'Loaded {len(doc.role_permissions)} permissions')

# Create the new role with all permissions
result = doc.create_new_role()
print(f'Result: {result}')
```

### API Endpoints

```javascript
// Load permissions from source role
frappe.call({
    method: 'duplicate.duplicate.doctype.role_duplicate.role_duplicate.load_role_permissions',
    args: {
        source_role: 'HR Manager',
        role_duplicate_name: 'ROLE-DUP-2025-00001'
    }
});

// Create new role from duplicate
frappe.call({
    method: 'duplicate.duplicate.doctype.role_duplicate.role_duplicate.create_role_from_duplicate',
    args: {
        role_duplicate_name: 'ROLE-DUP-2025-00001'
    }
});
```

## DocTypes Included

### Primary DocTypes
- **Role Duplicate**: Main interface for role duplication
- **User Permission Manager**: Enhanced user permission management

### Child DocTypes
- **Role Duplicate Permissions**: Stores individual permission details
- **User Permission Details**: Manages user-specific access controls

## Troubleshooting

### Common Issues

**Q: Role creation shows "Network/Server Error"**
A: Check browser console for detailed error messages. Verify API endpoints are accessible and CSRF tokens are valid.

**Q: Only some permissions are copied**
A: Check for DocTypes that don't exist in the target environment. The system will skip non-existent DocTypes and report them.

**Q: User permissions not applying**
A: Verify the user exists and has the necessary base permissions. User permissions are restrictions, not grants.

### Debug Mode

Enable debug logging in browser console to see detailed API call information:
```javascript
// Check browser console for detailed logs when using the interface
```

## Requirements

- **Frappe Framework**: v14.0.0 or higher
- **Python**: 3.8+
- **Database**: MySQL/MariaDB or PostgreSQL

## License

MIT License - see LICENSE file for details

## Support

For issues and feature requests, please create an issue in the GitHub repository.

## Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/duplicate
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### CI

This app can use GitHub Actions for CI. The following workflows are configured:

- CI: Installs this app and runs unit tests on every push to `develop` branch.
- Linters: Runs [Frappe Semgrep Rules](https://github.com/frappe/semgrep-rules) and [pip-audit](https://pypi.org/project/pip-audit/) on every pull request.


### License

mit
