import requests
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/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"

def send_slack_alert(message):
    payload = {"text": message}
    print(f"Slack msg: {message}")
    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload)
        if response.status_code != 200:
            print(f"Slack error: {response.status_code} {response.text}")
    except Exception as e:
        print(f"Failed to send Slack message: {e}")
