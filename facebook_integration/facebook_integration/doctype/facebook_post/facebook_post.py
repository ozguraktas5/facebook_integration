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
    Publish a post with optional image to Facebook.
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
    image_path = doc.attachment
    image_url = None
    if image_path:
        if "/private/" in image_path:
            image_url = move_file_to_public(image_path)
        else:
            site_url = get_url()
            image_url = f"{site_url}{image_path}"

    # Validate image URL
    if image_url and not image_url.startswith("http"):
        frappe.throw("Invalid image URL! Please provide a valid public URL.")

    # Prepare payload for Facebook API
    if image_url:
        # Publish post with an image
        url = f"https://graph.facebook.com/v12.0/{page_id}/photos"
        payload = {
            "url": image_url,
            "caption": post_content,
            "access_token": access_token
        }
    else:
        # Publish text-only post
        url = f"https://graph.facebook.com/v12.0/{page_id}/feed"
        payload = {
            "message": post_content,
            "access_token": access_token
        }

    # Make Facebook API call
    response = requests.post(url, data=payload)

    if response.status_code == 200:
        data = response.json()
        frappe.msgprint(f"Facebook Post Published. Post ID: {data['id']}")
    else:
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
