// Copyright (c) 2025, Ozgur Aktas and contributors
// For license information, please see license.txt

frappe.ui.form.on("Linkedin Post", {
	refresh: function (frm) {
		if (frm.doc.linkedin_status === "Published") {
			frm.add_custom_button("Delete Post", () => {
				frappe.call({
					method: "facebook_integration.facebook_integration.doctype.linkedin_post.linkedin_post.delete_linkedin_post",
					args: { linkedin_post_id: frm.doc.linkedin_post_id },
					callback: function (response) {
						if (response.message === "success") {
							frappe.msgprint("Linkedin Post deleted successfully!");
						}
					},
				});
			});
		}
	},
});
