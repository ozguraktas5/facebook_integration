# Copyright (c) 2024, Ozgur Aktas and contributors
# For license information, please see license.txt

import os
import requests
import frappe
from frappe.model.document import Document
from frappe.utils import get_url
from bs4 import BeautifulSoup


class InstagramPost(Document):
    pass

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


def publish_to_instagram(doc, method):
    """
    Publish an Instagram post when the Instagram Post Doctype is saved.
    """
    # Fetch Instagram API credentials
    access_token = frappe.db.get_single_value("Instagram Settings", "instagram_api_access_token")
    instagram_account_id = frappe.db.get_single_value("Instagram Settings", "instagram_account_id")

    if not access_token or not instagram_account_id:
        frappe.throw("Instagram API credentials are missing!")

    # Convert HTML content to plain text
    html_content = doc.instagram_post_content
    soup = BeautifulSoup(html_content, "html.parser")
    instagram_post_content = soup.get_text().strip()

    # Get dynamic ngrok URL
    site_url = get_dynamic_ngrok_url()

    # Get post content and media file
    media_path = doc.attachment  # Attachment field for media files
    media_url = f"{site_url}{media_path}" if media_path else None

    if not media_url:
        frappe.throw("Media file is missing!")

    # Step 1: Upload media
    upload_url = f"https://graph.facebook.com/v12.0/{instagram_account_id}/media"
    upload_payload = {
        "image_url": media_url,  # Replace with "video_url" if uploading videos
        "caption": instagram_post_content,
        "access_token": access_token,
    }

    upload_response = requests.post(upload_url, data=upload_payload)

    if upload_response.status_code == 200:
        upload_result = upload_response.json()
        container_id = upload_result.get("id")

        # Step 2: Publish the media
        publish_url = f"https://graph.facebook.com/v12.0/{instagram_account_id}/media_publish"
        publish_payload = {
            "creation_id": container_id,
            "access_token": access_token,
        }
        publish_response = requests.post(publish_url, data=publish_payload)

        if publish_response.status_code == 200:
            publish_result = publish_response.json()
            frappe.msgprint(f"Instagram Post Published. Post ID: {publish_result.get('id')}")
            doc.db_set("instagram_post_id", publish_result.get("id"))
            doc.db_set("instagram_status", "Published")  # Update the status to Published
        else:
            error_message = publish_response.json().get("error", {}).get("message", "Unknown error")
            frappe.log_error(
                message=f"Instagram Publish Error: {error_message}",
                title="Instagram API Error"
            )
            frappe.throw(f"Error Publishing Post: {error_message}")
    else:
        error_message = upload_response.json().get("error", {}).get("message", "Unknown error")
        frappe.log_error(
            message=f"Instagram Upload Error: {error_message}",
            title="Instagram API Error"
        )
        frappe.throw(f"Error Uploading Media: {error_message}")

@frappe.whitelist()
def delete_instagram_post(instagram_post_id):
    """
    Delete a post from Instagram using the Graph API.
    """
    # Fetch Instagram API credentials
    access_token = frappe.db.get_single_value("Instagram Settings", "instagram_api_access_token")

    if not access_token:
        frappe.throw("Instagram API credentials are missing!")

    # Instagram Graph API endpoint for deleting a post
    url = f"https://graph.facebook.com/v17.0/{instagram_post_id}"

    # Make the DELETE request to Instagram API
    response = requests.delete(url, params={"access_token": access_token})

    if response.status_code == 200:
        frappe.msgprint("Instagram post deleted successfully!")
        return "success"
    else:
        error_message = response.json().get("error", {}).get("message", "Unknown error")
        frappe.log_error(message=f"Instagram API Error: {error_message}", title="Instagram API Error")
        frappe.throw(f"Error Deleting Instagram Post: {error_message}")

