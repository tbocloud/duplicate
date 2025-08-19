// Custom script for Role DocType to add duplicate functionality
frappe.ui.form.on('Role', {
	refresh: function(frm) {
		if (!frm.is_new() && frm.perm[0] && frm.perm[0].write) {
			// Add Easy Duplicate Role button
			frm.add_custom_button(__('Easy Duplicate Role'), function() {
				duplicate_role_dialog(frm);
			}).addClass('btn-primary');
			
			// Add View Permissions Summary button
			frm.add_custom_button(__('View Permissions Summary'), function() {
				view_permissions_summary(frm);
			});
		}
	}
});

function duplicate_role_dialog(frm) {
	const d = new frappe.ui.Dialog({
		title: __('Easy Duplicate Role'),
		fields: [
			{
				fieldname: 'new_role_name',
				fieldtype: 'Data',
				label: __('New Role Name'),
				reqd: 1,
				default: frm.doc.role_name + ' Copy'
			},
			{
				fieldname: 'copy_permissions',
				fieldtype: 'Check',
				label: __('Copy all permissions'),
				default: 1
			},
			{
				fieldname: 'role_info',
				fieldtype: 'HTML',
				options: get_role_info_html(frm)
			}
		],
		primary_action_label: __('Duplicate'),
		primary_action: function() {
			const values = d.get_values();
			if (values) {
				duplicate_role(frm.doc.role_name, values.new_role_name, values.copy_permissions, d);
			}
		}
	});
	d.show();
}

function get_role_info_html(frm) {
	// Get permission count (this is approximate since we can't make server calls here)
	return `
		<div class="alert alert-info">
			<h6><strong>Source Role Details:</strong></h6>
			<p><strong>Role Name:</strong> ${frm.doc.role_name}</p>
			<p><strong>Desk Access:</strong> ${frm.doc.desk_access ? 'Yes' : 'No'}</p>
			<p><strong>Two Factor Auth:</strong> ${frm.doc.two_factor_auth ? 'Yes' : 'No'}</p>
			<p><strong>Disabled:</strong> ${frm.doc.disabled ? 'Yes' : 'No'}</p>
			<p><strong>Is Custom:</strong> ${frm.doc.is_custom ? 'Yes' : 'No'}</p>
		</div>
	`;
}

function duplicate_role(source_role, new_role_name, copy_permissions, dialog) {
	frappe.call({
		method: 'duplicate.api.role_utils.duplicate_role',
		args: {
			source_role: source_role,
			new_role_name: new_role_name,
			copy_permissions: copy_permissions
		},
		freeze: true,
		freeze_message: __('Duplicating role...'),
		callback: function(r) {
			if (r.message) {
				const result = r.message;
				if (result.success) {
					frappe.show_alert({
						message: result.message,
						indicator: 'green'
					});
					dialog.hide();
					
					// Ask if user wants to open the new role
					frappe.confirm(__('Would you like to open the newly created role?'), function() {
						frappe.set_route('Form', 'Role', result.new_role);
					});
				} else {
					frappe.msgprint({
						title: __('Error'),
						message: result.message,
						indicator: 'red'
					});
				}
			}
		}
	});
}

function view_permissions_summary(frm) {
	frappe.call({
		method: 'duplicate.api.role_utils.get_role_details',
		args: {
			role_name: frm.doc.role_name
		},
		callback: function(r) {
			if (r.message) {
				const data = r.message;
				show_permissions_dialog(data);
			}
		}
	});
}

function show_permissions_dialog(data) {
	let html = `
		<div class="permission-summary">
			<div class="row">
				<div class="col-md-6">
					<h6>Role Information</h6>
					<table class="table table-sm">
						<tr><td><strong>Role Name:</strong></td><td>${data.role.role_name}</td></tr>
						<tr><td><strong>Desk Access:</strong></td><td>${data.role.desk_access ? 'Yes' : 'No'}</td></tr>
						<tr><td><strong>Two Factor Auth:</strong></td><td>${data.role.two_factor_auth ? 'Yes' : 'No'}</td></tr>
						<tr><td><strong>Disabled:</strong></td><td>${data.role.disabled ? 'Yes' : 'No'}</td></tr>
					</table>
				</div>
				<div class="col-md-6">
					<h6>Permission Summary</h6>
					<table class="table table-sm">
						<tr><td><strong>Total Permissions:</strong></td><td>${data.total_permissions}</td></tr>
						<tr><td><strong>DocType Permissions:</strong></td><td>${data.doctype_permissions.length}</td></tr>
						<tr><td><strong>Custom Permissions:</strong></td><td>${data.custom_permissions.length}</td></tr>
					</table>
				</div>
			</div>
	`;
	
	if (data.doctype_permissions.length > 0) {
		html += `
			<hr>
			<h6>DocType Permissions</h6>
			<div class="table-responsive" style="max-height: 300px; overflow-y: auto;">
				<table class="table table-sm table-striped">
					<thead>
						<tr>
							<th>DocType</th>
							<th>Level</th>
							<th>Read</th>
							<th>Write</th>
							<th>Create</th>
							<th>Delete</th>
							<th>Submit</th>
							<th>Cancel</th>
							<th>Amend</th>
							<th>Report</th>
							<th>Export</th>
							<th>Import</th>
							<th>Print</th>
							<th>Email</th>
							<th>Share</th>
							<th>If Owner</th>
						</tr>
					</thead>
					<tbody>
		`;
		
		data.doctype_permissions.forEach(function(perm) {
			html += `
				<tr>
					<td><strong>${perm.parent}</strong></td>
					<td>${perm.permlevel || 0}</td>
					<td>${perm.read ? '✓' : ''}</td>
					<td>${perm.write ? '✓' : ''}</td>
					<td>${perm.create ? '✓' : ''}</td>
					<td>${perm.delete ? '✓' : ''}</td>
					<td>${perm.submit ? '✓' : ''}</td>
					<td>${perm.cancel ? '✓' : ''}</td>
					<td>${perm.amend ? '✓' : ''}</td>
					<td>${perm.report ? '✓' : ''}</td>
					<td>${perm.export ? '✓' : ''}</td>
					<td>${perm.import ? '✓' : ''}</td>
					<td>${perm.print ? '✓' : ''}</td>
					<td>${perm.email ? '✓' : ''}</td>
					<td>${perm.share ? '✓' : ''}</td>
					<td>${perm.if_owner ? '✓' : ''}</td>
				</tr>
			`;
		});
		
		html += `
					</tbody>
				</table>
			</div>
		`;
	}
	
	if (data.custom_permissions.length > 0) {
		html += `
			<hr>
			<h6>Custom Permissions</h6>
			<div class="table-responsive" style="max-height: 200px; overflow-y: auto;">
				<table class="table table-sm table-striped">
					<thead>
						<tr>
							<th>DocType</th>
							<th>Level</th>
							<th>Read</th>
							<th>Write</th>
							<th>Create</th>
							<th>Delete</th>
							<th>Submit</th>
							<th>Cancel</th>
							<th>Amend</th>
						</tr>
					</thead>
					<tbody>
		`;
		
		data.custom_permissions.forEach(function(perm) {
			html += `
				<tr>
					<td><strong>${perm.parent}</strong></td>
					<td>${perm.permlevel || 0}</td>
					<td>${perm.read ? '✓' : ''}</td>
					<td>${perm.write ? '✓' : ''}</td>
					<td>${perm.create ? '✓' : ''}</td>
					<td>${perm.delete ? '✓' : ''}</td>
					<td>${perm.submit ? '✓' : ''}</td>
					<td>${perm.cancel ? '✓' : ''}</td>
					<td>${perm.amend ? '✓' : ''}</td>
				</tr>
			`;
		});
		
		html += `
					</tbody>
				</table>
			</div>
		`;
	}
	
	html += `</div>`;
	
	const d = new frappe.ui.Dialog({
		title: __('Role Permissions Summary'),
		fields: [
			{
				fieldname: 'permissions_html',
				fieldtype: 'HTML',
				options: html
			}
		],
		size: 'extra-large'
	});
	
	d.show();
}
