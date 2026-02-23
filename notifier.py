import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

INSTANCE_ID = os.getenv("GREEN_INSTANCE_ID")
API_TOKEN = os.getenv("GREEN_API_TOKEN")
GROUP_CHAT_ID = os.getenv("GREEN_GROUP_CHAT_ID")
JIRA_BASE_URL = "https://vunetsystems.atlassian.net/browse"

# Load mapping from env
ASSIGNEE_PHONE_MAP = json.loads(os.getenv("ASSIGNEE_PHONE_MAP", "{}"))


def check_whatsapp_status():
    url = f"https://api.green-api.com/waInstance{INSTANCE_ID}/getStateInstance/{API_TOKEN}"
    response = requests.get(url)
    state = response.json().get("stateInstance")

    if state != "authorized":
        print(f"⚠️ WhatsApp instance not authorized! State: {state}")
        return False
    return True


def send_whatsapp_notification(issue, missing_fields, severity=None):
    if not check_whatsapp_status():
        print("❌ Skipping WhatsApp notification — instance not authorized")
        return

    issue_key = issue["key"]
    ticket_url = f"{JIRA_BASE_URL}/{issue_key}"

    assignee = issue["fields"].get("assignee", {})
    assignee_name = assignee.get("displayName", "Unassigned") if assignee else "Unassigned"

    issuetype = issue["fields"].get("issuetype", {}).get("name", "N/A")
    summary = issue["fields"].get("summary", "N/A")

    phone = ASSIGNEE_PHONE_MAP.get(assignee_name)

    if missing_fields:
        fields_list = "\n".join([f"  - {f}" for f in missing_fields])
        message = (
            f"🎫 *{issue_key}* - {summary}\n"
            f"🔗 {ticket_url}\n\n"
            f"📋 *Type:* {issuetype}\n"
            f"📋 *Severity:* {severity or 'N/A'}\n"
            f"👤 *Assignee:* {assignee_name}\n\n"
            f"⚠️ *Missing fields:*\n{fields_list}\n\n"
            f"📩 Requested additional info from reporter."
        )
    else:
        message = (
            f"🎫 *{issue_key}* - {summary}\n"
            f"🔗 {ticket_url}\n\n"
            f"📋 *Type:* {issuetype}\n"
            f"📋 *Severity:* {severity or 'N/A'}\n"
            f"👤 *Assignee:* {assignee_name}\n"
            f"✅ All fields present.\n"
            f"➡️ Ticket moved to Assigned status."
        )

    url = f"https://api.green-api.com/waInstance{INSTANCE_ID}/sendMessage/{API_TOKEN}"

    if phone:
        payload = {
            "chatId": GROUP_CHAT_ID,
            "message": message,
            "mentionedPhoneNumbersList": [phone]
        }
    else:
        payload = {
            "chatId": GROUP_CHAT_ID,
            "message": message
        }

    response = requests.post(url, json=payload)

    if response.status_code == 200:
        print(f"📲 WhatsApp group notified for {issue_key}")
    else:
        print(f"❌ WhatsApp failed for {issue_key}: {response.text}")