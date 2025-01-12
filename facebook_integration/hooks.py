app_name = "facebook_integration"
app_title = "Facebook Integration"
app_publisher = "Ozgur Aktas"
app_description = "Facebook Integration"
app_email = "ozguraktas.55555@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "facebook_integration",
# 		"logo": "/assets/facebook_integration/logo.png",
# 		"title": "Facebook Integration",
# 		"route": "/facebook_integration",
# 		"has_permission": "facebook_integration.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/facebook_integration/css/facebook_integration.css"
# app_include_js = "/assets/facebook_integration/js/facebook_integration.js"

# include js, css files in header of web template
# web_include_css = "/assets/facebook_integration/css/facebook_integration.css"
# web_include_js = "/assets/facebook_integration/js/facebook_integration.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "facebook_integration/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "facebook_integration/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "facebook_integration.utils.jinja_methods",
# 	"filters": "facebook_integration.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "facebook_integration.install.before_install"
# after_install = "facebook_integration.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "facebook_integration.uninstall.before_uninstall"
# after_uninstall = "facebook_integration.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "facebook_integration.utils.before_app_install"
# after_app_install = "facebook_integration.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "facebook_integration.utils.before_app_uninstall"
# after_app_uninstall = "facebook_integration.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "facebook_integration.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"facebook_integration.tasks.all"
# 	],
# 	"daily": [
# 		"facebook_integration.tasks.daily"
# 	],
# 	"hourly": [
# 		"facebook_integration.tasks.hourly"
# 	],
# 	"weekly": [
# 		"facebook_integration.tasks.weekly"
# 	],
# 	"monthly": [
# 		"facebook_integration.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "facebook_integration.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "facebook_integration.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "facebook_integration.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["facebook_integration.utils.before_request"]
# after_request = ["facebook_integration.utils.after_request"]

# Job Events
# ----------
# before_job = ["facebook_integration.utils.before_job"]
# after_job = ["facebook_integration.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"facebook_integration.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

doc_events = {
    "Facebook Post": {
        "after_insert": "facebook_integration.facebook_integration.doctype.facebook_post.facebook_post.publish_to_facebook"
    },
    "Instagram Post": {
        "after_insert": "facebook_integration.facebook_integration.doctype.instagram_post.instagram_post.publish_to_instagram"
    },
    "Linkedin Post": {
        "after_insert": "facebook_integration.facebook_integration.doctype.linkedin_post.linkedin_post.publish_to_linkedin"
    },
    "Youtube Post": {
        "after_insert": "facebook_integration.facebook_integration.doctype.youtube_post.youtube_post.publish_to_youtube"
    }
}

scheduler_events = {
    "cron": {
        "*/5 * * * *": [
            "facebook_integration.facebook_integration.doctype.facebook_post.facebook_post.update_facebook_likes",
        ],
        "*/10 * * * *": [
            "facebook_integration.facebook_integration.doctype.facebook_post.facebook_post.update_facebook_comments",
        ],
        "*/15 * * * *": [
            "facebook_integration.facebook_integration.doctype.instagram_post.instagram_post.update_instagram_likes",
        ],
        "*/20 * * * *": [
            "facebook_integration.facebook_integration.doctype.instagram_post.instagram_post.update_instagram_comments",
        ],
        "*/25 * * * *": [
            "facebook_integration.facebook_integration.doctype.linkedin_post.linkedin_post.update_likes_count"
        ],
        
    }
}





