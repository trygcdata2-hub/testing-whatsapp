import json
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

SERVICE_ACCOUNT_FILE = 'operations-511207-eb43144fc000.json'
SPREADSHEET_ID = '1cmG2xWjcbF-76YOcvPKyn1x_BciElT3F3gyFemE_Kq0'

creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=['https://www.googleapis.com/auth/spreadsheets.readonly'])
client = gspread.authorize(creds)
sheet = client.open_by_key(SPREADSHEET_ID)

# Inspect "what's app tasks"
ws_wa = sheet.worksheet("what's app tasks")
data_wa = ws_wa.get_all_values()
df_wa = pd.DataFrame(data_wa[1:], columns=[f"col_{i}" if not data_wa[0][i] else data_wa[0][i] for i in range(len(data_wa[0]))])

# Inspect "Tasks ( GC )"
ws_gc = sheet.worksheet("Tasks ( GC )")
data_gc = ws_gc.get_all_values()
df_gc = pd.DataFrame(data_gc[1:], columns=[f"col_{i}" if not data_gc[0][i] else data_gc[0][i] for i in range(len(data_gc[0]))])

# Inspect "NUMBERS Status"
ws_num = sheet.worksheet("NUMBERS Status")
data_num = ws_num.get_all_values()
df_num = pd.DataFrame(data_num[1:], columns=[f"col_{i}" if not data_num[0][i] else data_num[0][i] for i in range(len(data_num[0]))])

with open('deep_sheets_analysis.txt', 'w', encoding='utf-8') as f:
    f.write("=== NUMBERS Status ===\n")
    f.write(df_num.to_string() + "\n\n")
    
    f.write("=== what's app tasks summary ===\n")
    f.write(f"Total Rows: {len(df_wa)}\n")
    f.write(f"Columns: {list(df_wa.columns)}\n")
    f.write(f"Unique Tasks: {df_wa['Task'].unique()[:20]}\n")
    f.write(f"Sample Live Response entries:\n")
    f.write(df_wa[df_wa['Task'].str.contains('Live|Response|Line', case=False, na=False)].head(15).to_string() + "\n\n")
    
    f.write("=== Tasks ( GC ) summary ===\n")
    f.write(f"Total Rows: {len(df_gc)}\n")
    f.write(f"Columns: {list(df_gc.columns[:10])}\n")
    f.write(f"Unique Tasks: {df_gc['Task'].unique()[:20]}\n")
    f.write(f"Sample Live Response entries:\n")
    f.write(df_gc[df_gc['Task'].str.contains('Live|Response|Line', case=False, na=False)].head(15).to_string() + "\n\n")

print("Deep analysis complete.")
