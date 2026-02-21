import re

def extract_full_text(adf):
    text = ""
    for block in adf.get("content", []):
        if block.get("type") == "paragraph":
            for item in block.get("content", []):
                if item.get("type") == "text":
                    text += item.get("text", "")
            text += " "
    return text


def check_reporter_observation(issue):
    # ✅ Read from customfield_10106 — this is where actual user values are stored
    field = issue["fields"].get("customfield_10106")

    if not field:
        return []

    text = " ".join(extract_full_text(field).split()).lower()
    

    questions = [
        ("Initial insights", "mention any initial insights"),
        ("VED screenshot",   "check internal ved"),
        ("Health check",     "share the output of health check script"),
        ("Troubleshooting",  "mention the troubleshooting steps"),
        ("Screenshots",      "did you add screenshots"),
        ("Logs",             "add logs or error messages"),
    ]

    INVALID_VALUES = {"n/a", "none", "-", "nil"}
    missing = []

    for i, (label, keyword) in enumerate(questions):
        start = text.find(keyword)

        if start == -1:
            missing.append(label)
            continue

        end = len(text)
        for _, next_kw in questions[i + 1:]:
            pos = text.find(next_kw, start + len(keyword))
            if pos != -1:
                end = min(end, pos)
                break

        segment = text[start:end]

        if ":" not in segment:
            missing.append(label)
            continue

        value = segment.split(":")[-1].strip()

        first_word = value.split()[0] if value.split() else ""
        if not first_word or first_word in INVALID_VALUES:
            missing.append(label)

    return missing


def check_required_fields(issue):
    return check_reporter_observation(issue)


def build_comment(issue, missing_fields):
    if not missing_fields:
        return "Hi,\n\nWe acknowledge the issue. We will update further details soon.\n"

    fields_text = "\n".join([f"- {f}" for f in missing_fields])

    return (
        f"Hi,\n\nTo proceed further, please provide the following details:\n\n"
        f"{fields_text}\n\nThis will help us analyze the issue faster.\n"
    )