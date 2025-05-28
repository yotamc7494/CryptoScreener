import requests
from config import SLACK_WEBHOOK_URL, SEND_SLACK


def send_slack_alert(message):
    if not SEND_SLACK:
        return
    payload = {"text": message}
    print(f"Slack msg: {message}")
    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload)
        if response.status_code != 200:
            print(f"Slack error: {response.status_code} {response.text}")
    except Exception as e:
        print(f"Failed to send Slack message: {e}")
