import os
import datetime
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import Any, List

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
token_path = 'credentials/token.json'
secret_path = 'credentials/client_secret.json'

def get_credentials() -> Credentials:
    """
    Function that will connect to gsheet and getting credentials. If the token is present and/or still valid then it just refresh it.
    Returns:
    - creds: google Credentials
    """

    creds = None

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(secret_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path,'w') as token:
            token.write(creds.to_json())
    
    return creds

def get_service_connector() -> Any:
    """
    Function that returns the service varible needed for accessing Gsheet API.
    Args:
    - creds: gg credentials

    Returns:
    - service: the variable to access gsheet API
    """
    creds = get_credentials()

    try:
        service = build('sheets', 'v4', credentials=creds)
        return service
    except HttpError as err:
        print(err)

def extract_range_values_from_sheet(sheetAPI: Any, spreadsheetId: str, range: str) -> list:
    """
    Function that extracts data from a spreadsheet range
    Args:
    - sheetAPI, the gg spread API connector
    - spreadsheetId, the identifier of the spreadsheet
    - range, the range of the cells to select
    Returns:
    - list of extracted rows
    """
    result = sheetAPI.values().get(
        spreadsheetId=spreadsheetId, 
        range=range
    ).execute()
    return result.get('values',[])
    

def extract_info_from_sheet_id(sheet_id: str) -> dict:
    """
    Function that extracts all the information from chess scoresheet template and convert them into a dictionary
    """
    try:
        service = get_service_connector()
        sheetAPI = service.spreadsheets()
        fileInfo = sheetAPI.get(spreadsheetId=sheet_id).execute()
        fileName = fileInfo['properties']['title'] #we are going to save all the matches by date, hence the date is gathered directly from file name
        print("Found title", fileName)
        date = datetime.datetime.strptime(fileName, '%Y%m%d')
        date = date.strftime('%Y.%m.%d')
        print("Match played on", date)
        pgn = dict()
        
        for sheet in fileInfo['sheets']:
            sheetTitle = sheet['properties']['title']
            print("Looping in the sheet; title", sheetTitle)
            pgn[sheetTitle] = dict()
            pgn[sheetTitle]['properties'] = dict()

            pgn[sheetTitle]['properties']['Date'] = date
            pgn[sheetTitle]['properties']['Event'] = sheetTitle

            #Extract meta info
            RANGE_NAME_METADATA = f"'{sheetTitle}'!B5:G7"
            rows = extract_range_values_from_sheet(sheetAPI, sheet_id, RANGE_NAME_METADATA)
            for row in rows:
                if 'WHITE (name)' in row:
                    pgn[sheetTitle]['properties']['White'] = row[row.index('WHITE (name)') + 2]
                if 'BLACK (name)' in row:
                    pgn[sheetTitle]['properties']['Black'] = row[row.index('BLACK (name)') + 2]
                if 'PLACE' in row:
                    pgn[sheetTitle]['properties']['Site'] = row[row.index('PLACE') + 2]

            RANGE_NAME_RESULT = f"'{sheetTitle}'!D50"
            matchResult = extract_range_values_from_sheet(sheetAPI, sheet_id, RANGE_NAME_RESULT)[0][0]
            res = ''
            if matchResult == 'WHITE WON' or matchResult == 'BLACK RESIGNED':
                res = '1-0'
            elif matchResult == 'BLACK WON' or matchResult == 'WHITE RESIGNED':
                res = '0-1'
            else:
                res = '1/2-1/2'
            pgn[sheetTitle]['properties']['Result'] = res

            #Extract match and convert into a string            
            columns = ["B9:D49","E9:G49"]
            moves = ""
            for column in columns:
                RANGE_NAME = f"'{sheetTitle}'!{column}"
                rows =  extract_range_values_from_sheet(sheetAPI, sheet_id, RANGE_NAME)
                for row in rows:
                    if len(row)==1: #checking that there is at least a move otherwise the match is finished
                        break
                    if len(row) == 2:
                        line = f"{row[0]}. {row[1]} "
                    else:
                        line = f"{row[0]}. {row[1]} {row[2]} "                    
                    moves += line
            pgn[sheetTitle]['moves'] = moves
                
        
        for key in pgn: #the first key of iteration is the match
            with open(f'pgns/{fileName}__{key}.pgn','w') as f:
                sheetProperties = pgn[key]['properties']
                for property in sheetProperties:
                    f.write(f'[{property} "{sheetProperties[property]}"]\n')
                f.write(f"\n{pgn[key]['moves']}")
        
    except HttpError as err:
        print(err)