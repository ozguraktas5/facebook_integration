// Copyright (c) 2024, Ozgur Aktas and contributors
// For license information, please see license.txt

frappe.ui.form.on("Facebook Post", {
	refresh: function (frm) {
		// If the status is Published, show the "Delete Post" button
		if (frm.doc.status === "Published") {
			frm.add_custom_button(__("Delete Post"), function () {
				frappe.call({
					method: "facebook_integration.facebook_integration.doctype.facebook_post.facebook_post.delete_facebook_post",
					args: {
						facebook_post_id: frm.doc.facebook_post_id,
					},
					callback: function (response) {
						if (response.message === "success") {
							frappe.msgprint(__("Facebook Post Deleted Successfully"));
							frm.set_value("status", "Deleted");
							frm.save();
						}
					},
				});
			});
		}
	},
});
