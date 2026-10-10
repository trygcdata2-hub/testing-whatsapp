import pandas as pd
import json

with open('google_sheets_structure.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for s in data['sheets']:
    if s['title'] in ["what's app tasks", "Tasks ( GC )", "Handover ( GC )"]:
        df = pd.DataFrame(s['sample_rows'])
        print(f"Sheet: {s['title']}, Total Rows: {s['rows']}")

# Let's inspect unique dates in the sheets
import gspread
from google.oauth2.service_account import Credentials

creds = Credentials.from_service_account_file('operations-511207-eb43144fc000.json', scopes=['https://www.googleapis.com/auth/spreadsheets.readonly'])
client = gspread.authorize(creds)
sheet = client.open_by_key('1cmG2xWjcbF-76YOcvPKyn1x_BciElT3F3gyFemE_Kq0')

ws_wa = sheet.worksheet("what's app tasks")
col_dates_wa = ws_wa.col_values(1)
unique_dates_wa = list(set([d for d in col_dates_wa if d and d != '65' and d != 'Date']))

ws_gc = sheet.worksheet("Tasks ( GC )")
col_dates_gc = ws_gc.col_values(1)
unique_dates_gc = list(set([d for d in col_dates_gc if d and d != ' ,mggggggg' and d != 'Date']))

print(f"\nwhat's app tasks - unique date entries count: {len(unique_dates_wa)}")
print("Sample dates WA:", sorted(unique_dates_wa)[:15])

print(f"\nTasks ( GC ) - unique date entries count: {len(unique_dates_gc)}")
print("Sample dates GC:", sorted(unique_dates_gc)[:15])
