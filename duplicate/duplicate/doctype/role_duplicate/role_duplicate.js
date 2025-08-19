// Copyright (c) 2025, sammish and contributors
// For license information, please see license.txt

frappe.ui.form.on('Role Duplicate', {
	refresh: function(frm) {
		// Add custom buttons - show even for new documents
		if (frm.doc.source_role) {
			frm.add_custom_button(__('Load Permissions'), function() {
				load_source_permissions(frm);
			});
			
			frm.add_custom_button(__('Preview Source Role'), function() {
				preview_source_role(frm);
			});
		}
		
		if (!frm.is_new() && frm.doc.role_permissions && frm.doc.role_permissions.length > 0) {
			frm.add_custom_button(__('Create New Role'), function() {
				create_new_role(frm);
			});
		}
		
		// Style the create role button
		if (frm.doc.role_permissions && frm.doc.role_permissions.length > 0) {
			frm.get_field('create_role_button').df.options = 'Create New Role';
		}
	},
	
	source_role: function(frm) {
		// Refresh to show the buttons
		frm.refresh();
		
		// Auto-suggest new role name
		if (frm.doc.source_role && !frm.doc.new_role_name) {
			let suggested_name = frm.doc.source_role + ' Copy';
			frm.set_value('new_role_name', suggested_name);
		}
		
		// Auto-load permissions if document is saved and user confirms
		if (frm.doc.source_role && !frm.is_new()) {
			frappe.confirm(__('Load permissions from role "{0}"?', [frm.doc.source_role]), function() {
				load_source_permissions(frm);
			});
		}
	},
	
	new_role_name: function(frm) {
		// Check if role already exists
		if (frm.doc.new_role_name) {
			frappe.db.exists('Role', frm.doc.new_role_name).then(exists => {
				if (exists) {
					frappe.msgprint({
						title: __('Role Already Exists'),
						message: __('A role with name "{0}" already exists. Please choose a different name.', [frm.doc.new_role_name]),
						indicator: 'orange'
					});
				}
			});
		}
	}
});

function load_source_permissions(frm) {
	if (!frm.doc.source_role) {
		frappe.msgprint(__('Please select a source role first'));
		return;
	}
	
	console.log('DEBUG: Loading permissions for role:', frm.doc.source_role);
	
	frappe.call({
		method: 'duplicate.duplicate.doctype.role_duplicate.role_duplicate.load_role_permissions',
		args: {
			source_role: frm.doc.source_role,
			role_duplicate_name: frm.doc.name
		},
		callback: function(r) {
			console.log('DEBUG: Load permissions response:', r);
			if (r.message && r.message.status === 'success') {
				frappe.msgprint(__('Loaded {0} permissions from role "{1}"', [r.message.permissions_count, frm.doc.source_role]));
				frm.reload_doc();
			} else {
				frappe.msgprint(__('Error loading permissions: {0}', [r.message.message || 'Unknown error']));
			}
		}
	});
}

function preview_source_role(frm) {
	if (!frm.doc.source_role) {
		frappe.msgprint(__('Please select a source role first'));
		return;
	}
	
	frappe.set_route('Form', 'Role', frm.doc.source_role);
}

function create_new_role(frm) {
	if (!frm.doc.new_role_name) {
		frappe.msgprint(__('Please specify the new role name'));
		return;
	}
	
	if (!frm.doc.role_permissions || frm.doc.role_permissions.length === 0) {
		frappe.msgprint(__('No permissions loaded. Please load permissions first'));
		return;
	}

	console.log('DEBUG: UI create_new_role called');
	console.log('DEBUG: Document name:', frm.doc.name);
	console.log('DEBUG: New role name:', frm.doc.new_role_name);
	console.log('DEBUG: Permissions count:', frm.doc.role_permissions.length);
	
	frappe.confirm(
		__('Create new role "{0}" with {1} permissions?', [frm.doc.new_role_name, frm.doc.role_permissions.length]),
		function() {
			console.log('DEBUG: User confirmed role creation');
			
			// Save document if needed
			if (frm.is_dirty()) {
				console.log('DEBUG: Document is dirty, saving first');
				frm.save().then(function() {
					makeRoleCreationCall(frm);
				});
			} else {
				console.log('DEBUG: Document is clean, creating role directly');
				makeRoleCreationCall(frm);
			}
		}
	);
}

function makeRoleCreationCall(frm) {
	console.log('DEBUG: Making role creation API call');
	
	frappe.call({
		method: 'duplicate.duplicate.doctype.role_duplicate.role_duplicate.create_role_from_duplicate',
		args: {
			role_duplicate_name: frm.doc.name
		},
		freeze: true,
		freeze_message: __('Creating new role...'),
		callback: function(r) {
			console.log('DEBUG: Role creation API response:', r);
			
			if (r && r.message) {
				if (r.message.status === 'success') {
					// Show success dialog with detailed results
					showRoleCreationDialogResponsive(r.message, frm);
					
				} else {
					// Show error message
					console.log('DEBUG: API returned error:', r.message);
					frappe.msgprint({
						title: __('Error Creating Role'),
						message: r.message.message || __('Failed to create role'),
						indicator: 'red'
					});
				}
			} else {
				console.log('DEBUG: No message in response:', r);
				frappe.msgprint({
					title: __('Unexpected Response'),
					message: __('Received unexpected response from server'),
					indicator: 'orange'
				});
			}
		},
		error: function(xhr, status, error) {
			console.log('DEBUG: Role creation API error details:');
			console.log('DEBUG: xhr:', xhr);
			console.log('DEBUG: status:', status);
			console.log('DEBUG: error:', error);
			
			let error_message = 'Unknown network error';
			
			// Check if this is a CSRF or authentication issue
			if (xhr && xhr.status === 403) {
				error_message = 'Authentication error (403). Please refresh the page and try again.';
			} else if (xhr && xhr.status === 404) {
				error_message = 'API endpoint not found (404). The method may not be properly registered.';
			} else if (xhr && xhr.status === 500) {
				error_message = 'Internal server error (500). Check server logs for details.';
			} else {
				if (xhr && xhr.responseText) {
					try {
						let response = JSON.parse(xhr.responseText);
						error_message = response.message || response.exc || xhr.responseText;
					} catch (e) {
						error_message = xhr.responseText || `${status}: ${error}`;
					}
				} else if (error) {
					error_message = error;
				} else if (status) {
					error_message = `HTTP ${status}`;
				}
			}
			
			frappe.msgprint({
				title: __('Network/Server Error'),
				message: __('Failed to create role: {0}', [error_message]),
				indicator: 'red'
			});
		}
	});
}

function showRoleCreationDialog(result, frm) {
	let permissions_loaded = frm.doc.role_permissions ? frm.doc.role_permissions.length : 0;
	let permissions_created = result.permissions_count || 0;
	let failed_count = (result.failed_permissions || []).length;
	let success_rate = permissions_loaded > 0 ? Math.round((permissions_created / permissions_loaded) * 100) : 0;
	
	// Create the dialog
	let d = new frappe.ui.Dialog({
		title: __('Role Creation Complete'),
		fields: [
			{
				fieldtype: 'HTML',
				fieldname: 'results_html',
				options: `
					<div style="padding: 20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
						<div style="text-align: center; margin-bottom: 25px;">
							<div style="font-size: 48px; margin-bottom: 10px;">
								${success_rate === 100 ? '🎉' : success_rate >= 80 ? '✅' : '⚠️'}
							</div>
							<h3 style="color: ${success_rate === 100 ? '#28a745' : success_rate >= 80 ? '#28a745' : '#ffc107'}; margin: 0;">
								${success_rate === 100 ? 'Perfect Success!' : success_rate >= 80 ? 'Success!' : 'Partial Success'}
							</h3>
						</div>
						
						<div style="background: #f8f9fa; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
							<table style="width: 100%; border-collapse: separate; border-spacing: 0 8px;">
								<tr>
									<td style="padding: 8px 12px; font-weight: 600; color: #495057;">
										Role Name:
									</td>
									<td style="padding: 8px 12px; color: #007bff; font-weight: 600; background: white; border-radius: 4px;">
										${result.role_name}
									</td>
								</tr>
								<tr>
									<td style="padding: 8px 12px; font-weight: 600; color: #495057;">
										Permissions in Form:
									</td>
									<td style="padding: 8px 12px; background: white; border-radius: 4px;">
										${permissions_loaded}
									</td>
								</tr>
								<tr>
									<td style="padding: 8px 12px; font-weight: 600; color: #495057;">
										Permissions Created:
									</td>
									<td style="padding: 8px 12px; color: #28a745; font-weight: bold; background: white; border-radius: 4px;">
										${permissions_created}
									</td>
								</tr>
								<tr>
									<td style="padding: 8px 12px; font-weight: 600; color: #495057;">
										Failed Permissions:
									</td>
									<td style="padding: 8px 12px; color: ${failed_count > 0 ? '#dc3545' : '#28a745'}; font-weight: bold; background: white; border-radius: 4px;">
										${failed_count}
									</td>
								</tr>
								<tr>
									<td style="padding: 8px 12px; font-weight: 600; color: #495057;">
										Success Rate:
									</td>
									<td style="padding: 8px 12px; font-weight: bold; background: white; border-radius: 4px;">
										<span style="color: ${success_rate === 100 ? '#28a745' : success_rate >= 80 ? '#28a745' : '#ffc107'};">
											${success_rate}%
										</span>
									</td>
								</tr>
							</table>
						</div>
						
						${failed_count > 0 ? 
							`<div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 15px; margin-bottom: 20px;">
								<h5 style="color: #856404; margin-top: 0; margin-bottom: 10px;">
									⚠️ Failed DocTypes (${failed_count}):
								</h5>
								<div style="max-height: 120px; overflow-y: auto; font-family: monospace; font-size: 12px; line-height: 1.4; background: white; padding: 10px; border-radius: 4px;">
									${result.failed_permissions.map(fp => `<div style="margin-bottom: 2px;">• ${fp}</div>`).join('')}
								</div>
							</div>` : 
							`<div style="background: #d1f2eb; border: 1px solid #76d7c4; border-radius: 8px; padding: 15px; margin-bottom: 20px; text-align: center;">
								<h5 style="color: #155724; margin: 0;">
									🎉 All permissions created successfully!
								</h5>
							</div>`
						}
						
						<div style="text-align: center; font-size: 14px; color: #6c757d;">
							<strong>Summary:</strong> ${permissions_created} role ${permissions_created === 1 ? 'permission' : 'permissions'} created successfully
							${failed_count > 0 ? ` (${failed_count} failed)` : ''}
						</div>
					</div>
				`
			}
		],
		primary_action_label: __('Open New Role'),
		primary_action: function() {
			d.hide();
			frappe.set_route('Form', 'Role', result.role_name);
		},
		secondary_action_label: __('Close'),
		secondary_action: function() {
			d.hide();
		}
	});
	
	// Show the dialog
	d.show();
	
	// Auto-close after 10 seconds if no interaction
	setTimeout(() => {
		if (d && d.$wrapper && d.$wrapper.is(':visible')) {
			// Add a countdown in the secondary button
			let countdown = 5;
			let countdownInterval = setInterval(() => {
				d.set_secondary_action_label(__('Close ({0})', [countdown]));
				countdown--;
				if (countdown < 0) {
					clearInterval(countdownInterval);
					if (d && d.$wrapper && d.$wrapper.is(':visible')) {
						d.hide();
					}
				}
			}, 1000);
		}
	}, 5000);
	
	// Reload the document to refresh the form
	frm.reload_doc();
}

// Helper function to format numbers with commas
function formatNumber(num) {
	return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// Alternative compact dialog for mobile/small screens
function showCompactRoleCreationDialog(result, frm) {
	let permissions_created = result.permissions_count || 0;
	let failed_count = (result.failed_permissions || []).length;
	
	frappe.msgprint({
		title: __('Role Creation Complete'),
		message: `
			<div style="text-align: center; padding: 15px;">
				<div style="font-size: 36px; margin-bottom: 15px;">
					${failed_count === 0 ? '🎉' : '✅'}
				</div>
				<h4 style="color: #28a745; margin-bottom: 20px;">
					Role "${result.role_name}" Created!
				</h4>
				<div style="background: #f8f9fa; padding: 15px; border-radius: 6px; margin-bottom: 15px;">
					<div><strong>${permissions_created}</strong> permissions created</div>
					${failed_count > 0 ? `<div style="color: #dc3545;"><strong>${failed_count}</strong> permissions failed</div>` : ''}
				</div>
				<button class="btn btn-primary btn-sm" onclick="frappe.set_route('Form', 'Role', '${result.role_name}')">
					Open New Role
				</button>
			</div>
		`,
		indicator: failed_count === 0 ? 'green' : 'orange'
	});
	
	frm.reload_doc();
}

// Detect screen size and use appropriate dialog
function showRoleCreationDialogResponsive(result, frm) {
	if (window.innerWidth < 768) {
		showCompactRoleCreationDialog(result, frm);
	} else {
		showRoleCreationDialog(result, frm);
	}
}