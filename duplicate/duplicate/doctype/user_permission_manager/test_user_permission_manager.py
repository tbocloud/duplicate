# Copyright (c) 2025, sammish and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestUserPermissionManager(FrappeTestCase):
	def setUp(self):
		"""Set up test data"""
		# Create test user if not exists
		if not frappe.db.exists("User", "test@example.com"):
			user = frappe.new_doc("User")
			user.email = "test@example.com"
			user.first_name = "Test"
			user.last_name = "User"
			user.enabled = 1
			user.user_type = "System User"
			user.insert(ignore_permissions=True)
	
	def tearDown(self):
		"""Clean up test data"""
		# Delete test permission managers
		managers = frappe.get_all("User Permission Manager", 
			filters={"manager_name": ["like", "Test%"]},
			pluck="name"
		)
		for manager in managers:
			frappe.delete_doc("User Permission Manager", manager, ignore_permissions=True)
		
		# Clean up test user permissions
		permissions = frappe.get_all("User Permission",
			filters={"user": "test@example.com"},
			pluck="name"
		)
		for perm in permissions:
			frappe.delete_doc("User Permission", perm, ignore_permissions=True)
	
	def test_create_user_permission_manager(self):
		"""Test creating a User Permission Manager"""
		manager = frappe.new_doc("User Permission Manager")
		manager.manager_name = "Test Manager"
		manager.description = "Test permission manager"
		manager.user_field = "test@example.com"
		manager.is_active = 1
		
		# Add permission detail
		detail = manager.append("user_permission_details")
		detail.allow = "Company"
		detail.for_value = "_Test Company"
		detail.apply_to_all_doctypes = 1
		detail.is_default = 1
		
		manager.insert(ignore_permissions=True)
		
		self.assertTrue(frappe.db.exists("User Permission Manager", manager.name))
		self.assertEqual(len(manager.user_permission_details), 1)
	
	def test_auto_create_user_permissions(self):
		"""Test automatic creation of user permissions"""
		manager = frappe.new_doc("User Permission Manager")
		manager.manager_name = "Test Auto Manager"
		manager.user_field = "test@example.com"
		manager.is_active = 1
		
		detail = manager.append("user_permission_details")
		detail.allow = "Company"
		detail.for_value = "_Test Company"
		detail.is_default = 1
		
		manager.insert(ignore_permissions=True)
		
		# Check if user permission was created
		user_permission = frappe.db.exists("User Permission", {
			"user": "test@example.com",
			"allow": "Company",
			"for_value": "_Test Company"
		})
		
		self.assertTrue(user_permission)
	
	def test_update_user_permissions(self):
		"""Test updating user permissions when manager is modified"""
		manager = frappe.new_doc("User Permission Manager")
		manager.manager_name = "Test Update Manager"
		manager.user_field = "test@example.com"
		manager.is_active = 1
		
		detail = manager.append("user_permission_details")
		detail.allow = "Company"
		detail.for_value = "_Test Company"
		
		manager.insert(ignore_permissions=True)
		
		# Update manager with new permission
		detail2 = manager.append("user_permission_details")
		detail2.allow = "Cost Center"
		detail2.for_value = "_Test Cost Center"
		
		manager.save()
		
		# Check both permissions exist
		company_perm = frappe.db.exists("User Permission", {
			"user": "test@example.com",
			"allow": "Company",
			"for_value": "_Test Company"
		})
		
		cost_center_perm = frappe.db.exists("User Permission", {
			"user": "test@example.com",
			"allow": "Cost Center",
			"for_value": "_Test Cost Center"
		})
		
		self.assertTrue(company_perm)
		self.assertTrue(cost_center_perm)
	
	def test_delete_manager_removes_permissions(self):
		"""Test that deleting manager removes associated permissions"""
		manager = frappe.new_doc("User Permission Manager")
		manager.manager_name = "Test Delete Manager"
		manager.user_field = "test@example.com"
		manager.is_active = 1
		
		detail = manager.append("user_permission_details")
		detail.allow = "Company"
		detail.for_value = "_Test Company"
		
		manager.insert(ignore_permissions=True)
		manager_name = manager.name
		
		# Verify permission was created
		user_permission = frappe.db.exists("User Permission", {
			"user": "test@example.com",
			"allow": "Company",
			"for_value": "_Test Company"
		})
		self.assertTrue(user_permission)
		
		# Delete manager
		frappe.delete_doc("User Permission Manager", manager_name, ignore_permissions=True)
		
		# Verify permission was removed
		user_permission_after = frappe.db.exists("User Permission", {
			"user": "test@example.com", 
			"allow": "Company",
			"for_value": "_Test Company"
		})
		self.assertFalse(user_permission_after)
