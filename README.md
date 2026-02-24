# Auto Jira Responder 🤖

Automated Jira ticket responder with WhatsApp notifications.

## What it does
- Fetches open Jira tickets every 60 seconds
- Checks if required fields are filled in
- Posts a comment on the ticket
- Moves ticket to **Awaiting Info** if fields are missing
- Moves ticket to **Assigned** if all fields are present
- Sends WhatsApp group notification with ticket details

## Project Structure
```
auto-jira/
├── main.py          # Entry point and main loop
├── jira_client.py   # Jira API interactions
├── processor.py     # Field validation logic
├── notifier.py      # WhatsApp notifications via Green API
├── requirements.txt # Python dependencies
├── Dockerfile       # Docker image definition
└── k8s/
    ├── deployment.yaml  # Kubernetes deployment
    └── secret.yaml      # Kubernetes secrets template
```

## Setup

### Prerequisites
- Python 3.11+
- Docker
- Kubernetes cluster
- Jira API token
- Green API account for WhatsApp

### Environment Variables
Create a `.env` file:
```
JIRA_EMAIL=your@email.com
JIRA_API_TOKEN=your_jira_token
GREEN_INSTANCE_ID=your_instance_id
GREEN_API_TOKEN=your_green_api_token
GREEN_GROUP_CHAT_ID=your_group_chat_id
```

### Run locally
```bash
pip install -r requirements.txt
python main.py
```

### Build binary
```bash
docker run --rm -v "${PWD}:/app" python:3.11-slim bash -c \
  "apt-get update && apt-get install -y binutils && \
   pip install requests python-dotenv pyinstaller && \
   cd /app && pyinstaller --onefile main.py"
```

### Deploy to Kubernetes
```bash
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl logs -f deployment/auto-jira
```

