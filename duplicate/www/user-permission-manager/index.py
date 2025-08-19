import frappe
from frappe import _

def get_context(context):
	"""Set context for User Permission Manager page"""
	context.title = _("User Permission Manager Dashboard")
	context.no_cache = 1
	
	# Get all permission managers
	context.managers = frappe.get_all(
		"User Permission Manager",
		fields=["name", "manager_name", "description", "is_active", "apply_to_all_users", "user_field"],
		order_by="manager_name"
	)
	
	# Add permission count for each manager
	for manager in context.managers:
		count = frappe.db.count("User Permission Details", {"parent": manager.name})
		manager["permission_count"] = count
	
	# Get statistics
	from duplicate.api.user_permission_utils import get_permission_statistics
	context.stats = get_permission_statistics()
	
	# Get all users for selection
	context.users = frappe.get_all(
		"User",
		filters={"enabled": 1, "user_type": "System User"},
		fields=["name", "full_name"],
		order_by="full_name"
	)
	
	return context
