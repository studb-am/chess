from __future__ import print_function
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = '11w6BrHduFrtbp54CY9xh5bpWTmXUJ9UeHqMUVGvKIZo'
SAMPLE_RANGE_NAME = 'Sheet1!B9:E33'


def main():
    """
    Show the basic usage of Google Sheet API. It prints values from a sample gsheet
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('credentials/token.json'):
        creds = Credentials.from_authorized_user_file('credentials/token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials/client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('credentials/token.json','w') as token:
            token.write(creds.to_json())

    try:
        service = build('sheets','v4', credentials=creds)

        #call sheet API
        sheet = service.spreadsheets()
        result = sheet.values().get(
            spreadsheetId=SAMPLE_SPREADSHEET_ID, 
            range=SAMPLE_RANGE_NAME
        ).execute()
        values = result.get('values', [])

        if not values:
            print('No data found')
            return
        print('Name, Major:')
        for row in values:
            # Print columns A and E, which correspond to indices 0 and 4.
            print(f"{row[0]}, {row[3]}")
    except HttpError as err:
        print(err)

if __name__ == '__main__':
    main()