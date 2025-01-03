import frappe
import os
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


# def upload_image_to_linkedin(upload_url, image_path, access_token):
#     """
#     LinkedIn uploadUrl kullanarak resmi yükler.
#     """
#     try:
#         headers = {
#                 "Authorization": f"Bearer {access_token}",
#                 "Content-Type": "application/octet-stream"  # Binary dosya yüklemesi için
#             }

#         # Resim dosyasını binary formatında aç
#         with open(image_path, "rb") as image_file:
#             # PUT isteği ile resmi yükle
#             response = requests.put(upload_url, headers=headers, data=image_file)

#         # Yanıtı kontrol et
#         if response.status_code == 201:
#             print("Resim başarıyla yüklendi!")
#             return True
#         else:
#             print(f"Resim yükleme başarısız oldu: {response.status_code}")
#             print(f"LinkedIn API Hatası: {response.text}")
#             return False

#     except Exception as e:
#         print(f"Bir hata oluştu: {str(e)}")
#         return False

def upload_media_to_linkedin(upload_url, file_path, access_token):
    """
    LinkedIn uploadUrl kullanarak medya (resim/video) yükler.
    """
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/octet-stream"  # Binary dosya yüklemesi için
        }

        # Dosyayı binary formatında aç
        with open(file_path, "rb") as file:
            # PUT isteği ile medya yükle
            response = requests.put(upload_url, headers=headers, data=file)

        # Yanıtı kontrol et
        if response.status_code == 201:
            print("Medya başarıyla yüklendi!")
            return True
        else:
            print(f"Medya yükleme başarısız oldu: {response.status_code}")
            print(f"LinkedIn API Hatası: {response.text}")
            return False

    except Exception as e:
        print(f"Bir hata oluştu: {str(e)}")
        return False

# def publish_to_linkedin(doc, method):
#     """
#     Publish a post to LinkedIn with media support.
#     """
#     # LinkedIn API bilgilerini al
#     access_token = frappe.db.get_single_value("Linkedin Settings", "linkedin_access_token")
#     person_urn = frappe.db.get_single_value("Linkedin Settings", "linkedin_person_urn")
#     media_upload_endpoint = "https://api.linkedin.com/v2/assets?action=registerUpload"

#     if not access_token or not person_urn:
#         frappe.throw("LinkedIn API credentials are missing!")

#     # Post içeriğini HTML'den düz metne çevir
#     html_content = doc.linkedin_post_content or ""
#     soup = BeautifulSoup(html_content, "html.parser")
#     linkedin_post_content = soup.get_text().strip()

#     if not linkedin_post_content:
#         frappe.throw("Post content cannot be empty!")

#     # Medya dosyasını kontrol et ve LinkedIn'e yükle
#     media_urn = None
#     if doc.attachment:
#         # Dosya yolunu doğru şekilde oluştur
#         attachment_file_name = doc.attachment.replace("/files/", "")
#         file_path = frappe.get_site_path("public", "files", attachment_file_name)
#         site_url = frappe.utils.get_url()
#         attachment_url = f"{site_url}/files/{attachment_file_name}"

#         print(f"Attachment URL: {attachment_url}")
#         print(f"Resolved file path: {file_path}")

#         # Dosyanın mevcut olup olmadığını kontrol et
#         import os
#         if not os.path.exists(file_path):
#             frappe.throw(f"File not found at path: {file_path}")

#         # Medya yükleme için payload ve header
#         upload_headers = {
#             "Authorization": f"Bearer {access_token}",
#             "Content-Type": "application/json",
#             "X-Restli-Protocol-Version": "2.0.0"
#         }
#         upload_payload = {
#             "registerUploadRequest": {
#                 "owner": person_urn,
#                 "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
#                 "serviceRelationships": [{
#                     "relationshipType": "OWNER",
#                     "identifier": "urn:li:userGeneratedContent"
#                 }]
#             }
#         }

#         # Medyayı yükleme isteği
#         upload_response = requests.post(media_upload_endpoint, headers=upload_headers, json=upload_payload)

#         if upload_response.status_code == 200:
#             upload_result = upload_response.json()
#             print("Upload result", upload_result)
#             upload_url = upload_result["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
#             print("Upload URL:", upload_url)
#             media_urn = upload_result.get("value", {}).get("asset")
#             print("Media URN:", media_urn)

#             # LinkedIn'e yükleme işlemi
#             if not upload_image_to_linkedin(upload_url, file_path, access_token):
#                 frappe.throw("Failed to upload image to LinkedIn.")

#         else:
#             error_message = upload_response.json().get("message", "Unknown error")
#             frappe.throw(f"Error Uploading Media to LinkedIn: {error_message}")

#     # Gönderi için payload oluştur
#     payload = {
#         "author": person_urn,
#         "lifecycleState": "PUBLISHED",
#         "specificContent": {
#             "com.linkedin.ugc.ShareContent": {
#                 "shareCommentary": {
#                     "text": linkedin_post_content
#                 },
#                 "shareMediaCategory": "NONE" if not media_urn else "IMAGE",
#                 "media": [] if not media_urn else [
#                     {
#                         "status": "READY",
#                         "media": media_urn
#                     }
#                 ]
#             }
#         },
#         "visibility": {
#             "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
#         }
#     }

#     # LinkedIn API çağrısı
#     headers = {
#         "Authorization": f"Bearer {access_token}",
#         "Content-Type": "application/json",
#         "X-Restli-Protocol-Version": "2.0.0"
#     }

#     response = requests.post("https://api.linkedin.com/v2/ugcPosts", headers=headers, json=payload)

#     # Yanıtı işle
#     if response.status_code == 201:
#         data = response.json()
#         frappe.msgprint(f"LinkedIn Post Published. Post ID: {data.get('id')}")
#         doc.db_set("linkedin_post_id", data.get("id"))
#         doc.db_set("linkedin_status", "Published")
#     else:
#         error_message = response.json().get("message", "Unknown error")
#         frappe.log_error(message=f"LinkedIn API Error: {error_message}", title="LinkedIn API Error")
#         doc.db_set("linkedin_status", "Failed")
#         frappe.throw(f"Error Publishing Post: {error_message}")

def publish_to_linkedin(doc, method):
    """
    Publish a post to LinkedIn with media (image/video) support.
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
        # Dosya yolunu doğru şekilde oluştur
        attachment_file_name = doc.attachment.replace("/files/", "")
        file_path = frappe.get_site_path("public", "files", attachment_file_name)
        site_url = frappe.utils.get_url()
        attachment_url = f"{site_url}/files/{attachment_file_name}"

        print(f"Attachment URL: {attachment_url}")
        print(f"Resolved file path: {file_path}")

        # Dosyanın mevcut olup olmadığını kontrol et
        import os
        if not os.path.exists(file_path):
            frappe.throw(f"File not found at path: {file_path}")

        # Medya türünü belirle
        media_type = "urn:li:digitalmediaRecipe:feedshare-video" if file_path.endswith(('.mp4', '.mov')) else "urn:li:digitalmediaRecipe:feedshare-image"

        # Medya yükleme için payload ve header
        upload_headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        upload_payload = {
            "registerUploadRequest": {
                "owner": person_urn,
                "recipes": [media_type],
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
            print("Upload result", upload_result)
            upload_url = upload_result["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
            print("Upload URL:", upload_url)
            media_urn = upload_result.get("value", {}).get("asset")
            print("Media URN:", media_urn)

            # LinkedIn'e yükleme işlemi
            if not upload_media_to_linkedin(upload_url, file_path, access_token):
                frappe.throw("Failed to upload media to LinkedIn.")

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
                "shareMediaCategory": "NONE" if not media_urn else ("VIDEO" if file_path.endswith(('.mp4', '.mov')) else "IMAGE"),
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

# @frappe.whitelist()
# def delete_linkedin_post(linkedin_post_id):
#     """
#     Delete a post from LinkedIn using the DELETE method.
#     """
#     access_token = frappe.db.get_single_value("Linkedin Settings", "linkedin_access_token")

#     if not access_token:
#         frappe.throw("LinkedIn API credentials are missing!")

#     # `linkedin_post_id`'yi doğru formatla
#     if linkedin_post_id.startswith("urn:li:share:"):
#         linkedin_post_id = linkedin_post_id.split(":")[-1]

#     # LinkedIn API URL
#     url = f"https://api.linkedin.com/v2/shares/{linkedin_post_id}"

#     # API request headers
#     headers = {
#         "Authorization": f"Bearer {access_token}",
#     }

#     # DELETE isteği gönder
#     response = requests.delete(url, headers=headers)

#     # Yanıtı kontrol et
#     if response.status_code == 204:  # Başarılı silme işlemi
#         frappe.msgprint("LinkedIn post deleted successfully!")
#         return "success"
#     else:  # Hatalı durum veya başka durum kodları
#         try:
#             # Yanıtı JSON olarak işleme
#             response_data = response.json()
#             error_message = response_data.get("message", "Unknown error")
#         except Exception:
#             # JSON dışı yanıtı yakala ve yazdır
#             print(f"Raw response text: {response.text}")  # Konsola yazdır
#             frappe.log_error(message=f"Raw response text: {response.text}", title="LinkedIn API Raw Response")
#             error_message = response.text or "No response body returned from LinkedIn API."

#         frappe.log_error(message=f"LinkedIn API Error: {error_message}", title="LinkedIn API Error")
#         frappe.throw(f"Error Deleting LinkedIn Post: {error_message}")

@frappe.whitelist()
def delete_linkedin_post(linkedin_post_id):
    """
    Mark a LinkedIn post as DELETED by updating its lifecycleState.
    """
    access_token = frappe.db.get_single_value("Linkedin Settings", "linkedin_access_token")

    if not access_token:
        frappe.throw("LinkedIn API credentials are missing!")

    # URN türünü kontrol et
    if linkedin_post_id.startswith("urn:li:ugcPost:"):
        endpoint = "ugcPosts"
        linkedin_post_id = linkedin_post_id.split(":")[-1]
    elif linkedin_post_id.startswith("urn:li:share:"):
        endpoint = "shares"
        linkedin_post_id = linkedin_post_id.split(":")[-1]
    else:
        frappe.throw("Invalid LinkedIn Post ID format. Expected 'urn:li:share:<id>' or 'urn:li:ugcPost:<id>'.")

    # LinkedIn API URL
    url = f"https://api.linkedin.com/v2/{endpoint}/{linkedin_post_id}"

    # API request headers
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }

    # Eğer ugcPost ise varsayımsal version değeri ile lifecycleState güncellemesi
    if endpoint == "ugcPosts":
        # Varsayımsal version değeri
        version = 1  # Varsayımsal olarak 0 veya 1 deneyin
        payload = {
            "lifecycleState": "DELETED",
            "version": version
        }

        # Güncelleme isteği gönder
        response = requests.post(url, headers=headers, json=payload)
    else:
        # Share için DELETE isteği
        response = requests.delete(url, headers=headers)

    # Yanıtı kontrol et
    if response.status_code in [200, 204]:  # Başarılı durum kodları
        frappe.msgprint("LinkedIn post deleted successfully!")
        return "success"
    else:
        try:
            # Hata mesajını JSON'dan çıkar
            response_data = response.json()
            error_message = response_data.get("message", "Unknown error")
        except Exception:
            # JSON dışı veya boş yanıtı işleme
            error_message = response.text or "No response body returned from LinkedIn API."

        frappe.log_error(message=f"LinkedIn API Error: {error_message}", title="LinkedIn API Error")
        frappe.throw(f"Error Deleting LinkedIn Post: {error_message}")

@frappe.whitelist()
def update_likes_count(linkedin_post_id):
    """
    Update the likes count of a LinkedIn post in ERPNext.
    """
    # LinkedIn API Access Token
    access_token = frappe.db.get_single_value("Linkedin Settings", "linkedin_access_token")

    if not access_token:
        frappe.throw("LinkedIn API credentials are missing!")

    # LinkedIn API Endpoint
    url = f"https://api.linkedin.com/v2/socialMetadata/{linkedin_post_id}"

    # API Request Headers
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }

    # API Request
    response = requests.get(url, headers=headers)

    # Yanıtı kontrol et
    if response.status_code == 200:
        data = response.json()
        likes_count = data["elements"][0]["totalSocialActivityCounts"]["numLikes"]

        # ERPNext'teki `LinkedinPost` Doctype'ını güncelle
        linkedin_post = frappe.get_doc("Linkedin Post", {"linkedin_post_id": linkedin_post_id})
        linkedin_post.likes = likes_count
        linkedin_post.save()

        frappe.msgprint(f"Likes count updated: {likes_count}")
        return likes_count
    else:
        error_message = response.json().get("message", "Unknown error")
        frappe.log_error(message=f"LinkedIn API Error: {error_message}", title="LinkedIn API Error")
        frappe.throw(f"Error Updating Likes Count: {error_message}")



