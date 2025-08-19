// Copyright (c) 2025, sammish and contributors
// For license information, please see license.txt

frappe.ui.form.on('User Permission Manager', {
	refresh: function(frm) {
		// Add custom buttons
		if (!frm.is_new()) {
			frm.add_custom_button(__('Apply to User'), function() {
				apply_to_user_direct(frm);
			});
			
			frm.add_custom_button(__('Preview Permissions'), function() {
				preview_permissions(frm);
			});
			
			frm.add_custom_button(__('Sync User'), function() {
				sync_user(frm);
			});
			
			frm.add_custom_button(__('Check Missing Permissions'), function() {
				check_missing_permissions(frm);
			});
		}
	},
	
	user_field: function(frm) {
		if (frm.doc.user_field && frm.doc.is_active && frm.doc.user_permission_details.length > 0) {
			// Auto-apply permissions when user is selected
			if (!frm.is_new()) {
				apply_to_user_direct(frm, true); // Silent apply
			}
		}
	},
	
	is_active: function(frm) {
		if (frm.doc.is_active && frm.doc.user_permission_details.length > 0 && frm.doc.user_field) {
			frappe.confirm(__('Do you want to sync permissions now?'), function() {
				frm.save();
			});
		}
	}
});

frappe.ui.form.on('User Permission Details', {
	allow: function(frm, cdt, cdn) {
		// Clear for_value when allow changes
		frappe.model.set_value(cdt, cdn, 'for_value', '');
	},
	
	apply_to_all_doctypes: function(frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		if (row.apply_to_all_doctypes) {
			frappe.model.set_value(cdt, cdn, 'applicable_for', '');
		}
	},
	
	applicable_for: function(frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		if (row.applicable_for) {
			frappe.model.set_value(cdt, cdn, 'apply_to_all_doctypes', 0);
		}
	}
});

function apply_to_user_direct(frm, silent = false) {
	if (!frm.doc.user_field) {
		frappe.msgprint(__('Please select an Applied User first'));
		return;
	}
	
	if (!frm.doc.is_active) {
		frappe.msgprint(__('Permission Manager must be active to apply permissions'));
		return;
	}
	
	if (!frm.doc.user_permission_details || frm.doc.user_permission_details.length === 0) {
		frappe.msgprint(__('Please add permission details first'));
		return;
	}
	
	frappe.call({
		method: 'duplicate.duplicate.doctype.user_permission_manager.user_permission_manager.apply_permission_manager_to_user',
		args: {
			manager_name: frm.doc.name,
			user_email: frm.doc.user_field
		},
		freeze: !silent,
		freeze_message: silent ? '' : __('Applying permissions...'),
		callback: function(r) {
			if (r.message && r.message.success) {
				if (!silent) {
					frappe.show_alert({
						message: __('Permissions applied successfully to {0}', [frm.doc.user_field]),
						indicator: 'green'
					});
				}
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

function preview_permissions(frm) {
	if (!frm.doc.user_permission_details || frm.doc.user_permission_details.length === 0) {
		frappe.msgprint(__('No permission details to preview'));
		return;
	}
	
	let html = '<div class="permission-preview">';
	html += '<h5>' + __('Permission Details Preview') + '</h5>';
	html += '<table class="table table-bordered table-sm">';
	html += '<thead><tr>';
	html += '<th>' + __('Allow') + '</th>';
	html += '<th>' + __('For Value') + '</th>';
	html += '<th>' + __('Applicable For') + '</th>';
	html += '<th>' + __('Apply to All') + '</th>';
	html += '<th>' + __('Is Default') + '</th>';
	html += '</tr></thead><tbody>';
	
	frm.doc.user_permission_details.forEach(function(detail) {
		html += '<tr>';
		html += '<td>' + (detail.allow || '') + '</td>';
		html += '<td>' + (detail.for_value || '') + '</td>';
		html += '<td>' + (detail.applicable_for || 'All') + '</td>';
		html += '<td>' + (detail.apply_to_all_doctypes ? 'Yes' : 'No') + '</td>';
		html += '<td>' + (detail.is_default ? 'Yes' : 'No') + '</td>';
		html += '</tr>';
	});
	
	html += '</tbody></table>';
	
	if (frm.doc.user_field) {
		html += '<p><strong>' + __('Target User') + ':</strong> ' + frm.doc.user_field + '</p>';
	}
	if (frm.doc.apply_to_all_users) {
		html += '<p><strong>' + __('Target') + ':</strong> All System Users</p>';
	}
	
	html += '</div>';
	
	frappe.msgprint({
		title: __('Permission Preview'),
		message: html,
		wide: true
	});
}

function sync_user(frm) {
	if (!frm.doc.is_active) {
		frappe.msgprint(__('Permission Manager must be active to sync user'));
		return;
	}
	
	if (!frm.doc.user_field) {
		frappe.msgprint(__('Please select an Applied User first'));
		return;
	}
	
	frappe.confirm(
		__('This will sync permissions for {0}. Continue?', [frm.doc.user_field]),
		function() {
			apply_to_user_direct(frm);
		}
	);
}

function check_missing_permissions(frm) {
	if (!frm.doc.is_active) {
		frappe.msgprint(__('Permission Manager must be active to check permissions'));
		return;
	}
	
	if (!frm.doc.user_field) {
		frappe.msgprint(__('Please select an Applied User first'));
		return;
	}
	
	frappe.call({
		method: 'duplicate.duplicate.doctype.user_permission_manager.user_permission_manager.check_missing_permissions',
		args: {
			manager_name: frm.doc.name
		},
		freeze: true,
		freeze_message: __('Checking for missing permissions...'),
		callback: function(r) {
			if (r.message) {
				if (r.message.missing_count > 0) {
					frappe.confirm(
						__('Found {0} missing permissions. Do you want to recreate them?', [r.message.missing_count]),
						function() {
							frappe.call({
								method: 'duplicate.duplicate.doctype.user_permission_manager.user_permission_manager.recreate_missing_permissions',
								args: {
									manager_name: frm.doc.name
								},
								freeze: true,
								freeze_message: __('Recreating permissions...'),
								callback: function(r) {
									if (r.message && r.message.success) {
										frappe.show_alert({
											message: __('Missing permissions recreated successfully'),
											indicator: 'green'
										});
									}
								}
							});
						}
					);
				} else {
					frappe.show_alert({
						message: __('No missing permissions found'),
						indicator: 'green'
					});
				}
			}
		}
	});
}
