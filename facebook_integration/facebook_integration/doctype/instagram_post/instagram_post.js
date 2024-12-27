// Copyright (c) 2024, Ozgur Aktas and contributors
// For license information, please see license.txt

frappe.ui.form.on("Instagram Post", {
	refresh: function (frm) {
		if (frm.doc.instagram_status === "Published") {
			frm.add_custom_button("Delete Post", () => {
				frappe.call({
					method: "facebook_integration.facebook_integration.doctype.instagram_post.instagram_post.delete_instagram_post",
					args: { instagram_post_id: frm.doc.instagram_post_id },
					callback: function (response) {
						if (response.message === "success") {
							frappe.msgprint("Instagram Post deleted successfully!");
						}
					},
				});
			});
		}
	},
});
