import os
import pickle
import google.auth
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import scrubadub
import requests
import time
import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os
import pickle
import google.auth
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import scrubadub
import requests
import time
load_dotenv()

def authenticate_gmail():
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file( 
                "credentials.json", ["https://www.googleapis.com/auth/gmail.modify"]
            )
            creds = flow.run_local_server(port=0)

        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    return build("gmail", "v1", credentials=creds)


def get_unread_emails(service, categories):
   
    query = 'is:unread AND ' + ' AND '.join([f'-label:{category}' for category in categories])
    results = service.users().messages().list(userId='me', q=query).execute()
    messages = results.get('messages', [])
    return messages

def fetch_email_content(service, email_id):
    email = service.users().messages().get(userId='me', id=email_id, format='full').execute()
    payload = email.get('payload', {})
    headers = payload.get('headers', [])
    body = payload.get('body', {}).get('data', '')

    subject = next((header['value'] for header in headers if header['name'] == 'Subject'), '')
    return {'subject': subject, 'body': body, 'id': email_id}


def mask_pii(text):
    scrubber = scrubadub.Scrubber()
    masked_text = scrubber.clean(text)
    return masked_text


import google.generativeai as genai
import os

def get_category_from_llm(email_text, categories):
    
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])

    
    prompt = (
        f"You are an email categorization assistant. Here is the email:\n"
        f"---\n{email_text}\n---\n"
        f"Categories: {categories}\n"
        f"Respond with ONLY the matching category. If the email read has no matching category return nothing."
    )

   
    model = genai.GenerativeModel("gemini-1.5-flash")

    
    response = model.generate_content(prompt)

   
    if response and response.text:
        return response.text.strip()
    else:
        print("Failed to get category from LLM.")
        return None



def create_gmail_label(service, label_name):
    labels = service.users().labels().list(userId='me').execute().get('labels', [])
    existing_labels = [label['name'] for label in labels] 

    if label_name not in existing_labels:
        label_body = {"name": label_name, "labelListVisibility": "labelShow", "messageListVisibility": "show"}
        service.users().labels().create(userId='me', body=label_body).execute()
        print(f"Created label: {label_name}")
    else:
        print(f"Label '{label_name}' already exists.")


def apply_gmail_label(service, email_id, label_name):
    labels = service.users().labels().list(userId='me').execute().get('labels', [])
    label_id = next((label['id'] for label in labels if label['name'] == label_name), None)
    if label_id:
        service.users().messages().modify(
            userId='me',
            id=email_id,
            body={
                "addLabelIds": [label_id],
                "removeLabelIds": ["INBOX"]  
            }
        ).execute()


def process_new_emails(service, categories):
    emails = get_unread_emails(service, categories)
    for email_data in emails:
        email = fetch_email_content(service, email_data['id'])
        masked_content = mask_pii(email['subject'] + '\n' + email['body'])
        category = get_category_from_llm(masked_content, categories)

        if category:
            print(f"Categorizing email '{email['subject']}' into '{category}'")
            apply_gmail_label(service, email['id'], category)
        else:
            print(f"No matching category found for email: {email['subject']}")


if __name__ == "__main__":
    categories = ["Airline Booking", "password reset", "finance", "coding", "artwork", "sales", "meeting invites"]
    service = authenticate_gmail()

    for category in categories:
        create_gmail_label(service, category)

    print("Monitoring for new emails...")
    while True:
        process_new_emails(service, categories)
        time.sleep(10) 