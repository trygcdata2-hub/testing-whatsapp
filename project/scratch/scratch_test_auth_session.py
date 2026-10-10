from google.oauth2.service_account import Credentials
from google.auth.transport.requests import AuthorizedSession

SERVICE_ACCOUNT_FILE = 'operations-511207-eb43144fc000.json'
SPREADSHEET_ID = '1cmG2xWjcbF-76YOcvPKyn1x_BciElT3F3gyFemE_Kq0'

scopes = [
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]

creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
authed_session = AuthorizedSession(creds)

print("Testing Drive export endpoint...")
drive_export_url = f"https://www.googleapis.com/drive/v3/files/{SPREADSHEET_ID}/export?mimeType=application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
r_drive = authed_session.get(drive_export_url)
print(f"Drive export status: {r_drive.status_code}")
if r_drive.status_code == 200:
    with open("roster_sheet.xlsx", "wb") as f:
        f.write(r_drive.content)
    print("Saved to roster_sheet.xlsx successfully via Drive export!")
else:
    print("Drive error response:", r_drive.text[:300])

print("\nTesting Sheets API endpoint...")
sheets_url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}"
r_sheets = authed_session.get(sheets_url)
print(f"Sheets API status: {r_sheets.status_code}")
if r_sheets.status_code == 200:
    print("Sheets API success! Title:", r_sheets.json().get('properties', {}).get('title'))
else:
    print("Sheets API error response:", r_sheets.text[:300])
