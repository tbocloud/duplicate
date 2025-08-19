# Copyright (c) 2025, sammish and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class RoleDuplicate(Document):
	def validate(self):
		"""Validate the document"""
		if self.source_role and self.new_role_name:
			if self.source_role == self.new_role_name:
				frappe.throw(_("Source Role and New Role Name cannot be the same"))
			
			# Check if new role already exists
			if frappe.db.exists("Role", self.new_role_name):
				frappe.throw(_("Role '{0}' already exists").format(self.new_role_name))
		
		# Load permissions when source role is selected
		if self.source_role and not self.role_permissions:
			self.load_source_role_permissions()

	def load_source_role_permissions(self):
		"""Load permissions from the source role"""
		if not self.source_role:
			frappe.throw(_("Please select a source role first"))
		
		# Clear existing permissions
		self.role_permissions = []
		
		# Get ALL DocPerm records for the source role (not grouped)
		docperms = frappe.get_all("DocPerm", 
			filters={"role": self.source_role},
			fields=["parent", "read", "write", "create", "delete", "submit", "cancel", 
					"amend", "report", "export", "import", "print", "email", "share", "if_owner"],
			order_by="parent"
		)
		
		print(f"DEBUG: Found {len(docperms)} total DocPerm records for role '{self.source_role}'")
		
		# Create a dictionary to group permissions by DocType and combine multiple entries
		perm_dict = {}
		for perm in docperms:
			doctype = perm.parent
			if doctype not in perm_dict:
				# Initialize with current permission values
				perm_dict[doctype] = {
					"read": perm.get("read", 0),
					"write": perm.get("write", 0),
					"create": perm.get("create", 0),
					"delete": perm.get("delete", 0),
					"submit": perm.get("submit", 0),
					"cancel": perm.get("cancel", 0),
					"amend": perm.get("amend", 0),
					"report": perm.get("report", 0),
					"export": perm.get("export", 0),
					"import": perm.get("import", 0),
					"print": perm.get("print", 0),
					"email": perm.get("email", 0),
					"share": perm.get("share", 0),
					"if_owner": perm.get("if_owner", 0),
				}
			else:
				# If multiple permissions exist for same DocType, combine them (take maximum)
				existing = perm_dict[doctype]
				for field in ["read", "write", "create", "delete", "submit", "cancel", 
							"amend", "report", "export", "import", "print", "email", "share", "if_owner"]:
					if perm.get(field, 0):
						existing[field] = 1

		print(f"DEBUG: Processed into {len(perm_dict)} unique DocTypes")

		# Add permissions to child table
		for doctype, perm_data in perm_dict.items():
			self.append("role_permissions", {
				"document_type": doctype,
				"read": perm_data.get("read", 0),
				"write": perm_data.get("write", 0),
				"create": perm_data.get("create", 0),
				"delete": perm_data.get("delete", 0),
				"submit": perm_data.get("submit", 0),
				"cancel": perm_data.get("cancel", 0),
				"amend": perm_data.get("amend", 0),
				"report": perm_data.get("report", 0),
				"export": perm_data.get("export", 0),
				"import_data": perm_data.get("import", 0),
				"print": perm_data.get("print", 0),
				"email": perm_data.get("email", 0),
				"share": perm_data.get("share", 0),
				"if_owner": perm_data.get("if_owner", 0),
			})

		frappe.msgprint(_("Loaded {0} permissions from role '{1}'").format(
			len(perm_dict), self.source_role
		))

	def create_new_role(self):
		"""Create new role with permissions using proper Frappe methods"""
		try:
			# Validate inputs
			if not self.source_role or not self.new_role_name:
				frappe.throw("Source Role and New Role Name are required")
			
			# Check if role already exists
			if frappe.db.exists("Role", self.new_role_name):
				frappe.throw(f"Role '{self.new_role_name}' already exists")
			
			# Create the new role
			new_role = frappe.new_doc("Role")
			new_role.role_name = self.new_role_name
			new_role.is_custom = 1
			new_role.insert(ignore_permissions=True)
			
			# Load permissions if not already loaded
			if not self.role_permissions:
				self.load_source_role_permissions()
			
			# Create permissions using DocPerm directly
			permissions_created = 0
			failed_permissions = []
			
			for perm in self.role_permissions:
				try:
					doctype_name = perm.document_type
					
					# Check if DocType exists
					if not frappe.db.exists("DocType", doctype_name):
						failed_permissions.append(f"{doctype_name} - DocType not found")
						continue
					
					# Create DocPerm record directly
					docperm = frappe.new_doc("DocPerm")
					docperm.parent = doctype_name
					docperm.parenttype = "DocType"
					docperm.parentfield = "permissions"
					docperm.role = self.new_role_name
					docperm.read = perm.read
					docperm.write = perm.write
					docperm.create = perm.create
					docperm.delete = perm.delete
					docperm.submit = perm.submit
					docperm.cancel = perm.cancel
					docperm.amend = perm.amend
					docperm.report = perm.report
					docperm.export = getattr(perm, 'export', 0)
					docperm.import_ = getattr(perm, 'import_data', 0)
					docperm.print = getattr(perm, 'print', 0)
					docperm.email = getattr(perm, 'email', 0)
					docperm.share = getattr(perm, 'share', 0)
					docperm.if_owner = getattr(perm, 'if_owner', 0)
					
					# Insert the permission
					docperm.insert(ignore_permissions=True)
					permissions_created += 1
					
				except Exception as perm_error:
					error_msg = f"{perm.document_type} - {str(perm_error)}"
					failed_permissions.append(error_msg)
					frappe.log_error(f"Error creating permission for {perm.document_type}: {str(perm_error)}")
					continue
			
			# Clear cache to ensure permissions are immediately active
			frappe.clear_cache()
			
			frappe.db.commit()
			
			message = f"Role '{self.new_role_name}' created successfully with {permissions_created} permissions"
			if failed_permissions:
				message += f". Failed to create {len(failed_permissions)} permissions."
			
			return {
				"status": "success",
				"message": message,
				"role_name": self.new_role_name,
				"permissions_count": permissions_created,
				"failed_permissions": failed_permissions,
				"total_permissions": len(self.role_permissions)
			}
			
		except Exception as e:
			frappe.db.rollback()
			frappe.log_error(f"Error in create_new_role: {str(e)}")
			return {
				"status": "error",
				"message": f"Error creating role: {str(e)}",
				"role_name": self.new_role_name
			}


# API Methods
@frappe.whitelist()
def test_api_connection(role_duplicate_name):
	"""Simple test method to check if API connection works"""
	try:
		frappe.logger("role_duplicate").debug(f"DEBUG: test_api_connection called with role_duplicate_name: {role_duplicate_name}")
		print(f"DEBUG: test_api_connection called with role_duplicate_name: {role_duplicate_name}")
		
		if not role_duplicate_name:
			return {
				'status': 'error',
				'message': 'role_duplicate_name is required'
			}
		
		# Check if document exists
		if not frappe.db.exists("Role Duplicate", role_duplicate_name):
			return {
				'status': 'error',
				'message': f'Role Duplicate document {role_duplicate_name} not found'
			}
			
		return {
			'status': 'success',
			'message': f'API connection successful for document: {role_duplicate_name}',
			'timestamp': frappe.utils.now(),
			'user': frappe.session.user
		}
		
	except Exception as e:
		frappe.logger("role_duplicate").error(f"ERROR in test_api_connection: {str(e)}")
		frappe.logger("role_duplicate").error(f"ERROR traceback: {frappe.get_traceback()}")
		print(f"ERROR in test_api_connection: {str(e)}")
		print(f"ERROR traceback: {frappe.get_traceback()}")
		return {
			'status': 'error',
			'message': f'API test failed: {str(e)}'
		}

@frappe.whitelist()
def load_role_permissions(source_role, role_duplicate_name):
	"""Load permissions from source role into role duplicate document"""
	try:
		doc = frappe.get_doc("Role Duplicate", role_duplicate_name)
		doc.source_role = source_role
		doc.load_source_role_permissions()
		doc.save()
		return {"status": "success", "permissions_count": len(doc.role_permissions)}
	except Exception as e:
		frappe.log_error(f"Error loading permissions: {str(e)}")
		return {"status": "error", "message": str(e)}

@frappe.whitelist()
def create_role_from_duplicate(role_duplicate_name):
	"""Create new role from role duplicate document"""
	try:
		print(f"DEBUG: API create_role_from_duplicate called for document: {role_duplicate_name}")
		print(f"DEBUG: Current user: {frappe.session.user}")
		
		# Check if document exists
		if not frappe.db.exists("Role Duplicate", role_duplicate_name):
			return {"status": "error", "message": f"Document {role_duplicate_name} does not exist"}
		
		doc = frappe.get_doc("Role Duplicate", role_duplicate_name)
		print(f"DEBUG: Document loaded - source_role: {doc.source_role}, new_role_name: {doc.new_role_name}")
		print(f"DEBUG: Role permissions count: {len(doc.role_permissions)}")
		
		# Check if new role name is provided
		if not doc.new_role_name:
			return {"status": "error", "message": "New role name is required"}
		
		# Check if role already exists
		if frappe.db.exists("Role", doc.new_role_name):
			return {"status": "error", "message": f"Role '{doc.new_role_name}' already exists"}
		
		result = doc.create_new_role()
		print(f"DEBUG: API create result: {result}")
		return result
	except Exception as e:
		frappe.log_error(f"Error creating role: {str(e)}")
		print(f"DEBUG: API Error: {str(e)}")
		import traceback
		print(f"DEBUG: Traceback: {traceback.format_exc()}")
		return {"status": "error", "message": str(e)}

@frappe.whitelist()
def test_doctype_permissions(source_role):
	"""Test function to check DocType permissions for a role"""
	try:
		# Get all DocTypes that have permissions for the source role
		docperms = frappe.get_all("DocPerm", 
			filters={"role": source_role},
			fields=["parent", "read", "write", "create", "delete", "submit", "cancel", 
					"amend", "report", "export", "import", "print", "email", "share", "if_owner"]
		)
		
		# Group by DocType
		perm_dict = {}
		for perm in docperms:
			doctype = perm.parent
			if doctype not in perm_dict:
				perm_dict[doctype] = []
			perm_dict[doctype].append(perm)
		
		# Test creating permissions for a specific DocType (Employee)
		test_results = []
		test_doctype = "Employee"
		
		if test_doctype in perm_dict:
			try:
				# Get the DocType document
				doctype_doc = frappe.get_doc("DocType", test_doctype)
				
				# Find permissions for the source role
				source_perms = [p for p in doctype_doc.permissions if p.role == source_role]
				
				test_results.append({
					"doctype": test_doctype,
					"source_permissions_count": len(source_perms),
					"docperm_records": len(perm_dict[test_doctype]),
					"can_modify": not doctype_doc.issingle and not doctype_doc.istable,
					"is_custom": doctype_doc.custom
				})
				
			except Exception as e:
				test_results.append({
					"doctype": test_doctype,
					"error": str(e)
				})
		
		return {
			"status": "success",
			"total_doctypes": len(perm_dict),
			"total_permissions": len(docperms),
			"test_results": test_results,
			"sample_doctypes": list(perm_dict.keys())[:10]
		}
		
	except Exception as e:
		frappe.log_error(f"Error in test_doctype_permissions: {str(e)}")
		return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_role_permissions_preview(source_role):
	"""Get a preview of permissions for a source role"""
	try:
		# Get ALL DocPerm records for the source role (not grouped) 
		docperms = frappe.get_all("DocPerm", 
			filters={"role": source_role},
			fields=["parent", "read", "write", "create", "delete", "submit", "cancel", 
					"amend", "report", "export", "import", "print", "email", "share", "if_owner"],
			order_by="parent"
		)
		
		print(f"DEBUG: get_role_permissions_preview found {len(docperms)} DocPerm records for '{source_role}'")
		
		# Group by DocType and combine permissions
		perm_dict = {}
		for perm in docperms:
			doctype = perm.parent
			if doctype not in perm_dict:
				perm_dict[doctype] = {
					"document_type": doctype,
					"read": perm.get("read", 0), 
					"write": perm.get("write", 0), 
					"create": perm.get("create", 0), 
					"delete": perm.get("delete", 0),
					"submit": perm.get("submit", 0), 
					"cancel": perm.get("cancel", 0), 
					"amend": perm.get("amend", 0), 
					"report": perm.get("report", 0),
					"export": perm.get("export", 0), 
					"import_data": perm.get("import", 0), 
					"print": perm.get("print", 0), 
					"email": perm.get("email", 0),
					"share": perm.get("share", 0), 
					"if_owner": perm.get("if_owner", 0)
				}
			else:
				# Combine permissions (take maximum)
				existing = perm_dict[doctype]
				for field in ["read", "write", "create", "delete", "submit", "cancel", 
							"amend", "report", "export", "print", "email", "share", "if_owner"]:
					if perm.get(field, 0):
						key = "import_data" if field == "import" else field
						existing[key] = 1
		
		permissions_list = list(perm_dict.values())
		
		return {
			"status": "success",
			"permissions": permissions_list,
			"total_count": len(permissions_list)
		}
		
	except Exception as e:
		frappe.log_error(f"Error in get_role_permissions_preview: {str(e)}")
		return {"status": "error", "message": str(e)}