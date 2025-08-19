# Copyright (c) 2025, sammish and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _


class UserPermissionManager(Document):
	def validate(self):
		"""Validate the User Permission Manager"""
		if not self.user_permission_details:
			frappe.throw(_("Please add at least one User Permission Detail"))
		
		# Validate duplicate entries
		seen_combinations = set()
		for detail in self.user_permission_details:
			combination = (detail.allow, detail.for_value, detail.applicable_for or "")
			if combination in seen_combinations:
				frappe.throw(_("Duplicate permission entry found for {0} - {1}").format(
					detail.allow, detail.for_value
				))
			seen_combinations.add(combination)
		
		# Check for missing permissions if manager is active
		if self.is_active and not self.is_new():
			self.check_and_recreate_missing_permissions()
	
	def on_update(self):
		"""Handle updates to User Permission Manager"""
		if self.has_value_changed('user_field') or self.has_value_changed('user_permission_details'):
			self.sync_user_permissions()
	
	def sync_user_permissions(self):
		"""Sync user permissions based on the manager configuration"""
		if not self.is_active:
			return
		
		# Get target users
		target_users = self.get_target_users()
		
		if not target_users:
			return
		
		for user in target_users:
			self.create_user_permissions_for_user(user)
	
	def get_target_users(self):
		"""Get list of users to apply permissions to"""
		target_users = []
		
		if self.user_field:
			target_users.append(self.user_field)
		
		return target_users
	
	def create_user_permissions_for_user(self, user):
		"""Create user permissions for a specific user"""
		# Remove existing permissions managed by this manager
		self.remove_existing_managed_permissions(user)
		
		# Create new permissions
		for detail in self.user_permission_details:
			if detail.allow and detail.for_value:
				try:
					self.create_user_permission(user, detail)
				except Exception as e:
					frappe.log_error(
						title="User Permission Creation Failed",
						message=f"Failed to create permission for user {user}: {str(e)}"
					)
	
	def create_user_permission(self, user, detail):
		"""Create a single user permission"""
		# Check if permission already exists
		existing = frappe.db.exists("User Permission", {
			"user": user,
			"allow": detail.allow,
			"for_value": detail.for_value,
			"applicable_for": detail.applicable_for or None
		})
		
		if existing:
			# Update existing permission
			perm_doc = frappe.get_doc("User Permission", existing)
			perm_doc.apply_to_all = 1 if detail.apply_to_all_doctypes else 0
			perm_doc.is_default = 1 if detail.is_default else 0
			perm_doc.hide_descendants = 1 if detail.hide_descendants else 0
			perm_doc.user_permission_manager = self.name  # Track which manager created this
			perm_doc.save(ignore_permissions=True)
		else:
			# Create new permission
			perm_doc = frappe.new_doc("User Permission")
			perm_doc.user = user
			perm_doc.allow = detail.allow
			perm_doc.for_value = detail.for_value
			
			if detail.applicable_for:
				perm_doc.applicable_for = detail.applicable_for
			
			perm_doc.apply_to_all = 1 if detail.apply_to_all_doctypes else 0
			perm_doc.is_default = 1 if detail.is_default else 0
			perm_doc.hide_descendants = 1 if detail.hide_descendants else 0
			perm_doc.user_permission_manager = self.name  # Track which manager created this
			
			perm_doc.insert(ignore_permissions=True)
		
		frappe.db.commit()
	
	def remove_existing_managed_permissions(self, user):
		"""Remove existing permissions managed by this manager"""
		# First, add custom field to User Permission if it doesn't exist
		self.ensure_user_permission_custom_field()
		
		existing_permissions = frappe.get_all("User Permission", 
			filters={
				"user": user,
				"user_permission_manager": self.name
			},
			pluck="name"
		)
		
		for perm_name in existing_permissions:
			frappe.delete_doc("User Permission", perm_name, ignore_permissions=True)
	
	def ensure_user_permission_custom_field(self):
		"""Ensure User Permission DocType has the custom field for tracking"""
		if not frappe.db.exists("Custom Field", {
			"dt": "User Permission",
			"fieldname": "user_permission_manager"
		}):
			custom_field = frappe.new_doc("Custom Field")
			custom_field.dt = "User Permission"
			custom_field.fieldname = "user_permission_manager"
			custom_field.label = "User Permission Manager"
			custom_field.fieldtype = "Link"
			custom_field.options = "User Permission Manager"
			custom_field.hidden = 1
			custom_field.insert(ignore_permissions=True)
	
	def on_trash(self):
		"""Clean up user permissions when manager is deleted"""
		self.ensure_user_permission_custom_field()
		
		# Remove all permissions created by this manager
		permissions_to_delete = frappe.get_all("User Permission",
			filters={"user_permission_manager": self.name},
			pluck="name"
		)
		
		for perm_name in permissions_to_delete:
			frappe.delete_doc("User Permission", perm_name, ignore_permissions=True)

	def check_and_recreate_missing_permissions(self):
		"""Check for manually deleted permissions and recreate them if manager is active"""
		if not self.is_active or not self.user_field:
			return

		missing_permissions = []
		users = self.get_target_users()
		
		for user in users:
			for detail in self.user_permission_details:
				# Check if permission exists
				existing = frappe.db.exists("User Permission", {
					"user": user,
					"allow": detail.allow,
					"for_value": detail.for_value,
					"applicable_for": detail.applicable_for or None,
					"user_permission_manager": self.name
				})
				
				if not existing:
					missing_permissions.append({
						"user": user,
						"allow": detail.allow,
						"for_value": detail.for_value,
						"applicable_for": detail.applicable_for
					})
		
		# Recreate missing permissions
		if missing_permissions:
			for user in users:
				self.create_user_permissions_for_user(user)
			
			frappe.msgprint(
				_("Detected {0} missing permissions and recreated them").format(len(missing_permissions)),
				indicator="orange"
			)


@frappe.whitelist()
def apply_permission_manager_to_user(manager_name, user_email):
	"""API method to apply a permission manager to a specific user"""
	if not frappe.has_permission("User Permission Manager", "write"):
		frappe.throw(_("Insufficient permissions"))
	
	manager_doc = frappe.get_doc("User Permission Manager", manager_name)
	if manager_doc.is_active:
		manager_doc.create_user_permissions_for_user(user_email)
		return {
			"success": True,
			"message": _("Permissions applied successfully to user {0}").format(user_email)
		}
	else:
		return {
			"success": False,
			"message": _("User Permission Manager is not active")
		}


@frappe.whitelist()
def get_user_permission_managers_for_user(user_email):
	"""Get all permission managers applied to a user"""
	# First ensure custom field exists
	doc = frappe.new_doc("User Permission Manager")
	doc.ensure_user_permission_custom_field()
	
	managers = frappe.db.sql("""
		SELECT DISTINCT up.user_permission_manager, upm.manager_name, upm.description
		FROM `tabUser Permission` up
		LEFT JOIN `tabUser Permission Manager` upm ON up.user_permission_manager = upm.name
		WHERE up.user = %s AND up.user_permission_manager IS NOT NULL
	""", (user_email,), as_dict=True)
	
	return managers


@frappe.whitelist()
def check_missing_permissions(manager_name):
	"""Check for missing User Permissions that were manually deleted"""
	if not frappe.has_permission("User Permission Manager", "read"):
		frappe.throw(_("Insufficient permissions"))
	
	manager_doc = frappe.get_doc("User Permission Manager", manager_name)
	if not manager_doc.is_active or not manager_doc.user_field:
		return {"missing_count": 0, "message": _("Manager is not active or no user assigned")}
	
	missing_count = 0
	users = manager_doc.get_target_users()
	
	for user in users:
		for detail in manager_doc.user_permission_details:
			# Check if permission exists
			existing = frappe.db.exists("User Permission", {
				"user": user,
				"allow": detail.allow,
				"for_value": detail.for_value,
				"applicable_for": detail.applicable_for or None,
				"user_permission_manager": manager_name
			})
			
			if not existing:
				missing_count += 1
	
	return {
		"missing_count": missing_count,
		"message": _("Found {0} missing permissions").format(missing_count) if missing_count > 0 else _("No missing permissions")
	}


@frappe.whitelist()
def recreate_missing_permissions(manager_name):
	"""Recreate missing User Permissions"""
	if not frappe.has_permission("User Permission Manager", "write"):
		frappe.throw(_("Insufficient permissions"))
	
	manager_doc = frappe.get_doc("User Permission Manager", manager_name)
	if manager_doc.is_active and manager_doc.user_field:
		manager_doc.check_and_recreate_missing_permissions()
		return {"success": True, "message": _("Missing permissions recreated successfully")}
	else:
		return {"success": False, "message": _("Manager is not active or no user assigned")}


def prevent_managed_permission_deletion(doc, method):
	"""Prevent deletion of User Permissions that are managed by a Permission Manager"""
	if doc.user_permission_manager:
		# Check if the manager is still active
		manager_doc = frappe.get_doc("User Permission Manager", doc.user_permission_manager)
		if manager_doc.is_active:
			frappe.throw(
				_("This User Permission is managed by '{0}' and cannot be deleted manually. Please deactivate or modify the Permission Manager instead.").format(
					manager_doc.alias_name or manager_doc.name
				),
				title=_("Managed Permission")
			)
