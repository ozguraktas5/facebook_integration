# Copyright (c) 2024, Ozgur Aktas and contributors
# For license information, please see license.txt

import os
import requests
import frappe
from frappe import _
from frappe.utils.response import Response
from frappe.model.document import Document
from frappe.utils import get_url
from bs4 import BeautifulSoup

class FacebookPost(Document):
    pass

def move_file_to_public(file_path):
    """
    Move a file from the private directory to the public directory.
    """
    site_path = frappe.get_site_path()
    private_path = os.path.join(site_path, file_path.strip("/"))
    public_path = private_path.replace("/private/files/", "/public/files/")

    if os.path.exists(private_path):
        os.makedirs(os.path.dirname(public_path), exist_ok=True)
        os.rename(private_path, public_path)
        public_url = public_path.replace(site_path, "")
        return f"{get_url()}{public_url}"
    else:
        frappe.throw(f"File not found: {file_path}")

def get_dynamic_ngrok_url():
    """
    Fetch the current public forwarding URL from the ngrok API.
    """
    ngrok_api_url = "http://127.0.0.1:4040/api/tunnels"  # Default ngrok API endpoint for local machine
    try:
        response = requests.get(ngrok_api_url)
        response.raise_for_status()
        tunnels = response.json().get("tunnels", [])
        for tunnel in tunnels:
            if tunnel.get("proto") == "https":  # Look for the HTTPS tunnel
                return tunnel.get("public_url")
        frappe.throw("No HTTPS ngrok URL found. Make sure ngrok is running.")
    except requests.exceptions.RequestException as e:
        frappe.throw(f"Failed to fetch ngrok URL: {str(e)}")


def publish_to_facebook(doc, method):
    """
    Publish a post with an optional image or video to Facebook.
    """
    # Fetch Facebook API credentials
    access_token = frappe.db.get_single_value("Facebook Settings", "facebook_api_access_token")
    page_id = frappe.db.get_single_value("Facebook Settings", "facebook_page_id")

    if not access_token or not page_id:
        frappe.throw("Facebook API credentials are missing!")

    # Convert HTML content to plain text
    html_content = doc.post_content
    soup = BeautifulSoup(html_content, "html.parser")
    post_content = soup.get_text().strip()

    # Get dynamic ngrok URL
    site_url = get_dynamic_ngrok_url()

    # Check for attachment and process file
    file_path = doc.attachment  # Attachment from the Doctype
    file_url = f"{site_url}{file_path}" if file_path else None

    # Determine if the file is a video or image
    if file_url and file_url.endswith((".mp4", ".avi", ".mov")):
        # Video upload
        url = f"https://graph.facebook.com/v12.0/{page_id}/videos"
        payload = {
            "file_url": file_url,  # Video URL
            "description": post_content,  # Video description
            "access_token": access_token
        }
    elif file_url and file_url.endswith((".jpg", ".jpeg", ".png", ".gif")):
        # Image upload
        url = f"https://graph.facebook.com/v12.0/{page_id}/photos"
        payload = {
            "url": file_url,  # Image URL
            "caption": post_content,  # Image caption
            "access_token": access_token
        }
    else:
        # Text-only post
        url = f"https://graph.facebook.com/v12.0/{page_id}/feed"
        payload = {
            "message": post_content,
            "access_token": access_token
        }

    # Make Facebook API call
    response = requests.post(url, data=payload)

    if response.status_code == 200:
        data = response.json()
        frappe.msgprint(f"Facebook Post Published. Post ID: {data.get('id', 'Unknown')}")
        doc.db_set("facebook_post_id", data.get("id"))
        doc.db_set("status", "Published")
    else:
        error_message = response.json().get("error", {}).get("message", "Unknown error")
        frappe.log_error(message=f"Facebook API Error: {error_message}", title="Facebook API Error")
        frappe.throw(f"Error Publishing Post: {error_message}")

@frappe.whitelist()
def delete_facebook_post(facebook_post_id):
    """
    Delete a post from Facebook using the Graph API.
    """
    # Fetch Facebook API credentials
    access_token = frappe.db.get_single_value("Facebook Settings", "facebook_api_access_token")

    if not access_token:
        frappe.throw("Facebook API credentials are missing!")

    # Facebook Graph API endpoint for deleting a post
    url = f"https://graph.facebook.com/v12.0/{facebook_post_id}"

    # Make the DELETE request to Facebook API
    response = requests.delete(url, params={"access_token": access_token})

    if response.status_code == 200:
        frappe.msgprint("Post deleted successfully!")
        return "success"
    else:
        error_message = response.json().get("error", {}).get("message", "Unknown error")
        frappe.log_error(message=f"Facebook API Error: {error_message}", title="Facebook API Error")
        frappe.throw(f"Error Deleting Post: {error_message}")


def fetch_facebook_posts(access_token, page_id):
    """
    Fetch recent posts from Facebook and insert them as Facebook Post documents in ERPNext.
    """
    url = f"https://graph.facebook.com/v12.0/{page_id}/posts"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        posts = response.json().get('data', [])
        for post in posts:
            # Avoid duplicate entries
            if not frappe.db.exists("Facebook Post", {"facebook_post_id": post.get('id', '')}):
                doc = frappe.get_doc({
                    "doctype": "Facebook Post",
                    "post_title": post.get('message', '')[:30],  # First 30 characters
                    "post_content": post.get('message', ''),
                    "post_date": post.get('created_time', ''),
                    "facebook_post_id": post.get('id', '')
                })
                doc.insert()
    else:
        error_message = response.json().get("error", {}).get("message", "Unknown error")
        frappe.throw(f"Error Fetching Posts: {error_message}")

@frappe.whitelist(allow_guest=True)
def facebook_webhook_handler():
    """
    Handle Facebook Webhook events and save data to ERPNext.
    """
    if frappe.request.method == "POST":
        # Get the data sent by Facebook
        data = frappe.local.form_dict

        # Log the data for debugging
        frappe.log_error(message=data, title="Facebook Webhook Event")

        # Process likes (if they exist in the event)
        if "entry" in data:
            for entry in data["entry"]:
                if "changes" in entry:
                    for change in entry["changes"]:
                        if change.get("field") == "likes":
                            # Extract like details
                            post_id = change.get("value", {}).get("post_id")
                            like_count = change.get("value", {}).get("like_count")

                            if post_id and like_count is not None:
                                # Update the Facebook Post in ERPNext
                                update_like_count(post_id, like_count)

        # Return a 200 OK response to Facebook
        return Response("Event received", status=200, mimetype="text/plain")

    # Handle GET requests for verification
    if frappe.request.method == "GET":
        verify_token = "EAAR3ax0DANEBOzsSckzuqp0kGx8WpsrbXZAp74AyGPuRXmJRK9b2noiAr4HYMfDM6z09fR3elN2Xx7ZAOOJEu3FAeZBP1TI1BPnrWB4LstkZC3ldnv6RKvwuGyBbVD63GmcI1EcBBxakhe94o26gkDshZAZBLjURP4JKeatHGWGq8jnico4tNrgpi9Uqt6LwZDZD"  # Same token you set in Facebook settings
        mode = frappe.form_dict.get("hub.mode")
        token = frappe.form_dict.get("hub.verify_token")
        challenge = frappe.form_dict.get("hub.challenge")

        if mode == "subscribe" and token == verify_token:
            return Response(challenge, status=200, mimetype="text/plain")

    return Response("Not Found", status=404, mimetype="text/plain")

def update_like_count(post_id, like_count):
    """
    Update the like count for a specific Facebook post in ERPNext.
    """
    try:
        # Check if the post exists in ERPNext
        facebook_post = frappe.get_doc("Facebook Post", {"facebook_post_id": post_id})
        if facebook_post:
            # Update the like count
            facebook_post.db_set("likes", like_count)
            frappe.msgprint(f"Likes updated for Post ID {post_id}: {like_count}")
    except frappe.DoesNotExistError:
        frappe.log_error(message=f"Facebook Post with ID {post_id} not found.", title="Facebook Webhook Error")
