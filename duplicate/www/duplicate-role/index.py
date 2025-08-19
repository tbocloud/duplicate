import frappe
from frappe import _

def get_context(context):
	"""Set context for duplicate role page"""
	context.title = _("Easy Duplicate Role")
	context.no_cache = 1
	
	# Get all roles for selection
	context.roles = frappe.get_all(
		"Role",
		fields=["name", "disabled", "desk_access", "two_factor_auth"],
		order_by="name"
	)
	
	# Add permission count for each role
	for role in context.roles:
		doctype_count = frappe.db.count("DocPerm", {"role": role.name})
		custom_count = frappe.db.count("Custom DocPerm", {"role": role.name})
		role["permission_count"] = doctype_count + custom_count
	
	return context
