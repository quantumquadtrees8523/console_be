import base64
from email.mime.text import MIMEText
from model_interfaces.generated_content import construct_daily_digest, get_next_week_outlook, get_todo_list, get_week_in_review
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SURYA_GOOGLE_USER_ID = "102049077090928333881" # Stored as a string in firestore

# print(construct_daily_digest(SURYA_GOOGLE_USER_ID))

import requests

# Configuration
MAILGUN_API_KEY = "2a4ecc161589b8ce16dbccac5bb4b629-6df690bb-a35f5f8cy"  # Replace with your Mailgun API key
MAILGUN_DOMAIN = "sandbox1f5f1207a7d64fde8ad9bab0563e2d8e.mailgun.org"    # Replace with your Mailgun verified domain (e.g., "sandbox123.mailgun.org")


response = requests.post(
  		"https://api.mailgun.net/v3/sandbox1f5f1207a7d64fde8ad9bab0563e2d8e.mailgun.org/messages",
  		auth=("api", MAILGUN_API_KEY),
  		data={"from": "mailgun@sandbox1f5f1207a7d64fde8ad9bab0563e2d8e.mailgun.org",
  			"to": ["surya.duggirala96@gmail.com"],
  			"subject": "Hello",
  			"text": "Testing some Mailgun awesomeness!"})

print(response)
print(response.text)