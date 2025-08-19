import click
import frappe
from frappe.commands import pass_context, get_site


@click.command('duplicate-role')
@click.argument('source-role')
@click.argument('new-role-name')
@click.option('--no-permissions', is_flag=True, help='Do not copy permissions from source role')
@click.option('--site')
@pass_context
def duplicate_role(context, source_role, new_role_name, no_permissions, site):
	"""Duplicate a role with all its permissions"""
	
	site = get_site(context, site)
	
	with frappe.init_site(site):
		frappe.connect()
		
		try:
			copy_permissions = not no_permissions
			
			# Import the function
			from duplicate.api.role_utils import duplicate_role as dup_role
			
			result = dup_role(source_role, new_role_name, copy_permissions)
			
			if result['success']:
				click.echo(click.style(f"✓ {result['message']}", fg='green'))
				
				if copy_permissions:
					# Get permission count
					from duplicate.api.role_utils import get_role_details
					details = get_role_details(new_role_name)
					click.echo(f"  Copied {details['total_permissions']} permissions")
				
			else:
				click.echo(click.style(f"✗ {result['message']}", fg='red'))
				
		except Exception as e:
			click.echo(click.style(f"✗ Error: {str(e)}", fg='red'))
		
		finally:
			frappe.destroy()


@click.command('list-roles')
@click.option('--with-permissions', is_flag=True, help='Show permission counts for each role')
@click.option('--site')
@pass_context  
def list_roles(context, with_permissions, site):
	"""List all roles with their details"""
	
	site = get_site(context, site)
	
	with frappe.init_site(site):
		frappe.connect()
		
		try:
			if with_permissions:
				from duplicate.api.role_utils import get_all_roles_summary
				roles = get_all_roles_summary()
				
				click.echo("\nRoles with Permission Summary:")
				click.echo("-" * 80)
				click.echo(f"{'Role Name':<30} {'Permissions':<12} {'Desk Access':<12} {'Status':<10}")
				click.echo("-" * 80)
				
				for role in roles:
					status = "Disabled" if role['disabled'] else "Active"
					desk = "Yes" if role['desk_access'] else "No"
					click.echo(f"{role['name']:<30} {role['permission_count']:<12} {desk:<12} {status:<10}")
			else:
				roles = frappe.get_all("Role", fields=["name", "disabled", "desk_access"], order_by="name")
				
				click.echo("\nAll Roles:")
				click.echo("-" * 60)
				click.echo(f"{'Role Name':<30} {'Desk Access':<12} {'Status':<10}")
				click.echo("-" * 60)
				
				for role in roles:
					status = "Disabled" if role['disabled'] else "Active"
					desk = "Yes" if role['desk_access'] else "No"
					click.echo(f"{role['name']:<30} {desk:<12} {status:<10}")
			
		except Exception as e:
			click.echo(click.style(f"✗ Error: {str(e)}", fg='red'))
		
		finally:
			frappe.destroy()


@click.command('role-permissions')
@click.argument('role-name')
@click.option('--site')
@pass_context
def role_permissions(context, role_name, site):
	"""Show detailed permissions for a role"""
	
	site = get_site(context, site)
	
	with frappe.init_site(site):
		frappe.connect()
		
		try:
			from duplicate.api.role_utils import get_role_details
			details = get_role_details(role_name)
			
			role_data = details['role']
			click.echo(f"\nRole Details for: {role_data['role_name']}")
			click.echo("=" * 60)
			click.echo(f"Desk Access: {'Yes' if role_data['desk_access'] else 'No'}")
			click.echo(f"Two Factor Auth: {'Yes' if role_data['two_factor_auth'] else 'No'}")
			click.echo(f"Disabled: {'Yes' if role_data['disabled'] else 'No'}")
			click.echo(f"Is Custom: {'Yes' if role_data['is_custom'] else 'No'}")
			
			click.echo(f"\nPermission Summary:")
			click.echo(f"Total Permissions: {details['total_permissions']}")
			click.echo(f"DocType Permissions: {len(details['doctype_permissions'])}")
			click.echo(f"Custom Permissions: {len(details['custom_permissions'])}")
			
			if details['doctype_permissions']:
				click.echo(f"\nDocType Permissions:")
				click.echo("-" * 100)
				click.echo(f"{'DocType':<25} {'Level':<6} {'R':<2} {'W':<2} {'C':<2} {'D':<2} {'S':<2} {'Ca':<3} {'A':<2} {'Rep':<4} {'Exp':<4} {'Imp':<4} {'Owner'}")
				click.echo("-" * 100)
				
				for perm in details['doctype_permissions']:
					r = '✓' if perm['read'] else ''
					w = '✓' if perm['write'] else ''
					c = '✓' if perm['create'] else ''
					d = '✓' if perm['delete'] else ''
					s = '✓' if perm['submit'] else ''
					ca = '✓' if perm['cancel'] else ''
					a = '✓' if perm['amend'] else ''
					rep = '✓' if perm['report'] else ''
					exp = '✓' if perm['export'] else ''
					imp = '✓' if perm['import'] else ''
					owner = '✓' if perm['if_owner'] else ''
					
					click.echo(f"{perm['parent']:<25} {perm['permlevel']:<6} {r:<2} {w:<2} {c:<2} {d:<2} {s:<2} {ca:<3} {a:<2} {rep:<4} {exp:<4} {imp:<4} {owner}")
			
		except Exception as e:
			click.echo(click.style(f"✗ Error: {str(e)}", fg='red'))
		
		finally:
			frappe.destroy()


commands = [duplicate_role, list_roles, role_permissions]
