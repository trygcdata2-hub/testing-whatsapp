import json
import gspread
from google.oauth2.service_account import Credentials

SERVICE_ACCOUNT_FILE = 'operations-511207-eb43144fc000.json'
SPREADSHEET_ID = '1cmG2xWjcbF-76YOcvPKyn1x_BciElT3F3gyFemE_Kq0'

scopes = [
    'https://www.googleapis.com/auth/spreadsheets.readonly'
]

creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
client = gspread.authorize(creds)

sheet = client.open_by_key(SPREADSHEET_ID)

summary = {
    'title': sheet.title,
    'total_worksheets': len(sheet.worksheets()),
    'sheets': []
}

for ws in sheet.worksheets():
    data = ws.get_all_values()
    sheet_info = {
        'title': ws.title,
        'id': ws.id,
        'rows': len(data),
        'cols': len(data[0]) if data else 0,
        'header': data[0] if len(data) > 0 else [],
        'sample_rows': data[1:6] if len(data) > 1 else []
    }
    summary['sheets'].append(sheet_info)

with open('google_sheets_structure.json', 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print("Successfully inspected all worksheets and saved to google_sheets_structure.json")
