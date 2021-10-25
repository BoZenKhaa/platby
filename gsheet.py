from __future__ import print_function

import pandas as pd
from googleapiclient.discovery import build

from config import CONFIG
from google_authentication import GOOGLE_CREDENTIALS

# The ID and range of a sample spreadsheet.
SPREADSHEET_ID = CONFIG['spreadsheet']['id']
SHEET_NAME = CONFIG['spreadsheet']['sheet_name']



class Sheets:
    def __init__(self, sheet_id):
        self.sheet_id = sheet_id
        self.creds = GOOGLE_CREDENTIALS
        self.service = build('sheets', 'v4', credentials=self.creds)

    def get_available_sheet_info(self):
        sheet_metadata = self.service.spreadsheets().get(spreadsheetId=self.sheet_id).execute()

        properties = sheet_metadata.get('sheets')
        for item in properties:
            sheet_id = (item.get("properties").get('sheetId'))
            print(item)

    def get_sheet_names(self):
        sheet_metadata = self.service.spreadsheets().get(spreadsheetId=self.sheet_id).execute()
        properties = sheet_metadata.get('sheets')

        return [prop['properties']['title'] for prop in properties]

    def get_dataframe(self, sheet_name: str,
                      colnames_range: str = "A1:Z",
                      values_range: str = "A2:Z"):
        column_names = self.service.spreadsheets().values().get(spreadsheetId=self.sheet_id,
                                                                range=f"'{sheet_name}'!{colnames_range}").execute()
        values = self.service.spreadsheets().values().get(spreadsheetId=self.sheet_id,
                                                          range=f"'{sheet_name}'!{values_range}").execute()

        return pd.DataFrame(values['values'], columns=column_names['values'][0])


if __name__ == '__main__':
    sheets = Sheets(SPREADSHEET_ID)
    # sheets.get_available_sheet_info()

    sheet_metadata = sheets.service.spreadsheets().get(spreadsheetId=sheets.sheet_id).execute()
    properties = sheet_metadata.get('sheets')
