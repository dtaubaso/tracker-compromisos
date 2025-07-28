import firebase_service, requests, json, logging

ACCESO = firebase_service.acces_firebase_db()
error_webhook = ACCESO['error_webhook']

def send_slack(text):
  slack_data = {'text': "[TRACKER-BOT] " + text}
  response = requests.post(error_webhook, data=json.dumps(slack_data), headers={'Content-Type': 'application/json'})
  logging.info(response.status_code)