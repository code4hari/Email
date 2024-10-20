import os
import pickle
import google.auth
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import time
from google_auth_oauthlib.flow import InstalledAppFlow
from dotenv import load_dotenv
import google.generativeai as genai
import datetime

load_dotenv()

# Google API scope
SCOPES = ["https://www.googleapis.com/auth/calendar", 'https://www.googleapis.com/auth/gmail.readonly']

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
        "```\n"
        "Event Title: <Event title here>\n"
        "Event Date: <Event date in YYYY-MM-DD format>\n"
        "Event Time: <Event time in HH:MM format (24-hour)>\n"
        "```\n"
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

if __name__ == "__main__":
    calendar_service, creds = authenticate_google_service()
    gmail_service = build("gmail", "v1", credentials=creds)
    print("Monitoring for new emails...")
    while True:
        process_new_emails(calendar_service, gmail_service)
        time.sleep(10)
