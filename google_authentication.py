import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from config import CONFIG

"""
Based on 
https://developers.google.com/docs/api/quickstart/python

To allow access:
1. go to https://console.cloud.google.com, enable g-sheet and g-mail apis
2. go to OAuth consent screen -> internal -> fill fields and continue
3. go to Credentials -> Create credentials -> OAuth client ID -> fill fields -> download json
"""


# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly',
          'https://www.googleapis.com/auth/gmail.readonly',
          'https://www.googleapis.com/auth/gmail.send']

CREDENTIALS = CONFIG['credentials']['path']


def load_or_generate_credentials(scopes, credentials_file=CREDENTIALS):
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('authentication/token.json'):
        creds = Credentials.from_authorized_user_file('authentication/token.json', scopes)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_file, scopes)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('authentication/token.json', 'wt', encoding='utf-8') as token:
            token.write(creds.to_json())
    return creds


GOOGLE_CREDENTIALS = load_or_generate_credentials(SCOPES)
