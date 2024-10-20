import os
import pickle
import time
from flask import Flask, jsonify
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import scrubadub
from dotenv import load_dotenv
from datetime import datetime
import google.generativeai as genai

load_dotenv()

app = Flask(__name__)

# Google API scope
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

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
            print("Today's email summary:")
            print(summary)
            return summary
        else:
            print("No important content found.")
            return "No important content found."
    else:
        print("No emails received today.")
        return "No emails received today."


@app.route('/api/summarize_emails', methods=['POST'])
def summarize_emails_api():
    service = authenticate_gmail()
    summary = process_todays_emails(service)
    return jsonify({"message": "Email summarization complete", "summary": summary}), 200

import os
import pickle
import time
from flask import Flask, request, jsonify
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import scrubadub
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Google API scope
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

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

# --- Flask API Endpoint ---
@app.route('/api/categorize_emails', methods=['POST'])
def categorize_emails_api():
    data = request.get_json()
    categories = data.get('categories', [])

    if not categories:
        return jsonify({"error": "Missing 'categories' parameter"}), 400

    global running 
    running = True 
    
    service = authenticate_gmail()
    for category in categories:
        create_gmail_label(service, category)
    while running:
        process_new_emails(service, categories)
        time.sleep(10)

    return jsonify({"message": "Email categorization started in the background"}), 200

@app.route('/api/stop_categorization', methods=['POST'])
def stop_categorization_api():
    global running 
    running = False 
    return jsonify({"message": "Email categorization stopped"}), 200

import os
import pickle
import time
from flask import Flask, jsonify, request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import datetime
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Google API scope
SCOPES = ["https://www.googleapis.com/auth/calendar", 'https://www.googleapis.com/auth/gmail.readonly']

# Flag to control the loop
running = False

def authenticate_google_service():
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    if creds:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        creds = flow.run_local_server(port=0)

    with open("token.pickle", "wb") as token:
        pickle.dump(creds, token)

    calendar_service = build("calendar", "v3", credentials=creds)
    return calendar_service, creds

def get_unread_emails(service):
    results = service.users().messages().list(userId='me', q='is:unread').execute()
    messages = results.get('messages', [])
    return messages

def fetch_email_content(service, email_id):
    email = service.users().messages().get(userId='me', id=email_id, format='full').execute()
    payload = email.get('payload', {})
    headers = payload.get('headers', [])
    body = payload.get('body', {}).get('data', '')

    subject = next((header['value'] for header in headers if header['name'] == 'Subject'), '')
    return {'subject': subject, 'body': body, 'id': email_id}

def get_event_from_llm(email_text):
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])

    prompt = (
        "You are a helpful assistant that extracts event details from emails.\n"
        "Here's an email:\n"
        "---\n"
        f"{email_text}\n"
        "---\n"
        "If the email contains an event, provide the event details in this EXACT format:\n"
        "\n"
        "Event Title: <Event title here>\n"
        "Event Date: <Event date in YYYY-MM-DD format>\n"
        "Event Time: <Event time in HH:MM format (24-hour)>\n"
        "\n"
        "If the email doesn't contain an event, respond with 'No Event Found'."
    )

    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)

    if response and response.text and "No Event Found" not in response.text:
        return response.text.strip()
    else:
        print("No event found in the email.")
        return None

def create_google_calendar_event(service, event_title, event_date, event_time=None):
    """Creates a Google Calendar event, handling both all-day and timed events."""
    if event_time:
        start_datetime = f"{event_date}T{event_time}:00"
        end_datetime = (datetime.datetime.fromisoformat(start_datetime) + datetime.timedelta(hours=1)).isoformat()
        event_body = {
            "summary": event_title,
            "start": {"dateTime": start_datetime, "timeZone": "UTC"},
            "end": {"dateTime": end_datetime, "timeZone": "UTC"},
        }
    else:
        event_body = {
            "summary": event_title,
            "start": {"date": event_date},
            "end": {"date": event_date},
        }
    
    service.events().insert(calendarId='primary', body=event_body).execute()
    print(f"Added event: {event_title} on {event_date} at {event_time if event_time else 'All Day'}")

def event_exists(service, event_title, event_date, event_time=None):
    """Checks if an event with the same title, date, and optional time exists."""
    try:
        event_date = datetime.datetime.strptime(event_date, '%Y-%m-%d').date()
    except ValueError as e:
        print(f"Error parsing event date: {e}")
        return False

    timeMin = datetime.datetime.combine(event_date, datetime.time.min).isoformat() + 'Z'
    timeMax = datetime.datetime.combine(event_date + datetime.timedelta(days=1), datetime.time.min).isoformat() + 'Z'

    try:
        events_result = service.events().list(
            calendarId='primary',
            timeMin=timeMin,
            timeMax=timeMax,
            q=event_title,
            singleEvents=True
        ).execute()
        events = events_result.get('items', [])

        if event_time:
            # Check for events with matching time as well
            for event in events:
                start = event.get('start', {}).get('dateTime', '')
                if start and event_time in start:
                    return True
        return len(events) > 0
    except Exception as e:
        print(f"Error checking events: {e}")
        return False

def process_new_emails(calendar_service, gmail_service):
    emails = get_unread_emails(gmail_service)
    for email_data in emails:
        email = fetch_email_content(gmail_service, email_data['id'])
        event_info = get_event_from_llm(email['subject'] + '\n' + email['body'])

        if event_info:
            try:
                event_data = {}
                for line in event_info.strip().split('\n'):
                    if ': ' in line:
                        key, value = line.split(': ', 1)
                        event_data[key.strip()] = value.strip()
                    else:
                        print(f"Skipping malformed line: {line}")

                event_title = event_data.get('Event Title')
                event_date = event_data.get('Event Date')
                event_time = event_data.get('Event Time')  

                if event_title and event_date and not event_exists(calendar_service, event_title, event_date, event_time):
                    create_google_calendar_event(calendar_service, event_title, event_date, event_time)
            except (IndexError, ValueError, AttributeError) as e:
                print(f"Failed to parse event info: {event_info}. Error: {e}")

# --- Flask API Endpoint ---
@app.route('/api/linear_updates', methods=['POST'])
def linear_updates_api():
    global running
    if not running:
        calendar_service, creds = authenticate_google_service()
        gmail_service = build("gmail", "v1", credentials=creds)
        running = True
        while running:
            process_new_emails(calendar_service, gmail_service)
            time.sleep(10)  # Adjust the polling interval
    return jsonify({"message": "Linear updates started"}), 200

@app.route('/api/stop_linear_updates', methods=['POST'])
def stop_linear_updates_api():
    global running
    running = False
    return jsonify({"message": "Linear updates stopped"}), 200

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
