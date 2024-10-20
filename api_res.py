import os
import pickle
import time
import base64
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from dotenv import load_dotenv
import scrubadub
import google.generativeai as genai
from flask import Flask, request, jsonify

load_dotenv()

app = Flask(__name__)

# OAuth2 credentials
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

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
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    return build("gmail", "v1", credentials=creds)

def get_sent_emails(service):
    """Fetch all sent emails."""
    query = "in:sent" 
    results = service.users().messages().list(userId='me', q=query).execute()
    messages = results.get('messages', [])
    return messages

def has_response(service, thread_id):
    """Check if the sent email has a response."""
    thread = service.users().threads().get(userId='me', id=thread_id).execute()
    return len(thread.get('messages', [])) > 1 

def fetch_email_content(service, email_id):
    email = service.users().messages().get(userId='me', id=email_id, format='full').execute()
    payload = email.get('payload', {})
    headers = payload.get('headers', [])

    subject = next((header['value'] for header in headers if header['name'] == 'Subject'), '')
    to = next((header['value'] for header in headers if header['name'] == 'To'), '')

    body = get_email_body(payload)

    return {'subject': subject, 'body': body, 'to': to, 'threadId': email['threadId']}

def get_email_body(payload):
    """Helper function to retrieve the email body content, handling multipart emails."""
    if 'parts' in payload:
        parts = payload['parts']
        for part in parts:
            if part['mimeType'] == 'text/plain':
                return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
    else:
        body_data = payload.get('body', {}).get('data', '')
        if body_data:
            return base64.urlsafe_b64decode(body_data).decode('utf-8')

    return "No plain text content found."

def mask_pii(text):
    scrubber = scrubadub.Scrubber()
    masked_text = scrubber.clean(text)
    return masked_text

def generate_follow_up_email(chain_text):
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])

    prompt = (
        f"Create a polite follow-up email based on the following conversation:\n"
        f"---\n{chain_text}\n---\n"
        f"The follow-up should be concise, professional, and encourage a response. No work should be left to the user. The email should be complete in the sense it can be sent immediately and containing no blanks for the user to fill in."
    )

    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)

    if response and response.text:
        return response.text.strip()
    else:
        print("Failed to generate follow-up email.")
        return None

def create_draft_email(service, recipient, subject, body):
    """Create a draft email with the generated follow-up message."""
    message = {
        'raw': base64.urlsafe_b64encode(
            f"To: {recipient}\nSubject: {subject}\n\n{body}".encode('utf-8')
        ).decode('utf-8')
    }

    draft = service.users().drafts().create(userId='me', body={'message': message}).execute()
    print(f"Draft email created for {recipient}. Draft ID: {draft['id']}")

def process_sent_emails(service):
    emails = get_sent_emails(service)
    follow_up_needed = []

    for email_data in emails:
        email = fetch_email_content(service, email_data['id'])

        if not has_response(service, email['threadId']):
            print(f"Hey, I recommend you follow up with {email['to']}.")
            follow_up_needed.append(email)

    for email in follow_up_needed:
        masked_content = mask_pii(email['subject'] + '\n' + email['body'])
        follow_up_text = generate_follow_up_email(masked_content)

        if follow_up_text:
            print(f"Generated follow-up email for {email['to']}:")
            print(f"Subject: Follow-up on: {email['subject']}\n{follow_up_text}")

            create_draft_email(
                service,
                recipient=email['to'],
                subject=f"Follow-up on: {email['subject']}",
                body=follow_up_text
            )

@app.route('/process_emails', methods=['GET'])
def process_emails():
    service = authenticate_gmail()
    process_sent_emails(service)
    return jsonify({'message': 'Emails processed successfully'})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=6000, debug=True)
