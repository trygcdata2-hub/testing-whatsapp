import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from .config import (
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
    df['whatsappAccId'] = df['whatsappAccId'].astype(str)
    return df

def load_google_sheet_tasks(sheet_name: str = "what's app tasks") -> pd.DataFrame:
    """
    Reads tasks from the Google Spreadsheet in STRICT READ-ONLY mode.
    Sheet options: 'what's app tasks', 'Tasks ( GC )', 'NUMBERS Status'.
    """
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
