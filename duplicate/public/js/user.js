// Custom script to add User Permission Manager functionality to User DocType
frappe.ui.form.on('User', {
	refresh: function(frm) {
		// Add User Permission Manager field if it doesn't exist
		if (!frm.fields_dict.user_permission_manager && !frm.is_new()) {
			// Add custom button to manage user permissions
			frm.add_custom_button(__('Manage User Permissions'), function() {
				show_user_permission_manager_dialog(frm);
			}, __('Permissions'));
			
			frm.add_custom_button(__('View Applied Managers'), function() {
				show_applied_managers(frm);
			}, __('Permissions'));
		}
		
		// Show current permission managers
		if (!frm.is_new()) {
			load_permission_managers_info(frm);
		}
	}
});

function show_user_permission_manager_dialog(frm) {
	let d = new frappe.ui.Dialog({
		title: __('Apply User Permission Manager'),
		fields: [
			{
				fieldname: 'permission_manager',
				fieldtype: 'Link',
				label: __('User Permission Manager'),
				options: 'User Permission Manager',
				reqd: 1,
				get_query: function() {
					return {
						filters: {
							'is_active': 1
						}
					};
				}
			},
			{
				fieldname: 'preview',
				fieldtype: 'Button',
				label: __('Preview Permissions')
			}
		],
		primary_action_label: __('Apply'),
		primary_action: function() {
			let values = d.get_values();
			if (values && values.permission_manager) {
				frappe.call({
					method: 'duplicate.duplicate.doctype.user_permission_manager.user_permission_manager.apply_permission_manager_to_user',
					args: {
						manager_name: values.permission_manager,
						user_email: frm.doc.name
					},
					callback: function(r) {
						if (r.message && r.message.success) {
							frappe.show_alert({
								message: r.message.message,
								indicator: 'green'
							});
							d.hide();
							// Refresh the user form to show updated info
							load_permission_managers_info(frm);
						} else {
							frappe.msgprint({
								title: __('Error'),
								message: r.message ? r.message.message : __('Failed to apply permissions'),
								indicator: 'red'
							});
						}
					}
				});
			}
		}
	});
	
	// Preview functionality
	d.fields_dict.preview.$input.click(function() {
		let manager = d.get_value('permission_manager');
		if (manager) {
			frappe.call({
				method: 'frappe.client.get',
				args: {
					doctype: 'User Permission Manager',
					name: manager
				},
				callback: function(r) {
					if (r.message) {
						show_manager_preview(r.message);
					}
				}
			});
		} else {
			frappe.msgprint(__('Please select a User Permission Manager first'));
		}
	});
	
	d.show();
}

function show_manager_preview(manager_doc) {
	let html = '<div class="manager-preview">';
	html += '<h6>' + __('Manager Details') + '</h6>';
	html += '<p><strong>' + __('Name') + ':</strong> ' + manager_doc.manager_name + '</p>';
	html += '<p><strong>' + __('Description') + ':</strong> ' + (manager_doc.description || 'No description') + '</p>';
	
	if (manager_doc.user_permission_details && manager_doc.user_permission_details.length > 0) {
		html += '<h6>' + __('Permissions to be Applied') + '</h6>';
		html += '<table class="table table-bordered table-sm">';
		html += '<thead><tr>';
		html += '<th>' + __('Allow') + '</th>';
		html += '<th>' + __('For Value') + '</th>';
		html += '<th>' + __('Applicable For') + '</th>';
		html += '</tr></thead><tbody>';
		
		manager_doc.user_permission_details.forEach(function(detail) {
			html += '<tr>';
			html += '<td>' + (detail.allow || '') + '</td>';
			html += '<td>' + (detail.for_value || '') + '</td>';
			html += '<td>' + (detail.applicable_for || 'All DocTypes') + '</td>';
			html += '</tr>';
		});
		
		html += '</tbody></table>';
	}
	
	html += '</div>';
	
	frappe.msgprint({
		title: __('Permission Manager Preview'),
		message: html,
		wide: true
	});
}

function show_applied_managers(frm) {
	frappe.call({
		method: 'duplicate.duplicate.doctype.user_permission_manager.user_permission_manager.get_user_permission_managers_for_user',
		args: {
			user_email: frm.doc.name
		},
		callback: function(r) {
			if (r.message && r.message.length > 0) {
				let html = '<div class="applied-managers">';
				html += '<h6>' + __('Applied Permission Managers') + '</h6>';
				html += '<table class="table table-bordered table-sm">';
				html += '<thead><tr>';
				html += '<th>' + __('Manager Name') + '</th>';
				html += '<th>' + __('Description') + '</th>';
				html += '<th>' + __('Action') + '</th>';
				html += '</tr></thead><tbody>';
				
				r.message.forEach(function(manager) {
					html += '<tr>';
					html += '<td>' + (manager.manager_name || 'Unknown') + '</td>';
					html += '<td>' + (manager.description || 'No description') + '</td>';
					html += '<td><a href="/app/user-permission-manager/' + manager.user_permission_manager + '" target="_blank">View</a></td>';
					html += '</tr>';
				});
				
				html += '</tbody></table></div>';
				
				frappe.msgprint({
					title: __('Applied Permission Managers'),
					message: html,
					wide: true
				});
			} else {
				frappe.msgprint(__('No permission managers applied to this user'));
			}
		}
	});
}

function load_permission_managers_info(frm) {
	// Add info section to show applied managers
	frappe.call({
		method: 'duplicate.duplicate.doctype.user_permission_manager.user_permission_manager.get_user_permission_managers_for_user',
		args: {
			user_email: frm.doc.name
		},
		callback: function(r) {
			if (r.message && r.message.length > 0) {
				let manager_names = r.message.map(m => m.manager_name || 'Unknown').join(', ');
				frm.dashboard.add_comment(
					__('Applied Permission Managers: ') + manager_names,
					'blue'
				);
			}
		}
	});
}
