import frappe
from frappe import _


@frappe.whitelist()
def get_available_permission_managers():
	"""Get all active User Permission Managers"""
	managers = frappe.get_all("User Permission Manager",
		filters={"is_active": 1},
		fields=["name", "manager_name", "description", "apply_to_all_users", "user_field"],
		order_by="manager_name"
	)
	
	# Add permission count for each manager
	for manager in managers:
		count = frappe.db.count("User Permission Details", {"parent": manager.name})
		manager["permission_count"] = count
	
	return managers


@frappe.whitelist()
def get_user_permissions_summary(user_email):
	"""Get summary of user permissions with their source managers"""
	# Ensure custom field exists
	from duplicate.duplicate.doctype.user_permission_manager.user_permission_manager import UserPermissionManager
	doc = frappe.new_doc("User Permission Manager")
	doc.ensure_user_permission_custom_field()
	
	permissions = frappe.db.sql("""
		SELECT 
			up.name,
			up.allow,
			up.for_value,
			up.applicable_for,
			up.apply_to_all,
			up.is_default,
			up.user_permission_manager,
			upm.manager_name
		FROM `tabUser Permission` up
		LEFT JOIN `tabUser Permission Manager` upm ON up.user_permission_manager = upm.name
		WHERE up.user = %s
		ORDER BY up.allow, up.for_value
	""", (user_email,), as_dict=True)
	
	# Group by source
	managed_permissions = []
	manual_permissions = []
	
	for perm in permissions:
		if perm.user_permission_manager:
			managed_permissions.append(perm)
		else:
			manual_permissions.append(perm)
	
	return {
		"managed_permissions": managed_permissions,
		"manual_permissions": manual_permissions,
		"total_permissions": len(permissions)
	}


@frappe.whitelist()
def bulk_apply_permission_manager(manager_name, user_emails):
	"""Apply permission manager to multiple users"""
	if isinstance(user_emails, str):
		import json
		user_emails = json.loads(user_emails)
	
	if not frappe.has_permission("User Permission Manager", "write"):
		frappe.throw(_("Insufficient permissions"))
	
	manager_doc = frappe.get_doc("User Permission Manager", manager_name)
	
	if not manager_doc.is_active:
		frappe.throw(_("User Permission Manager is not active"))
	
	results = []
	
	for user_email in user_emails:
		try:
			manager_doc.create_user_permissions_for_user(user_email)
			results.append({
				"user": user_email,
				"success": True,
				"message": _("Permissions applied successfully")
			})
		except Exception as e:
			results.append({
				"user": user_email,
				"success": False,
				"message": str(e)
			})
	
	return {"results": results}


@frappe.whitelist()
def remove_permission_manager_from_user(manager_name, user_email):
	"""Remove all permissions created by a specific manager for a user"""
	if not frappe.has_permission("User Permission Manager", "write"):
		frappe.throw(_("Insufficient permissions"))
	
	# Ensure custom field exists
	from duplicate.duplicate.doctype.user_permission_manager.user_permission_manager import UserPermissionManager
	doc = frappe.new_doc("User Permission Manager")
	doc.ensure_user_permission_custom_field()
	
	permissions_to_delete = frappe.get_all("User Permission",
		filters={
			"user": user_email,
			"user_permission_manager": manager_name
		},
		pluck="name"
	)
	
	deleted_count = 0
	for perm_name in permissions_to_delete:
		frappe.delete_doc("User Permission", perm_name, ignore_permissions=True)
		deleted_count += 1
	
	frappe.db.commit()
	
	return {
		"success": True,
		"message": _("Removed {0} permissions from user {1}").format(deleted_count, user_email),
		"deleted_count": deleted_count
	}


@frappe.whitelist()
def get_permission_manager_preview(manager_name):
	"""Get detailed preview of what permissions will be applied"""
	manager_doc = frappe.get_doc("User Permission Manager", manager_name)
	
	target_users = manager_doc.get_target_users()
	
	preview_data = {
		"manager_details": {
			"name": manager_doc.name,
			"manager_name": manager_doc.manager_name,
			"description": manager_doc.description,
			"is_active": manager_doc.is_active,
			"apply_to_all_users": manager_doc.apply_to_all_users,
			"user_field": manager_doc.user_field
		},
		"permission_details": [],
		"target_users": target_users,
		"target_user_count": len(target_users)
	}
	
	for detail in manager_doc.user_permission_details:
		preview_data["permission_details"].append({
			"allow": detail.allow,
			"for_value": detail.for_value,
			"applicable_for": detail.applicable_for,
			"apply_to_all_doctypes": detail.apply_to_all_doctypes,
			"is_default": detail.is_default
		})
	
	return preview_data


@frappe.whitelist()
def sync_all_permission_managers():
	"""Sync all active permission managers"""
	if not frappe.has_permission("User Permission Manager", "write"):
		frappe.throw(_("Insufficient permissions"))
	
	active_managers = frappe.get_all("User Permission Manager",
		filters={"is_active": 1},
		pluck="name"
	)
	
	results = []
	
	for manager_name in active_managers:
		try:
			manager_doc = frappe.get_doc("User Permission Manager", manager_name)
			manager_doc.sync_user_permissions()
			
			results.append({
				"manager": manager_name,
				"success": True,
				"message": _("Synced successfully")
			})
		except Exception as e:
			results.append({
				"manager": manager_name,
				"success": False,
				"message": str(e)
			})
	
	return {
		"results": results,
		"total_managers": len(active_managers),
		"success_count": len([r for r in results if r["success"]])
	}


@frappe.whitelist()
def get_permission_statistics():
	"""Get statistics about user permissions and managers"""
	stats = {}
	
	# Permission Manager stats
	stats["total_managers"] = frappe.db.count("User Permission Manager")
	stats["active_managers"] = frappe.db.count("User Permission Manager", {"is_active": 1})
	stats["inactive_managers"] = stats["total_managers"] - stats["active_managers"]
	
	# User Permission stats
	stats["total_permissions"] = frappe.db.count("User Permission")
	
	# Managed vs Manual permissions
	from duplicate.duplicate.doctype.user_permission_manager.user_permission_manager import UserPermissionManager
	doc = frappe.new_doc("User Permission Manager")
	doc.ensure_user_permission_custom_field()
	
	managed_count = frappe.db.count("User Permission", {"user_permission_manager": ["!=", ""]})
	stats["managed_permissions"] = managed_count
	stats["manual_permissions"] = stats["total_permissions"] - managed_count
	
	# Users with permissions
	users_with_permissions = frappe.db.sql("""
		SELECT COUNT(DISTINCT user) as count
		FROM `tabUser Permission`
	""")[0][0]
	stats["users_with_permissions"] = users_with_permissions
	
	# Most common permission types
	common_permissions = frappe.db.sql("""
		SELECT allow, COUNT(*) as count
		FROM `tabUser Permission`
		GROUP BY allow
		ORDER BY count DESC
		LIMIT 5
	""", as_dict=True)
	stats["common_permissions"] = common_permissions
	
	return stats
