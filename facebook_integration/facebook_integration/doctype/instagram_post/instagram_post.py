# Copyright (c) 2024, Ozgur Aktas and contributors
# For license information, please see license.txt

import os
from PIL import Image
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

def resolve_media_path(media_path):
    """
    Resolve the media path to the full filesystem path.
    """
    # Eğer yol /files ile başlıyorsa, public/files dizinine dönüştür
    if media_path.startswith("/files"):
        path = frappe.utils.get_site_path("public", "files", media_path.lstrip("/files"))
    elif media_path.startswith("/private/files"):
        path = frappe.utils.get_site_path("private", "files", media_path.lstrip("/private/files"))
    else:
        # Eğer /files ile başlamıyorsa, yolun başına public/files ekle
        path = frappe.utils.get_site_path("public", "files", media_path)

    # Dosyanın mevcut olup olmadığını kontrol et
    if not os.path.exists(path):
        raise FileNotFoundError(f"Media file does not exist at: {path}")

    return path

    
def validate_video_format(video_path):
    """
    Validate that the video is in a supported format (MP4).
    """
    if not video_path.endswith(".mp4"):
        raise ValueError("Unsupported video format. Only MP4 is allowed.")

    # Eğer gerekliyse ek video formatı kontrolleri eklenebilir
    return video_path

def validate_image_format(image_path):
    """
    Validate that the image is in a supported format and meets Instagram's requirements.
    """
    try:
        with Image.open(image_path) as img:
            # Kontrol: Dosya formatı
            if img.format not in ["JPEG", "PNG"]:
                raise ValueError("Unsupported image format. Only JPEG and PNG are allowed.")

            # Kontrol: Renk Modu
            if img.mode not in ["RGB", "RGBA"]:
                img = img.convert("RGB")  # Renk modunu RGB'ye çevirin

            # Kontrol: Dosya boyutu
            width, height = img.size
            if width > 1080 or height > 1080:
                img.thumbnail((1080, 1080))  # 1080px'e yeniden boyutlandır

            # Doğrulanan dosyayı kaydet
            validated_path = os.path.splitext(image_path)[0] + "_validated.jpg"
            img.save(validated_path, "JPEG", quality=95)  # JPEG formatında kaydedin
            return validated_path

    except Exception as e:
        raise ValueError(f"Image validation failed: {str(e)}")

def publish_to_instagram(doc, method):
    """
    Publish an Instagram post when the Instagram Post Doctype is saved.
    """
    # Instagram API kimlik bilgilerini alın
    access_token = frappe.db.get_single_value("Instagram Settings", "instagram_api_access_token")
    instagram_account_id = frappe.db.get_single_value("Instagram Settings", "instagram_account_id")

    if not access_token or not instagram_account_id:
        frappe.throw("Instagram API credentials are missing!")

    # HTML içeriğini düz metne dönüştür
    html_content = doc.instagram_post_content or ""
    if not html_content.strip():
        frappe.throw("Instagram post content cannot be empty!")
    soup = BeautifulSoup(html_content, "html.parser")
    instagram_post_content = soup.get_text().strip()

    # Medya dosyasını doğrula ve yolunu çözümle
    media_path = doc.attachment
    if not media_path:
        frappe.throw("Media file is missing!")  # Attachment field for media files

    try:
        media_path = resolve_media_path(media_path)  # Medya yolunu çözümle
        if not os.path.exists(media_path):
            frappe.throw(f"Media file not found: {media_path}")

        # Dosya türüne göre doğrula
        if media_path.endswith(".mp4"):
            media_path = validate_video_format(media_path)  # Video doğrulama
        else:
            media_path = validate_image_format(media_path)  # Resim doğrulama
    except FileNotFoundError as e:
        frappe.throw(str(e))

    # Medya URL'sini oluştur
    site_url = get_dynamic_ngrok_url()
    relative_media_path = os.path.relpath(media_path, frappe.utils.get_site_path("public"))
    media_url = f"{site_url}/{relative_media_path}"

    # Media URL loglama
    frappe.log_error(message=f"Media URL: {media_url}", title="Media URL Debug")
    frappe.log_error(message=f"Resolved Media Path: {media_path}", title="Media Path Debug")
    frappe.log_error(message=f"Generated Media URL: {media_url}", title="Media URL Debug")


    # Instagram'a medya yükle
    upload_url = f"https://graph.facebook.com/v21.0/{instagram_account_id}/media"

    # Medya türüne göre payload oluştur
    if media_path.strip().lower().endswith(".mp4"):
        upload_payload = {
            "video_url": media_url,
            "caption": instagram_post_content,
            "access_token": access_token,
        }
    else:
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

        # Medyayı yayınla
        publish_url = f"https://graph.facebook.com/v21.0/{instagram_account_id}/media_publish"
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
    url = f"https://graph.facebook.com/v21.0/{instagram_post_id}"

    # Make the DELETE request to Instagram API
    response = requests.delete(url, params={"access_token": access_token})

    if response.status_code == 200:
        frappe.msgprint("Instagram post deleted successfully!")
        return "success"
    else:
        error_message = response.json().get("error", {}).get("message", "Unknown error")
        frappe.log_error(message=f"Instagram API Error: {error_message}", title="Instagram API Error")
        frappe.throw(f"Error Deleting Instagram Post: {error_message}")

