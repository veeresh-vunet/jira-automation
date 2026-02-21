import requests
from requests.auth import HTTPBasicAuth
import os

DEBUG = False

# CONFIG
JIRA_URL = "https://vunetsystems.atlassian.net"
EMAIL = os.getenv("JIRA_EMAIL")
API_TOKEN = os.getenv("JIRA_API_TOKEN")

auth = HTTPBasicAuth(EMAIL, API_TOKEN)

headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}

CARE_ACCOUNT_ID = "712020:f10344b1-ab23-4316-8dd7-5b52f0ae994c"


# ---------------- FETCH ----------------
def fetch_open_tickets():
    url = f"{JIRA_URL}/rest/api/3/search/jql"

    payload = {
        "jql": "filter=13912",
        "maxResults": 20,
        "expand": "renderedFields",
        "fields": [
            "summary",
            "labels",
            "reporter",
            "assignee",
            "customfield_10106",
            "customfield_10369"
        ]
    }

    response = requests.post(url, json=payload, headers=headers, auth=auth)

    if response.status_code != 200:
        print("❌ Error fetching tickets:", response.text)
        return []

    return response.json().get("issues", [])


# ---------------- COMMENT ----------------
def add_comment(issue, comment_text):
    issue_key = issue["key"]

    reporter = issue["fields"].get("reporter", {})
    account_id = reporter.get("accountId")

    if not account_id:
        print(f"⚠️ No reporter for {issue_key}")
        return False

    url = f"{JIRA_URL}/rest/api/3/issue/{issue_key}/comment"

    body = {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "mention",
                        "attrs": {"id": account_id}
                    },
                    {"type": "text", "text": " "},
                    {"type": "text", "text": comment_text}
                ]
            }
        ]
    }

    response = requests.post(
        url,
        json={"body": body},
        headers=headers,
        auth=auth
    )

    if response.status_code != 201:
        print(f"❌ Failed comment {issue_key}: {response.text}")
        return False

    return True


# ---------------- LABEL ----------------
def add_label(issue_key):
    url = f"{JIRA_URL}/rest/api/3/issue/{issue_key}"

    payload = {
        "update": {
            "labels": [{"add": "auto-responded"}]
        }
    }

    response = requests.put(url, json=payload, headers=headers, auth=auth)

    if response.status_code != 204:
        print(f"❌ Label failed {issue_key}: {response.text}")
        return False


    return True


# ---------------- SET CARE OWNER ----------------
def set_care_owner(issue_key):
    url = f"{JIRA_URL}/rest/api/3/issue/{issue_key}"

    payload = {
        "fields": {
            "customfield_10105": {
                "accountId": CARE_ACCOUNT_ID
            }
        }
    }

    response = requests.put(url, json=payload, headers=headers, auth=auth)

    if response.status_code != 204:
        print(f"❌ Failed to set CARE Owner {issue_key}: {response.text}")
        return False

    print(f"👤 CARE Owner set {issue_key}")
    return True



# ---------------- TRANSITIONS ----------------
def get_transitions(issue_key):
    url = f"{JIRA_URL}/rest/api/3/issue/{issue_key}/transitions"

    response = requests.get(url, headers=headers, auth=auth)

    if response.status_code != 200:
        print(f"❌ Transition fetch failed {issue_key}")
        return []

    return response.json().get("transitions", [])


def transition_issue(issue_key, transition_id):
    url = f"{JIRA_URL}/rest/api/3/issue/{issue_key}/transitions"

    payload = {
        "transition": {
            "id": str(transition_id)
        }
    }

    response = requests.post(url, json=payload, headers=headers, auth=auth)

    if response.status_code != 204:
        print(f"\n❌ Transition FAILED for {issue_key}")
        print("Status:", response.status_code)
        print("Response:", response.text)   # 🔥 IMPORTANT
        return False

    print(f"➡️ Transitioned {issue_key} using {transition_id}")
    return True


# ---------------- MOVE STATUS ----------------
def move_to_awaiting_info(issue):
    issue_key = issue["key"]

    # Set CARE Owner
    set_care_owner(issue_key)

    for i in range(6):

        transitions = get_transitions(issue_key)

        if not transitions:
            print(f"❌ No transitions available for {issue_key}")
            return

        # DEBUG logs (optional)
        if DEBUG:
            print(f"\n🔍 Step {i+1} transitions for {issue_key}")
            for t in transitions:
                print(f"➡️ {t['id']} -> {t['name']}")

        moved = False

        for t in transitions:
            name = t["name"].lower()

            # 🎯 FINAL TARGET
            if any(x in name for x in ["awaiting", "requesting more info", "more info"]):
                print(f"🎯 Moved to Awaiting Info {issue_key}")
                transition_issue(issue_key, t["id"])
                return

            # 🚀 INTERMEDIATE STEPS
            elif any(x in name for x in ["assign", "progress", "troubleshooting"]):
                if DEBUG:
                    print(f"➡️ Moving via {t['name']}")

                success = transition_issue(issue_key, t["id"])

                if success:
                    moved = True
                    break

        if not moved:
            print(f"⚠️ Cannot move further {issue_key}")
            return
        
def move_to_assigned(issue):
    issue_key = issue["key"]

    for i in range(6):
        transitions = get_transitions(issue_key)

        if not transitions:
            print(f"❌ No transitions available for {issue_key}")
            return

        for t in transitions:
            name = t["name"].lower()
            if any(x in name for x in ["assign", "assigned"]):
                print(f"🎯 Moved to Assigned {issue_key}")
                transition_issue(issue_key, t["id"])
                return
            elif any(x in name for x in ["progress", "troubleshooting"]):
                success = transition_issue(issue_key, t["id"])
                if success:
                    break
        else:
            print(f"⚠️ Cannot move further {issue_key}")
            return   