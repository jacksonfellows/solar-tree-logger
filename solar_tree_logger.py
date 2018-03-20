
import httplib2
import os, json
import serial

from datetime import datetime

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/sheets.googleapis.com-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Solar Tree Logger'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'sheets.googleapis.com-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

SPREADSHEET_FILE = 'spreadsheet.json'
INTERVAL = 10

def main():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)

    # Get spreadsheet id and other metadata.
    # If spreadsheet file exists, read id from there and update file.
    # If not, create spreadsheet and write to file

    if not os.path.exists(SPREADSHEET_FILE):
        headers = create_row_data(['stringValue'] * 3, ['Time', 'Solar Tree Output (V)', 'Flat Panel Output (V)'])
        request = service.spreadsheets().create(body={
            'properties': {'title': 'Solar Tree Logs'},
            'sheets': [{'data': [{'rowData': headers}]}]
            })
    else:
        spreadsheet_id = json.load(open(SPREADSHEET_FILE, 'r'))['spreadsheetId']
        request = service.spreadsheets().get(spreadsheetId=spreadsheet_id, includeGridData=False)

    spreadsheet_data = request.execute()
    json.dump(spreadsheet_data, open(SPREADSHEET_FILE, 'w'))
    spreadsheet_id = spreadsheet_data['spreadsheetId']
    sheet_id = spreadsheet_data['sheets'][0]['properties']['sheetId']

    # Read serial data from Arduino
    # Collect averages and append to the Google Sheet after a set number of points are read

    ser = serial.Serial('COM3', 9600)
    while True:
        averages = []
        i = 0
        timestamp = str(datetime.now())
        while i < INTERVAL:
            voltages = [float(x) for x in ser.readline().split(b',')]
            for v in range(len(voltages)):
                if len(averages) <= v:
                    averages.append(0)
                averages[v] += voltages[v]
            i += 1
        for a in range(len(averages)):
            averages[a] /= INTERVAL

        row = create_row_data(['stringValue'] + ['numberValue'] * 2, [timestamp] + [round(x, 1) for x in averages])
        request = service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={
                'requests': [{'appendCells': {'sheetId': sheet_id, 'fields': '*', 'rows': [row]}}]
            })
        response = request.execute()

def create_row_data(types, data):
    return {'values': [{'userEnteredValue': {types[i]: data[i]}} for i in range(len(data))]}

if __name__ == '__main__':
    main()
