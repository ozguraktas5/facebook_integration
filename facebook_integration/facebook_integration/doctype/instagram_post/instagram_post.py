# Copyright (c) 2024, Ozgur Aktas and contributors
# For license information, please see license.txt

import os
from PIL import Image
import requests
import frappe
from frappe.model.document import Document
from frappe.utils import get_url
from bs4 import BeautifulSoup
from datetime import datetime, timedelta


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

def resolve_media_path(media_path):
    """
    Resolve the media path to the full filesystem path.
    """
    if media_path.startswith("/files"):
        path = frappe.utils.get_site_path("public", "files", media_path.lstrip("/files"))
    elif media_path.startswith("/private/files"):
        path = frappe.utils.get_site_path("private", "files", media_path.lstrip("/private/files"))
    else:
        path = frappe.utils.get_site_path("public", "files", media_path)

    if not os.path.exists(path):
        raise FileNotFoundError(f"Media file does not exist at: {path}")

    return path

def validate_image_format(image_path):
    """
    Validate that the image is in a supported format and meets Instagram's requirements.
    """
    try:
        with Image.open(image_path) as img:
            if img.format not in ["JPEG", "PNG"]:
                raise ValueError("Unsupported image format. Only JPEG and PNG are allowed.")

            if img.mode not in ["RGB", "RGBA"]:
                img = img.convert("RGB")

            width, height = img.size
            if width > 1080 or height > 1080:
                img.thumbnail((1080, 1080))

            validated_path = os.path.splitext(image_path)[0] + "_validated.jpg"
            img.save(validated_path, "JPEG", quality=95)
            return validated_path

    except Exception as e:
        raise ValueError(f"Image validation failed: {str(e)}")

def publish_to_instagram(doc, method):
    """
    Publish an Instagram post when the Instagram Post Doctype is saved.
    """
    access_token = frappe.db.get_single_value("Instagram Settings", "instagram_api_access_token")
    instagram_account_id = frappe.db.get_single_value("Instagram Settings", "instagram_account_id")

    if not access_token or not instagram_account_id:
        frappe.throw("Instagram API credentials are missing!")

    html_content = doc.instagram_post_content or ""
    if not html_content.strip():
        frappe.throw("Instagram post content cannot be empty!")
    soup = BeautifulSoup(html_content, "html.parser")
    instagram_post_content = soup.get_text().strip()

    media_path = doc.attachment
    if not media_path:
        frappe.throw("Media file is missing!")

    try:
        media_path = resolve_media_path(media_path)
        if not os.path.exists(media_path):
            frappe.throw(f"Media file not found: {media_path}")

        media_path = validate_image_format(media_path)
    except FileNotFoundError as e:
        frappe.throw(str(e))

    site_url = get_dynamic_ngrok_url()
    relative_media_path = os.path.relpath(media_path, frappe.utils.get_site_path("public"))
    media_url = f"{site_url}/{relative_media_path}"

    upload_url = f"https://graph.facebook.com/v21.0/{instagram_account_id}/media"

    upload_payload = {
        "image_url": media_url,
        "caption": instagram_post_content,
        "access_token": access_token,
    }

    frappe.log_error(
        message=f"Upload Payload: {upload_payload}",
        title="Instagram API Debug"
    )

    upload_response = requests.post(upload_url, data=upload_payload)

    if upload_response.status_code == 200:
        upload_result = upload_response.json()
        container_id = upload_result.get("id")

        publish_url = f"https://graph.facebook.com/v21.0/{instagram_account_id}/media_publish"
        publish_payload = {
            "creation_id": container_id,
            "access_token": access_token,
        }
        publish_response = requests.post(publish_url, data=publish_payload)

        if publish_response.status_code == 200:
            publish_result = publish_response.json()
            frappe.msgprint(f"Image successfully published to Instagram. Post ID: {publish_result.get('id')}")
            doc.db_set("instagram_post_id", publish_result.get("id"))
            doc.db_set("instagram_status", "Published")
        else:
            error_message = publish_response.json().get("error", {}).get("message", "Unknown error")
            frappe.throw(f"Error Publishing Image: {error_message}")
    else:
        error_message = upload_response.json().get("error", {}).get("message", "Unknown error")
        frappe.throw(f"Error Uploading Media: {error_message}")

@frappe.whitelist()
def delete_instagram_post(instagram_post_id):
    """
    Delete a post from Instagram using the Graph API.
    """
    access_token = frappe.db.get_single_value("Instagram Settings", "instagram_api_access_token")

    if not access_token:
        frappe.throw("Instagram API credentials are missing!")

    url = f"https://graph.facebook.com/v21.0/{instagram_post_id}"

    response = requests.delete(url, params={"access_token": access_token})

    if response.status_code == 200:
        frappe.msgprint("Instagram post deleted successfully!")
        return "success"
    else:
        error_message = response.json().get("error", {}).get("message", "Unknown error")
        frappe.log_error(message=f"Instagram API Error: {error_message}", title="Instagram API Error")
        frappe.throw(f"Error Deleting Instagram Post: {error_message}")


def update_instagram_likes():
    """
    5 dakikada bir çalışacak görev: Instagram gönderilerinin beğeni sayılarını günceller.
    """
    # Instagram API erişim tokeni
    access_token = frappe.db.get_single_value("Instagram Settings", "instagram_api_access_token")

    if not access_token:
        frappe.throw("Instagram API credentials are missing!")

    # ERPNext'teki Instagram Post kayıtlarını al
    instagram_posts = frappe.get_all("Instagram Post", fields=["name", "instagram_post_id"])

    for post in instagram_posts:
        instagram_post_id = post.get("instagram_post_id")
        try:
            # Instagram Graph API'den beğeni sayısını al
            url = f"https://graph.facebook.com/v14.0/{instagram_post_id}?fields=like_count&access_token={access_token}"
            response = requests.get(url)
            response_data = response.json()

            if "error" in response_data:
                frappe.log_error(
                    message=f"Instagram API Hatası: {response_data['error']['message']}",
                    title="Instagram API Error"
                )
                continue

            # Beğeni sayısını güncelle
            likes = response_data.get("like_count", 0)
            doc = frappe.get_doc("Instagram Post", post["name"])
            doc.likes = likes
            doc.save()

            frappe.log_error(
                message=f"Post ID: {instagram_post_id}, Likes: {likes} olarak güncellendi.",
                title="Instagram Likes Update"
            )

        except Exception as e:
            # Hataları logla
            frappe.log_error(
                message=f"Hata: {str(e)} - Post ID: {instagram_post_id}",
                title="Instagram Likes Update Error"
            )

def update_instagram_comments():
    """
    Instagram gönderilerine ait yorumları ERPNext'e kaydeder.
    """
    # Instagram API erişim tokenini al
    access_token = frappe.db.get_single_value("Instagram Settings", "instagram_api_access_token")

    if not access_token:
        frappe.throw("Instagram API erişim bilgileri eksik!")

    # ERPNext'teki tüm Instagram Post kayıtlarını al
    instagram_posts = frappe.get_all("Instagram Post", fields=["name", "instagram_post_id", "instagram_post_content"])

    for post in instagram_posts:
        instagram_post_id = post.get("instagram_post_id")

        # ID eksikse atla
        if not instagram_post_id:
            frappe.log_error(
                message=f"Instagram Post ID eksik: {post['name']}",
                title="Instagram Comments Update Error"
            )
            continue

        try:
            # Instagram Graph API'den yorumları al
            url = f"https://graph.facebook.com/v14.0/{instagram_post_id}/comments?access_token={access_token}"
            response = requests.get(url)
            response_data = response.json()

            # API'den hata dönerse logla ve devam et
            if "error" in response_data:
                frappe.log_error(
                    message=f"Instagram API Hatası: {response_data['error']['message']}",
                    title="Instagram API Error"
                )
                continue

            # Yorumları birleştir
            comments_content = ""
            for comment in response_data.get("data", []):
                comment_message = comment.get("text", "")  # "message" yerine "text"
                comment_id = comment.get("id", "Bilinmeyen ID")
                created_time = comment.get("timestamp", "Bilinmeyen Tarih")  # "created_time" yerine "timestamp"

                # Tarihi "gün-ay-yıl saat" formatına dönüştür
                if created_time != "Bilinmeyen Tarih":
                    created_time = datetime.strptime(created_time, "%Y-%m-%dT%H:%M:%S+0000")
                    local_time = created_time + timedelta(hours=3)  # UTC+3
                    formatted_time = local_time.strftime("%d-%m-%Y %H:%M:%S")
                else:
                    formatted_time = created_time

                # Yorum detaylarını birleştir
                comments_content += f"<p><strong>Yorum:</strong> {comment_message}<br><strong>ID:</strong> {comment_id}<br><strong>Tarih:</strong> {formatted_time}</p><br><br>"

            # ERPNext'teki ilgili Instagram Post kaydını güncelle
            doc = frappe.get_doc("Instagram Post", post["name"])
            doc.instagram_post_content = comments_content.strip()
            doc.save()
            frappe.db.commit()

            # Başarı logu
            frappe.log_error(
                message=f"Post ID: {instagram_post_id} için yorumlar başarıyla güncellendi.",
                title="Instagram Comments Update"
            )

        except Exception as e:
            frappe.log_error(
                message=f"Hata: {str(e)} - Post ID: {instagram_post_id}",
                title="Instagram Comments Update Error"
            )