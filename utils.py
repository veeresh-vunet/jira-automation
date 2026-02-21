def is_already_processed(issue):
    labels = issue.get("fields", {}).get("labels", [])
    return "auto-responded" in labels