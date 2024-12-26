# Copyright (c) 2024, Ozgur Aktas and contributors
# For license information, please see license.txt

import os
import requests
import frappe
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

    # Check for attachment and process file
    file_path = doc.attachment  # Attachment from the Doctype
    site_url = "https://b59a-2a02-e0-c208-b000-547d-6928-4c6a-e73c.ngrok-free.app"  # Ngrok URL
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

    # Log the parameters for debugging
    print("API URL:", url)
    print("Payload (parameters being sent):", payload)

    # Make Facebook API call
    response = requests.post(url, data=payload)

    # Log the response for debugging
    print("Response Status Code:", response.status_code)
    print("Response Text:", response.text)

    if response.status_code == 200:
        # Facebook API call succeeded
        data = response.json()
        frappe.msgprint(f"Facebook Post Published. Post ID: {data.get('id', 'Unknown')}")
        # Save the Facebook Post ID to the ERPNext record
        doc.db_set("facebook_post_id", data.get("id"))
        doc.save()
    elif response.status_code == 400 and "Invalid parameter" in response.text:
        # Facebook accepted the post but returned a warning
        frappe.msgprint("Facebook Post Published, but with a warning: Invalid parameter.")
    else:
        # Facebook API call failed
        error_message = response.json().get("error", {}).get("message", "Unknown error")
        frappe.throw(f"Error Publishing Post: {error_message}")

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
