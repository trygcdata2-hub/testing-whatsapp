import json
import gspread
from google.oauth2.service_account import Credentials

SERVICE_ACCOUNT_FILE = 'operations-511207-eb43144fc000.json'
SPREADSHEET_ID = '1cmG2xWjcbF-76YOcvPKyn1x_BciElT3F3gyFemE_Kq0'

scopes = [
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]

creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
client = gspread.authorize(creds)

sheet = client.open_by_key(SPREADSHEET_ID)

print(f"Spreadsheet Title: {sheet.title}")
worksheets = sheet.worksheets()
print(f"Total Worksheets: {len(worksheets)}")

summary = {}
for ws in worksheets:
    print(f"\n--- Worksheet: '{ws.title}' (id: {ws.id}) ---")
    data = ws.get_all_values()
    print(f"Rows: {len(data)}, Cols: {len(data[0]) if data else 0}")
    if data:
        print("Header / First 5 rows:")
        for r_idx, row in enumerate(data[:5]):
            # Print non-empty columns or first 10
            row_preview = [c for c in row if c != ''][:10]
            print(f"  Row {r_idx}: {row_preview}")
    summary[ws.title] = {
        'id': ws.id,
        'rowCount': len(data),
        'preview': data[:5] if data else []
    }

with open('scratch_sheets_summary.json', 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print("\nDone reading spreadsheet.")
