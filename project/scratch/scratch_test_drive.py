from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import io
from googleapiclient.http import MediaIoBaseDownload

SERVICE_ACCOUNT_FILE = 'operations-511207-eb43144fc000.json'
SPREADSHEET_ID = '1cmG2xWjcbF-76YOcvPKyn1x_BciElT3F3gyFemE_Kq0'

creds = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=['https://www.googleapis.com/auth/drive.readonly']
)

try:
    drive_service = build('drive', 'v3', credentials=creds)
    file_metadata = drive_service.files().get(fileId=SPREADSHEET_ID).execute()
    print("Drive API succeeded! File metadata:", file_metadata)
    
    # Try exporting as xlsx
    request = drive_service.files().export_media(
        fileId=SPREADSHEET_ID,
        mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
        print(f"Download {int(status.progress() * 100)}%.")
        
    with open('roster_sheet.xlsx', 'wb') as f:
        f.write(fh.getvalue())
    print("Successfully exported Google Sheet to roster_sheet.xlsx via Drive API!")

except Exception as e:
    print(f"Drive API Error: {e}")
