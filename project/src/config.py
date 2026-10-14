import os
from pathlib import Path

# Base Paths - robust to running from repo root or cloud subfolder
_resolved = Path(__file__).resolve()
_root_candidate = _resolved.parent
while _root_candidate != _root_candidate.parent:
    if (_root_candidate / "data").exists() and (_root_candidate / "data" / "last_month_s_data.parquet").exists():
        break
    if (_root_candidate / "requirements.txt").exists():
        break
    _root_candidate = _root_candidate.parent

BASE_DIR = _root_candidate
DATA_DIR = BASE_DIR / "data"
if not DATA_DIR.exists() and (BASE_DIR / "project" / "data").exists():
    DATA_DIR = BASE_DIR / "project" / "data"

SCRIPTS_DIR = BASE_DIR / "src"

# Data Files
WHATSAPP_DATA_PATH = DATA_DIR / "last_month_s_data.parquet"
WHATSAPP_DATA_CSV_PATH = DATA_DIR / "last_month_s_data.csv"
WHATSAPP_LINES_PATH = DATA_DIR / "whatsapp_lines.xlsx"
CAMPAIGNS_PATH = DATA_DIR / "campaigns_since_1may.csv"
CAMPAIGN_INFLUENCERS_PATH = DATA_DIR / "campaign_influencers.csv"
INFLUENCERS_MASTER_PATH = DATA_DIR / "influencers_master.csv"
DB_DOCS_PATH = DATA_DIR / "documentations for the database.xlsx"

# Google Sheets Configuration (STRICTLY READ-ONLY)
def _find_service_account_file() -> Path:
    for search_dir in [BASE_DIR, BASE_DIR / "project", Path.cwd(), Path.cwd() / "project"]:
        if search_dir.exists():
            matched = sorted(list(search_dir.glob("operations-*.json")), key=lambda p: p.stat().st_mtime, reverse=True)
            if matched:
                return matched[0]
    return BASE_DIR / "operations-511207-c2981485761f.json"

SERVICE_ACCOUNT_FILE = _find_service_account_file()
GOOGLE_SHEET_ID = "1cmG2xWjcbF-76YOcvPKyn1x_BciElT3F3gyFemE_Kq0"
GOOGLE_SHEETS_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly"
]

# Shift Timing Definitions (Egypt Local Time)
SHIFT_HOURS = {
    "Morning": {"start": "09:00", "end": "17:00"},
    "Between": {"start": "17:00", "end": "01:00"},
    "Night":   {"start": "01:00", "end": "09:00"}
}

# Status Definitions from 'documentations for the database.xlsx'
STATUS_MAP = {
    0: "Added to List",
    1: "Confirmation",
    2: "Visit (Missing Coverage)",
    3: "Missed Visit",
    4: "Cancel from influencer",
    5: "Waiting",
    6: "Incorrect",
    7: "Posted / Completed Coverage",
    8: "Delivery (Missing Coverage)",
    9: "Not Delivery / Missed",
    10: "Reject",
    11: "Share",
    12: "Not Share",
    13: "Post",
    14: "Not Post",
    15: "Approved",
    17: "Canceled from client",
    18: "Reject from Client"
}

# Ground Truth Rule: Active Influencers who participated
ACTIVE_INFLUENCER_STATUSES = [2, 7, 8, 11, 13]
