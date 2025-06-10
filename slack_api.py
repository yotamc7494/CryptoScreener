import requests
from config import SLACK_WEBHOOK_URL, SEND_SLACK

def send_slack_alert(message):
    if not SEND_SLACK:
        return
    headers = {
        "Authorization": f"Bearer {SLACK_WEBHOOK_URL}",
        "Content-Type": "application/json"
    }
    data = {
        "channel": "#general",
        "text": message
    }
    try:
        response = requests.post("https://slack.com/api/chat.postMessage", headers=headers, json=data)
        if response.status_code != 200:
            print(f"Slack error: {response.status_code} {response.text}")
        else:
            print(f"Send Slack Msg: {message}")
    except Exception as e:
        print(f"Failed to send Slack message: {e}")
