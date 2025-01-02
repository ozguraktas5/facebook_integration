import frappe
from frappe.model.document import Document
import requests
from bs4 import BeautifulSoup


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


def upload_image_to_linkedin(upload_url, image_path, access_token):
    """
    LinkedIn uploadUrl kullanarak resmi yükler.
    """
    try:
        # Resim dosyasını binary formatında aç
        with open(image_path, "rb") as image_file:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/octet-stream"  # Binary dosya yüklemesi için
            }

            # PUT isteği ile resmi yükle
            response = requests.put(upload_url, headers=headers, data=image_file)

            # Yanıtı kontrol et
            if response.status_code == 201:
                print("Resim başarıyla yüklendi!")
                return True
            else:
                print(f"Resim yükleme başarısız oldu: {response.status_code}, {response.text}")
                return False

    except Exception as e:
        print(f"Bir hata oluştu: {str(e)}")
        return False


def publish_to_linkedin(doc, method):
    """
    Publish a post to LinkedIn with media support.
    """
    # LinkedIn API bilgilerini al
    access_token = frappe.db.get_single_value("Linkedin Settings", "linkedin_access_token")
    person_urn = frappe.db.get_single_value("Linkedin Settings", "linkedin_person_urn")
    media_upload_endpoint = "https://api.linkedin.com/v2/assets?action=registerUpload"

    if not access_token or not person_urn:
        frappe.throw("LinkedIn API credentials are missing!")

    # Post içeriğini HTML'den düz metne çevir
    html_content = doc.linkedin_post_content or ""
    soup = BeautifulSoup(html_content, "html.parser")
    linkedin_post_content = soup.get_text().strip()

    if not linkedin_post_content:
        frappe.throw("Post content cannot be empty!")

    # Medya dosyasını kontrol et ve LinkedIn'e yükle
    media_urn = None
    if doc.attachment:
        site_url = frappe.utils.get_url()
        attachment_url = f"{site_url}/files/{doc.attachment}"
        


        # Medya yükleme için payload ve header
        upload_headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        upload_payload = {
            "registerUploadRequest": {
                "owner": person_urn,
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                "serviceRelationships": [{
                    "relationshipType": "OWNER",
                    "identifier": "urn:li:userGeneratedContent"
                }]
            }
        }

        # Medyayı yükleme isteği
        upload_response = requests.post(media_upload_endpoint, headers=upload_headers, json=upload_payload)

        if upload_response.status_code == 200:
            upload_result = upload_response.json()
            upload_url = upload_result["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
            media_urn = upload_result.get("value", {}).get("asset")

            if not upload_image_to_linkedin(upload_url, frappe.get_site_path("public", doc.attachment), access_token):
                frappe.throw("Failed to upload image to LinkedIn.")

        else:
            error_message = upload_response.json().get("message", "Unknown error")
            frappe.throw(f"Error Uploading Media to LinkedIn: {error_message}")

    # Gönderi için payload oluştur
    payload = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": linkedin_post_content
                },
                "shareMediaCategory": "NONE" if not media_urn else "IMAGE",
                "media": [] if not media_urn else [
                    {
                        "status": "READY",
                        "media": media_urn
                    }
                ]
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }

    # LinkedIn API çağrısı
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }

    response = requests.post("https://api.linkedin.com/v2/ugcPosts", headers=headers, json=payload)

    # Yanıtı işle
    if response.status_code == 201:
        data = response.json()
        frappe.msgprint(f"LinkedIn Post Published. Post ID: {data.get('id')}")
        doc.db_set("linkedin_post_id", data.get("id"))
        doc.db_set("linkedin_status", "Published")
    else:
        error_message = response.json().get("message", "Unknown error")
        frappe.log_error(message=f"LinkedIn API Error: {error_message}", title="LinkedIn API Error")
        doc.db_set("linkedin_status", "Failed")
        frappe.throw(f"Error Publishing Post: {error_message}")
