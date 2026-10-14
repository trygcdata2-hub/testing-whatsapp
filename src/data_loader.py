import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from .config import (
    BASE_DIR,
    DATA_DIR,
    WHATSAPP_DATA_PATH,
    WHATSAPP_DATA_CSV_PATH,
    WHATSAPP_LINES_PATH,
    CAMPAIGNS_PATH,
    CAMPAIGN_INFLUENCERS_PATH,
    INFLUENCERS_MASTER_PATH,
    SERVICE_ACCOUNT_FILE,
    GOOGLE_SHEET_ID,
    GOOGLE_SHEETS_SCOPES,
    ACTIVE_INFLUENCER_STATUSES
)

def load_whatsapp_lines() -> pd.DataFrame:
    """Loads the mapping between whatsappAccId, line_name, and phone."""
    if not WHATSAPP_LINES_PATH.exists():
        raise FileNotFoundError(f"WhatsApp lines file not found at {WHATSAPP_LINES_PATH}")
    df = pd.read_excel(WHATSAPP_LINES_PATH)
    for col in df.columns:
        df[col] = df[col].astype(str)
    return df

def load_google_sheet_tasks(sheet_name: str = "what's app tasks") -> pd.DataFrame:
    """
    Reads tasks from the Google Spreadsheet in STRICT READ-ONLY mode.
    Sheet options: 'what's app tasks', 'Tasks ( GC )', 'NUMBERS Status'.
    """
    if not SERVICE_ACCOUNT_FILE.exists():
        return pd.DataFrame()
        
    try:
        creds = Credentials.from_service_account_file(
            str(SERVICE_ACCOUNT_FILE),
            scopes=GOOGLE_SHEETS_SCOPES
        )
        client = gspread.authorize(creds)
        sheet = client.open_by_key(GOOGLE_SHEET_ID)
        ws = sheet.worksheet(sheet_name)
        data = ws.get_all_values()
        
        if not data:
            return pd.DataFrame()
            
        headers = [f"col_{i}" if not data[0][i].strip() else data[0][i].strip() for i in range(len(data[0]))]
        df = pd.DataFrame(data[1:], columns=headers)
        return df
    except Exception as e:
        print(f"Warning: Could not load sheet '{sheet_name}' from Google Sheets API: {e}")
        return pd.DataFrame()

def sync_tasks_from_google_sheets() -> dict:
    """
    STRICT READ-ONLY: Connects to the official Google Spreadsheet,
    fetches 'what's app tasks' and 'Tasks ( GC )',
    and updates the fast local Parquet cache layer.
    """
    if not SERVICE_ACCOUNT_FILE.exists():
        return {"success": False, "error": f"Credentials file not found at {SERVICE_ACCOUNT_FILE}"}
    
    try:
        creds = Credentials.from_service_account_file(
            str(SERVICE_ACCOUNT_FILE),
            scopes=GOOGLE_SHEETS_SCOPES
        )
        client = gspread.authorize(creds)
        sheet = client.open_by_key(GOOGLE_SHEET_ID)
        
        results = {}
        cached_wa_p = DATA_DIR / "cached_whatsapp_tasks.parquet"
        cached_gc_p = DATA_DIR / "cached_gc_tasks.parquet"
        
        # 1. 'what's app tasks'
        try:
            ws_wa = sheet.worksheet("what's app tasks")
            rows_wa = ws_wa.get_all_values()
            if rows_wa:
                headers = [f"col_{i}" if not rows_wa[0][i].strip() else rows_wa[0][i].strip() for i in range(len(rows_wa[0]))]
                df_wa = pd.DataFrame(rows_wa[1:], columns=headers).astype(str)
                df_wa.to_parquet(cached_wa_p, index=False)
                results["whatsapp_tasks_rows"] = len(df_wa)
        except Exception as e:
            results["whatsapp_tasks_error"] = str(e)
            
        # 2. 'Tasks ( GC )'
        try:
            ws_gc = sheet.worksheet("Tasks ( GC )")
            rows_gc = ws_gc.get_all_values()
            if rows_gc:
                headers = [f"col_{i}" if not rows_gc[0][i].strip() else rows_gc[0][i].strip() for i in range(len(rows_gc[0]))]
                df_gc = pd.DataFrame(rows_gc[1:], columns=headers).astype(str)
                df_gc.to_parquet(cached_gc_p, index=False)
                results["gc_tasks_rows"] = len(df_gc)
        except Exception as e:
            results["gc_tasks_error"] = str(e)
            
        results["success"] = "whatsapp_tasks_rows" in results or "gc_tasks_rows" in results
        return results
    except Exception as e:
        return {"success": False, "error": str(e)}

def load_tasks_data(force_refresh_google_sheets: bool = False) -> pd.DataFrame:
    """
    Loads tasks from either fast local Parquet cache or live Google Sheets.
    If force_refresh_google_sheets=True or cache is missing, syncs directly from Google Sheets.
    Combines 'what's app tasks' and 'Tasks ( GC )'.
    """
    cached_wa_p = DATA_DIR / "cached_whatsapp_tasks.parquet"
    cached_gc_p = DATA_DIR / "cached_gc_tasks.parquet"
    
    # If forced or if cache does not exist, fetch live from Google Sheets
    if force_refresh_google_sheets or not (cached_wa_p.exists() and cached_gc_p.exists()):
        sync_res = sync_tasks_from_google_sheets()
        if sync_res.get("success"):
            print(f"Synced roster from Google Sheets: {sync_res}")
            
    tasks_dfs = []
    
    # 1. Read from local Parquet cache
    if cached_wa_p.exists():
        try:
            tasks_dfs.append(pd.read_parquet(cached_wa_p))
        except Exception:
            pass
    if cached_gc_p.exists():
        try:
            tasks_dfs.append(pd.read_parquet(cached_gc_p))
        except Exception:
            pass
            
    # 2. Fallback to local Excel files in data/ if parquet failed
    if not tasks_dfs:
        for fn in ["tasks.xlsx", "Chat Team 's Tasks.xlsx", "google_sheets_tasks.xlsx"]:
            excel_p = DATA_DIR / fn
            if excel_p.exists():
                try:
                    xls = pd.ExcelFile(excel_p)
                    for sname in xls.sheet_names:
                        if any(k in sname.lower() for k in ["what's app tasks", "whats app tasks", "tasks ( gc )"]):
                            tasks_dfs.append(pd.read_excel(xls, sheet_name=sname, dtype=str))
                except Exception as e:
                    print(f"Error reading local tasks Excel {excel_p}: {e}")
                
    # 3. Direct Google Sheets fallback if no local files exist
    if not tasks_dfs:
        for sname in ["what's app tasks", "Tasks ( GC )"]:
            df = load_google_sheet_tasks(sname)
            if not df.empty:
                tasks_dfs.append(df)
                
    if tasks_dfs:
        combined = pd.concat(tasks_dfs, ignore_index=True).drop_duplicates()
        return combined
        
    return pd.DataFrame()

def load_raw_messages() -> pd.DataFrame:
    """Loads the raw WhatsApp messages export (Parquet or CSV)."""
    if WHATSAPP_DATA_PATH.exists():
        df = pd.read_parquet(WHATSAPP_DATA_PATH)
    elif WHATSAPP_DATA_CSV_PATH.exists():
        df = pd.read_csv(WHATSAPP_DATA_CSV_PATH, dtype=str, encoding="utf-8-sig").drop_duplicates()
    else:
        raise FileNotFoundError(f"WhatsApp data file not found at {WHATSAPP_DATA_PATH} or {WHATSAPP_DATA_CSV_PATH}")
    return df

def load_campaigns() -> pd.DataFrame:
    """Loads the active/historical campaigns summary."""
    if not CAMPAIGNS_PATH.exists():
        raise FileNotFoundError(f"Campaigns file not found at {CAMPAIGNS_PATH}")
    try:
        df = pd.read_csv(CAMPAIGNS_PATH, dtype=str, encoding="utf-8-sig")
    except Exception:
        df = pd.read_excel(CAMPAIGNS_PATH, dtype=str)
    return df

def load_campaign_influencers() -> pd.DataFrame:
    """Loads the campaign influencer booking statuses."""
    if not CAMPAIGN_INFLUENCERS_PATH.exists():
        raise FileNotFoundError(f"Campaign influencers file not found at {CAMPAIGN_INFLUENCERS_PATH}")
    df = pd.read_csv(CAMPAIGN_INFLUENCERS_PATH, dtype=str, encoding="utf-8-sig")
    if 'status_id' in df.columns:
        df['status_id'] = pd.to_numeric(df['status_id'], errors='coerce')
        df['is_active_influencer'] = df['status_id'].isin(ACTIVE_INFLUENCER_STATUSES)
    return df

def load_influencers_master() -> pd.DataFrame:
    """Loads the master influencer profile directory."""
    if not INFLUENCERS_MASTER_PATH.exists():
        raise FileNotFoundError(f"Influencers master file not found at {INFLUENCERS_MASTER_PATH}")
    df = pd.read_csv(INFLUENCERS_MASTER_PATH, dtype=str, encoding="utf-8-sig")
    return df
