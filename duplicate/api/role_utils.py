import frappe
from frappe import _


@frappe.whitelist()
def duplicate_role(source_role, new_role_name, copy_permissions=True):
	"""
	Duplicate a role with all its permissions
	
	Args:
		source_role (str): Name of the source role to duplicate
		new_role_name (str): Name for the new duplicated role
		copy_permissions (bool): Whether to copy all permissions from source role
		
	Returns:
		dict: Result with success status and new role name
	"""
	try:
		# Check if source role exists
		if not frappe.db.exists("Role", source_role):
			frappe.throw(_("Source role '{0}' does not exist").format(source_role))
		
		# Check if new role name already exists
		if frappe.db.exists("Role", new_role_name):
			frappe.throw(_("Role '{0}' already exists").format(new_role_name))
		
		# Get source role document
		source_role_doc = frappe.get_doc("Role", source_role)
		
		# Create new role document
		new_role_doc = frappe.new_doc("Role")
		new_role_doc.role_name = new_role_name
		
		# Copy basic fields from source role
		fields_to_copy = [
			"disabled", "desk_access", "two_factor_auth", 
			"restrict_to_domain", "is_custom"
		]
		
		for field in fields_to_copy:
			if hasattr(source_role_doc, field):
				setattr(new_role_doc, field, getattr(source_role_doc, field))
		
		# Insert the new role
		new_role_doc.insert(ignore_permissions=True)
		
		if copy_permissions:
			# Copy all permissions from source role
			copy_role_permissions(source_role, new_role_name)
		
		frappe.db.commit()
		
		return {
			"success": True,
			"message": _("Role '{0}' duplicated successfully as '{1}'").format(source_role, new_role_name),
			"new_role": new_role_name
		}
		
	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(title="Role Duplication Error", message=str(e))
		return {
			"success": False,
			"message": str(e)
		}


def copy_role_permissions(source_role, target_role):
	"""
	Copy all permissions from source role to target role
	
	Args:
		source_role (str): Source role name
		target_role (str): Target role name
	"""
	# Get all DocType permissions for source role
	doctype_permissions = frappe.get_all(
		"DocPerm",
		filters={"role": source_role},
		fields=["*"]
	)
	
	# Copy DocType permissions
	for perm in doctype_permissions:
		new_perm = frappe.new_doc("DocPerm")
		
		# Copy all fields except name and role
		fields_to_copy = [
			"parent", "parenttype", "parentfield", "permlevel", 
			"read", "write", "create", "delete", "submit", "cancel", 
			"amend", "report", "export", "import", "set_user_permissions",
			"share", "print", "email", "if_owner", "select", "match"
		]
		
		for field in fields_to_copy:
			if field in perm:
				setattr(new_perm, field, perm[field])
		
		new_perm.role = target_role
		new_perm.insert(ignore_permissions=True)
	
	# Copy Custom DocPerm if any
	custom_permissions = frappe.get_all(
		"Custom DocPerm",
		filters={"role": source_role},
		fields=["*"]
	)
	
	for perm in custom_permissions:
		new_perm = frappe.new_doc("Custom DocPerm")
		
		fields_to_copy = [
			"parent", "parenttype", "parentfield", "permlevel",
			"read", "write", "create", "delete", "submit", "cancel",
			"amend", "report", "export", "import", "set_user_permissions",
			"share", "print", "email", "if_owner", "select", "match"
		]
		
		for field in fields_to_copy:
			if field in perm:
				setattr(new_perm, field, perm[field])
		
		new_perm.role = target_role
		new_perm.insert(ignore_permissions=True)


@frappe.whitelist()
def get_role_details(role_name):
	"""
	Get detailed information about a role including its permissions
	
	Args:
		role_name (str): Name of the role
		
	Returns:
		dict: Role details and permissions
	"""
	if not frappe.db.exists("Role", role_name):
		frappe.throw(_("Role '{0}' does not exist").format(role_name))
	
	role_doc = frappe.get_doc("Role", role_name)
	
	# Get DocType permissions
	doctype_permissions = frappe.get_all(
		"DocPerm",
		filters={"role": role_name},
		fields=["parent", "permlevel", "read", "write", "create", "delete", 
				"submit", "cancel", "amend", "report", "export", "import", 
				"set_user_permissions", "share", "print", "email", "if_owner"]
	)
	
	# Get Custom permissions
	custom_permissions = frappe.get_all(
		"Custom DocPerm",
		filters={"role": role_name},
		fields=["parent", "permlevel", "read", "write", "create", "delete", 
				"submit", "cancel", "amend", "report", "export", "import", 
				"set_user_permissions", "share", "print", "email", "if_owner"]
	)
	
	return {
		"role": role_doc.as_dict(),
		"doctype_permissions": doctype_permissions,
		"custom_permissions": custom_permissions,
		"total_permissions": len(doctype_permissions) + len(custom_permissions)
	}


@frappe.whitelist()
def bulk_duplicate_roles(roles_data):
	"""
	Duplicate multiple roles at once
	
	Args:
		roles_data (list): List of dicts with source_role and new_role_name
		
	Returns:
		dict: Results for each role duplication
	"""
	if isinstance(roles_data, str):
		import json
		roles_data = json.loads(roles_data)
	
	results = []
	
	for role_data in roles_data:
		source_role = role_data.get("source_role")
		new_role_name = role_data.get("new_role_name")
		copy_permissions = role_data.get("copy_permissions", True)
		
		result = duplicate_role(source_role, new_role_name, copy_permissions)
		results.append({
			"source_role": source_role,
			"new_role_name": new_role_name,
			"result": result
		})
	
	return {"results": results}


@frappe.whitelist()
def get_all_roles_summary():
	"""
	Get summary of all roles with their permission counts
	
	Returns:
		list: List of roles with summary information
	"""
	roles = frappe.get_all(
		"Role", 
		fields=["name", "disabled", "desk_access", "two_factor_auth", "restrict_to_domain", "is_custom"],
		order_by="name"
	)
	
	for role in roles:
		# Count permissions for each role
		doctype_count = frappe.db.count("DocPerm", {"role": role.name})
		custom_count = frappe.db.count("Custom DocPerm", {"role": role.name})
		
		role["permission_count"] = doctype_count + custom_count
		role["doctype_permissions"] = doctype_count
		role["custom_permissions"] = custom_count
	
	return roles
