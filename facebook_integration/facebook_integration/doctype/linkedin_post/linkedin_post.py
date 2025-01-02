# Copyright (c) 2025, Ozgur Aktas and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta


class LinkedinPost(Document):
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

def publish_to_linkedin(doc, method):
    """
    Publish a post to LinkedIn.
    """
    # LinkedIn API bilgilerini al
    access_token = frappe.db.get_single_value("Linkedin Settings", "linkedin_access_token")
    person_urn = frappe.db.get_single_value("Linkedin Settings", "linkedin_person_urn")
    api_endpoint = "https://api.linkedin.com/v2/ugcPosts"

    if not access_token or not person_urn:
        frappe.throw("LinkedIn API credentials are missing!")

    # Post içeriğini HTML'den düz metne çevir
    html_content = doc.post_content or ""
    soup = BeautifulSoup(html_content, "html.parser")
    linkedin_post_content = soup.get_text().strip()

    if not linkedin_post_content:
        frappe.throw("Post content cannot be empty!")

    # Ek dosya (Resim/Video) kontrolü
    attachment_url = None
    if doc.attachment:
        site_url = frappe.utils.get_url()
        attachment_url = f"{site_url}{doc.attachment}"

    # Payload oluştur
    payload = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": linkedin_post_content
                },
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }

    # Eğer ek dosya varsa, payload'a medya bilgisi ekle
    if attachment_url:
        payload["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "IMAGE" if attachment_url.endswith((".jpg", ".png")) else "VIDEO"
        payload["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [
            {
                "status": "READY",
                "originalUrl": attachment_url
            }
        ]

    # LinkedIn API çağrısı
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }

    response = requests.post(api_endpoint, headers=headers, json=payload)

    # Yanıtı işle
    if response.status_code == 201:
        data = response.json()
        frappe.msgprint(f"LinkedIn Post Published. Post ID: {data.get('id')}")
        doc.db_set("linkedin_post_id", data.get("id"))
        doc.db_set("status", "Published")
    else:
        error_message = response.json().get("message", "Unknown error")
        frappe.log_error(message=f"LinkedIn API Error: {error_message}", title="LinkedIn API Error")
        doc.db_set("status", "Failed")
        frappe.throw(f"Error Publishing Post: {error_message}")
