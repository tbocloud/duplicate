import frappe
from frappe import _


def create_sample_permission_managers():
	"""
	Create sample User Permission Managers to demonstrate functionality
	"""
	
	# Ensure test users exist
	test_users = [
		{"email": "manager@example.com", "first_name": "Test", "last_name": "Manager"},
		{"email": "employee@example.com", "first_name": "Test", "last_name": "Employee"},
		{"email": "admin@example.com", "first_name": "Test", "last_name": "Admin"}
	]
	
	for user_data in test_users:
		if not frappe.db.exists("User", user_data["email"]):
			user = frappe.new_doc("User")
			user.email = user_data["email"]
			user.first_name = user_data["first_name"]
			user.last_name = user_data["last_name"]
			user.enabled = 1
			user.user_type = "System User"
			user.insert(ignore_permissions=True)
			print(f"Created test user: {user_data['email']}")
	
	# Sample Permission Managers
	sample_managers = [
		{
			"manager_name": "Company Access Manager",
			"description": "Manages company-specific access permissions",
			"user_field": "manager@example.com",
			"permissions": [
				{
					"allow": "Company",
					"for_value": "_Test Company",
					"apply_to_all_doctypes": 1,
					"is_default": 1
				},
				{
					"allow": "Cost Center",
					"for_value": "_Test Cost Center",
					"apply_to_all_doctypes": 1,
					"is_default": 0
				}
			]
		},
		{
			"manager_name": "Department Access Manager",
			"description": "Manages department-specific permissions",
			"user_field": "employee@example.com",
			"permissions": [
				{
					"allow": "Department",
					"for_value": "_Test Department",
					"applicable_for": "Employee",
					"apply_to_all_doctypes": 0,
					"is_default": 1
				}
			]
		},
		{
			"manager_name": "Global Admin Manager",
			"description": "Global permissions for admin users",
			"apply_to_all_users": 1,
			"permissions": [
				{
					"allow": "Company",
					"for_value": "_Test Company",
					"apply_to_all_doctypes": 1,
					"is_default": 1
				}
			]
		}
	]
	
	for manager_data in sample_managers:
		manager_name = manager_data["manager_name"]
		
		if not frappe.db.exists("User Permission Manager", {"manager_name": manager_name}):
			manager = frappe.new_doc("User Permission Manager")
			manager.manager_name = manager_data["manager_name"]
			manager.description = manager_data["description"]
			
			if "user_field" in manager_data:
				manager.user_field = manager_data["user_field"]
			
			if manager_data.get("apply_to_all_users"):
				manager.apply_to_all_users = 1
			
			manager.is_active = 1
			
			# Add permission details
			for perm_data in manager_data["permissions"]:
				detail = manager.append("user_permission_details")
				detail.allow = perm_data["allow"]
				detail.for_value = perm_data["for_value"]
				
				if "applicable_for" in perm_data:
					detail.applicable_for = perm_data["applicable_for"]
				
				detail.apply_to_all_doctypes = perm_data.get("apply_to_all_doctypes", 0)
				detail.is_default = perm_data.get("is_default", 0)
			
			manager.insert(ignore_permissions=True)
			print(f"Created User Permission Manager: {manager_name}")
		else:
			print(f"User Permission Manager already exists: {manager_name}")
	
	frappe.db.commit()


def demonstrate_permission_manager():
	"""
	Demonstrate User Permission Manager functionality
	"""
	print("\n" + "="*60)
	print("USER PERMISSION MANAGER DEMONSTRATION")
	print("="*60)
	
	# Create sample data
	create_sample_permission_managers()
	
	# Show created managers
	print("\n1. Created Permission Managers:")
	print("-" * 30)
	
	managers = frappe.get_all("User Permission Manager",
		fields=["name", "manager_name", "description", "is_active", "user_field", "apply_to_all_users"],
		order_by="manager_name"
	)
	
	for manager in managers:
		print(f"  • {manager.manager_name}")
		print(f"    Description: {manager.description}")
		if manager.user_field:
			print(f"    Target User: {manager.user_field}")
		elif manager.apply_to_all_users:
			print(f"    Target: All Users")
		print(f"    Status: {'Active' if manager.is_active else 'Inactive'}")
		
		# Show permission details
		details = frappe.get_all("User Permission Details",
			filters={"parent": manager.name},
			fields=["allow", "for_value", "applicable_for", "apply_to_all_doctypes", "is_default"]
		)
		
		print(f"    Permissions ({len(details)}):")
		for detail in details:
			applicable = detail.applicable_for or "All DocTypes"
			default = " (Default)" if detail.is_default else ""
			print(f"      - {detail.allow}: {detail.for_value} → {applicable}{default}")
		print()
	
	# Show created user permissions
	print("\n2. Auto-Created User Permissions:")
	print("-" * 35)
	
	permissions = frappe.db.sql("""
		SELECT up.user, up.allow, up.for_value, up.applicable_for, up.is_default,
			   upm.manager_name
		FROM `tabUser Permission` up
		LEFT JOIN `tabUser Permission Manager` upm ON up.user_permission_manager = upm.name
		WHERE up.user_permission_manager IS NOT NULL
		ORDER BY up.user, up.allow
	""", as_dict=True)
	
	current_user = None
	for perm in permissions:
		if perm.user != current_user:
			current_user = perm.user
			print(f"\n  User: {current_user}")
		
		applicable = perm.applicable_for or "All"
		default = " (Default)" if perm.is_default else ""
		manager = perm.manager_name or "Unknown Manager"
		print(f"    • {perm.allow}: {perm.for_value} → {applicable}{default}")
		print(f"      Source: {manager}")
	
	print(f"\n  Total managed permissions: {len(permissions)}")
	
	# Demonstrate API functions
	print("\n3. API Demonstration:")
	print("-" * 20)
	
	from duplicate.api.user_permission_utils import get_permission_statistics
	stats = get_permission_statistics()
	
	print(f"  • Total Permission Managers: {stats['total_managers']}")
	print(f"  • Active Permission Managers: {stats['active_managers']}")
	print(f"  • Total User Permissions: {stats['total_permissions']}")
	print(f"  • Managed Permissions: {stats['managed_permissions']}")
	print(f"  • Manual Permissions: {stats['manual_permissions']}")
	print(f"  • Users with Permissions: {stats['users_with_permissions']}")
	
	print("\n4. Usage Examples:")
	print("-" * 18)
	print("  • Web Interface: Visit /user-permission-manager")
	print("  • User Form: Go to any User → Permissions → Manage User Permissions")
	print("  • DocType Form: Go to User Permission Manager documents")
	print("  • API: Use functions in duplicate.api.user_permission_utils")
	
	print("\n" + "="*60)
	print("DEMONSTRATION COMPLETE")
	print("="*60)


if __name__ == "__main__":
	demonstrate_permission_manager()
