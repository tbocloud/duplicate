import frappe
from frappe import _


def create_sample_roles():
	"""
	Create sample roles to demonstrate duplication functionality
	This is useful for testing and demonstration purposes
	"""
	
	sample_roles = [
		{
			"role_name": "Academic Administrator",
			"desk_access": 1,
			"permissions": [
				{"doctype": "User", "read": 1, "write": 1, "create": 1},
				{"doctype": "Role", "read": 1, "write": 1},
				{"doctype": "Student", "read": 1, "write": 1, "create": 1, "delete": 1},
				{"doctype": "Course", "read": 1, "write": 1, "create": 1},
			]
		},
		{
			"role_name": "Faculty Member", 
			"desk_access": 1,
			"permissions": [
				{"doctype": "Student", "read": 1, "write": 1},
				{"doctype": "Course", "read": 1, "write": 1},
				{"doctype": "Grade", "read": 1, "write": 1, "create": 1},
			]
		},
		{
			"role_name": "Department Head",
			"desk_access": 1, 
			"permissions": [
				{"doctype": "User", "read": 1, "write": 1},
				{"doctype": "Student", "read": 1, "write": 1, "create": 1},
				{"doctype": "Course", "read": 1, "write": 1, "create": 1, "delete": 1},
				{"doctype": "Grade", "read": 1, "write": 1, "create": 1},
			]
		}
	]
	
	for role_data in sample_roles:
		if not frappe.db.exists("Role", role_data["role_name"]):
			# Create role
			role_doc = frappe.new_doc("Role")
			role_doc.role_name = role_data["role_name"]
			role_doc.desk_access = role_data.get("desk_access", 0)
			role_doc.is_custom = 1
			role_doc.insert(ignore_permissions=True)
			
			print(f"Created role: {role_data['role_name']}")
		else:
			print(f"Role already exists: {role_data['role_name']}")
	
	frappe.db.commit()


def demonstrate_role_duplication():
	"""
	Demonstrate the role duplication functionality
	"""
	from duplicate.api.role_utils import duplicate_role, get_role_details
	
	print("\n" + "="*60)
	print("ROLE DUPLICATION DEMONSTRATION")
	print("="*60)
	
	# Ensure sample roles exist
	create_sample_roles()
	
	# Example 1: Basic role duplication
	print("\n1. Basic Role Duplication:")
	print("-" * 30)
	
	result = duplicate_role(
		source_role="Academic Administrator",
		new_role_name="Academic Administrator Copy",
		copy_permissions=True
	)
	
	print(f"Result: {result['message']}")
	
	if result['success']:
		# Show details of the new role
		details = get_role_details("Academic Administrator Copy")
		print(f"New role has {details['total_permissions']} permissions")
	
	# Example 2: Role without permissions
	print("\n2. Role Duplication Without Permissions:")
	print("-" * 40)
	
	result = duplicate_role(
		source_role="Faculty Member",
		new_role_name="Junior Faculty",
		copy_permissions=False
	)
	
	print(f"Result: {result['message']}")
	
	# Example 3: Bulk duplication
	print("\n3. Bulk Role Duplication:")
	print("-" * 25)
	
	from duplicate.api.role_utils import bulk_duplicate_roles
	
	bulk_data = [
		{
			"source_role": "Department Head",
			"new_role_name": "Assistant Department Head",
			"copy_permissions": True
		},
		{
			"source_role": "Faculty Member", 
			"new_role_name": "Senior Faculty",
			"copy_permissions": True
		}
	]
	
	bulk_result = bulk_duplicate_roles(bulk_data)
	
	for result in bulk_result['results']:
		print(f"  {result['source_role']} → {result['new_role_name']}: {result['result']['message']}")
	
	# Example 4: Show role summary
	print("\n4. Role Summary:")
	print("-" * 15)
	
	from duplicate.api.role_utils import get_all_roles_summary
	
	roles = get_all_roles_summary()
	custom_roles = [r for r in roles if r.get('is_custom')]
	
	print(f"{'Role Name':<30} {'Permissions':<12} {'Desk Access':<12}")
	print("-" * 55)
	
	for role in custom_roles:
		desk = "Yes" if role['desk_access'] else "No"
		print(f"{role['name']:<30} {role['permission_count']:<12} {desk:<12}")
	
	print(f"\nTotal custom roles: {len(custom_roles)}")
	print("="*60)


if __name__ == "__main__":
	# Run this script to demonstrate functionality
	demonstrate_role_duplication()
