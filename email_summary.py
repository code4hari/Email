import os
import pickle
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import scrubadub
import time
from google_auth_oauthlib.flow import InstalledAppFlow
from dotenv import load_dotenv
from datetime import datetime
import google.generativeai as genai

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


def get_todays_emails(service):
    today = datetime.now().strftime('%Y/%m/%d')
    query = f'after:{today}'

    results = service.users().messages().list(userId='me', q=query).execute()
    messages = results.get('messages', [])
    return messages

import base64

def fetch_email_content(service, email_id):
    email = service.users().messages().get(userId='me', id=email_id, format='full').execute()
    payload = email.get('payload', {})
    headers = payload.get('headers', [])

    # Fetch subject
    subject = next((header['value'] for header in headers if header['name'] == 'Subject'), '')

    # Extract the body of the email (checking for multipart)
    body = get_email_body(payload)

    return {'subject': subject, 'body': body, 'id': email_id}

def get_email_body(payload):
    """Helper function to retrieve the email body content, handling multipart emails."""
    if 'parts' in payload:
        parts = payload['parts']
        for part in parts:
            if part['mimeType'] == 'text/plain':
                return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
    else:
        # Single-part email body
        body_data = payload.get('body', {}).get('data', '')
        if body_data:
            return base64.urlsafe_b64decode(body_data).decode('utf-8')

    return "No plain text content found."


    
def mask_pii(text):
    scrubber = scrubadub.Scrubber()
    masked_text = scrubber.clean(text)
    return masked_text


def summarize_email_content(email_texts):
    
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])

    
    prompt = (
        f"First summarize all the emails recieved today in one paragraph atleast 500 words. Then summarize each individual email recieved today also identifying which email you are summarizing. Finally, print the inportant details from all the emails you think should be highlights, and specify which emails these important details came from:\n"
        f"---\n" + '\n'.join(email_texts) + "\n---"
    )

    
    model = genai.GenerativeModel("gemini-1.5-flash")

    response = model.generate_content(prompt)

  
    if response and response.text:
        return response.text.strip()
    else:
        print("Failed to get summary from LLM.")
        return None


def process_todays_emails(service):
    emails = get_todays_emails(service)
    email_texts = []

    for email_data in emails:
        email = fetch_email_content(service, email_data['id'])
        masked_content = mask_pii(email['subject'] + '\n' + email['body'])
        email_texts.append(masked_content)

    if email_texts:
        summary = summarize_email_content(email_texts)
        if summary:
            print("your emails content is", email_texts)
            print("Today's email summary:")
            print(summary)
        else:
            print("No important content found.")
    else:
        print("No emails received today.")


if __name__ == "__main__":
    service = authenticate_gmail()
    print("Checking for today's emails...")

    while True:
        process_todays_emails(service)
        time.sleep(86400) 
