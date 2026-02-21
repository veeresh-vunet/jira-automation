import sys
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

import time
from jira_client import fetch_open_tickets, add_comment, add_label, move_to_awaiting_info, move_to_assigned
from processor import check_required_fields, build_comment
from notifier import send_whatsapp_notification



DEBUG = False   # set True only when debugging


def process_tickets():
    tickets = fetch_open_tickets()

    print(f"\n📊 Found {len(tickets)} tickets")

    for issue in tickets:
        key = issue["key"]
        labels = issue["fields"].get("labels", [])

        # skip already processed
        if "auto-responded" in labels:
            print(f"⏭️ Skipping {key}")
            continue

        print(f"⚙️ Processing {key}")

        try:
            # check missing fields
            missing = check_required_fields(issue)

            # build comment
            comment = build_comment(issue, missing)

            # add comment
            if add_comment(issue, comment):
                print(f"💬 Comment added {key}")
            else:
                print(f"❌ Failed to add comment {key}")
                continue

            # add label
            if add_label(key):
                print(f"🏷️ Label added {key}")
            else:
                print(f"❌ Failed to add label {key}")

            # get severity
            severity = issue["fields"].get("customfield_10369", {}).get("value", "N/A")

            # move and notify based on missing fields
            if missing:
                print(f"📌 Missing fields → moving {key} to Awaiting Info")
                move_to_awaiting_info(issue)
            else:
                print(f"✅ All fields present → moving {key} to Assigned")
                move_to_assigned(issue)

            # send WhatsApp notification
            send_whatsapp_notification(issue, missing, severity)
            print(f"📲 WhatsApp notified {key}")

        except Exception as e:
            print(f"❌ Error {key}: {e}")


if __name__ == "__main__":
    print("🚀 Jira Auto Responder Started")

    while True:
        process_tickets()
        print("⏳ Sleeping 60 sec...\n")
        time.sleep(60)