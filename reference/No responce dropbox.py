import os
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# =============================================================
#  CONFIGURATION
# =============================================================
SOURCE_FOLDERS = [
    r"C:\Users\DA-05\Dropbox\GC - operation live\Campaign Source\4- KSA\Grand Community\Active Campaigns",
    r"C:\Users\DA-05\Dropbox\GC - operation live\Campaign Source\4- KSA\ELITE\Active Campaigns",
    r"C:\Users\DA-05\Dropbox\GC - operation live\Campaign Source\3- UAE\Grand Community\Active Campaigns",
    r"C:\Users\DA-05\Dropbox\GC - operation live\Campaign Source\3- UAE\Elite\Active Campaigns",
    r"C:\Users\DA-05\Dropbox\GC - operation live\Campaign Source\2- KW\Grand Community\Active Campaigns",
    r"C:\Users\DA-05\Dropbox\GC - operation live\Campaign Source\2- KW\Elite\Active Campaigns",
    r"C:\Users\DA-05\Dropbox\GC - operation live\Campaign Source\1- EGY\Active Campaigns\Active Campaigns",
]

SPREADSHEET_ID = "1VM8LGRFL35APOK7_l8wf8B2zFOM6iPnZVdmUcwK4Yys"
SERVICE_ACCOUNT_JSON = r"C:\Users\DA-05\Desktop\campaign-extractor-41062b9a599c.json"

SHEET_NAME = "Pending Users"

# Flexible status matching - handles manual typos
TARGET_STATUS_PATTERNS = [
    ("Block", ["block", "blok", "bloc", "blo", "blc", "bk"]),
    ("No Response", ["no response", "noresponse", "no resp", "nores", "no res", "no rsp", "no rspns", "no rspnse"]),
    ("Not Found", ["not found", "notfound", "not fnd", "not fd", "nt found", "nt fnd"]),
]

# ALL GCC + Middle East countries with flexible matching
COUNTRY_PATTERNS = {
    "KSA": ["ksa", "saudi", "saudi arabia", "kingdom of saudi arabia", "riyadh", "jeddah"],
    "UAE": ["uae", "dubai", "abu dhabi", "emirates", "united arab emirates", "sharjah", "ajman"],
    "KW": ["kw", "kuwait", "kuw", "kwt", "kuwai"],
    "EGY": ["egy", "egypt", "eg", "cairo", "alexandria", "giza"],
    "QA": ["qa", "qatar", "qtr", "doha"],
    "BH": ["bh", "bahrain", "bhr", "manama"],
    "OM": ["om", "oman", "omn", "muscat"],
    "JO": ["jo", "jordan", "jrd", "jor", "amman"],
    "LB": ["lb", "lebanon", "lbn", "beirut"],
    "IQ": ["iq", "iraq", "irq", "baghdad"],
}

STATUS_1_PATTERNS = [
    "statu 1", "status 1", "statu1", "status1", "statu_1", "status_1",
    "staut 1", "stauts 1", "stats 1", "stat 1", "staus 1", "sta 1",
]

STATUS_2_PATTERNS = [
    "statu 2", "status 2", "statu2", "status2", "statu_2", "status_2",
    "staut 2", "stauts 2", "stats 2", "stat 2", "staus 2", "sta 2",
]

ACTIVE_LIST_PATTERNS = [
    "active list", "activelist", "active_list", "active  list",
    "active-list", "activ list", "actve list", "actv list",
]

INACTIVE_LIST_PATTERNS = [
    "inactive list", "inactivelist", "inactive_list", "inactive  list",
    "inactive-list", "inactiv list", "inactve list", "inactv list",
    "in active list", "in-active list", "in_active list",
]

USERNAME_PATTERNS = [
    "username", "user name", "ig username", "igusername", "user",
    "uname", "user_name", "ig_user", "ig user", "usrname",
]

# =============================================================
#  HELPERS
# =============================================================

def log(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print("[" + timestamp + "] " + msg)


def find_column(df, patterns):
    cols_lower = {str(c).strip().lower(): c for c in df.columns}
    for pattern in patterns:
        pattern_clean = pattern.strip().lower()
        if pattern_clean in cols_lower:
            return cols_lower[pattern_clean]
        for col_lower, col_original in cols_lower.items():
            if pattern_clean in col_lower or col_lower in pattern_clean:
                return col_original
    return None


def find_sheet(xls, patterns, fallback_contains, fallback_exclude):
    sheet_names = [str(s).strip() for s in xls.sheet_names]
    for pattern in patterns:
        for sheet in sheet_names:
            if pattern in sheet.lower():
                return sheet
    for sheet in sheet_names:
        s_lower = sheet.lower()
        if fallback_contains in s_lower and fallback_exclude not in s_lower:
            return sheet
    return None


def extract_campaign_name(file_name):
    """
    Extract campaign name from file name.
    File name format: "List campaign_name.xlsx"
    Result: "campaign_name" (without "List " prefix and extension)
    """
    name = file_name
    if name.lower().startswith("list "):
        name = name[5:]
    name = name.replace(".xlsx", "").replace(".xlsm", "")
    name = name.strip().strip("-").strip()
    return name


def extract_country_from_campaign(campaign_name):
    """
    Extract country from campaign name using flexible matching.
    Searches for country keywords in the campaign name itself.
    """
    campaign_lower = campaign_name.lower()

    for country, patterns in COUNTRY_PATTERNS.items():
        for pattern in patterns:
            if pattern in campaign_lower:
                return country
    return "Unknown"


def match_status_flexible(status_val):
    """
    Flexible status matching that handles manual typos.
    Returns the canonical status name or None if no match.
    """
    status_lower = status_val.strip().lower()

    for canonical, variations in TARGET_STATUS_PATTERNS:
        for var in variations:
            if var in status_lower:
                return canonical
    return None


def collect_list_files():
    files = []
    for folder in SOURCE_FOLDERS:
        if not os.path.exists(folder):
            log("Skipping missing folder: " + folder)
            continue
        for root, _, filenames in os.walk(folder):
            for f in filenames:
                if f.lower().endswith((".xlsx", ".xlsm")):
                    if f.lower().startswith("list "):
                        files.append(os.path.join(root, f))
    return files


def process_sheet(file_path, xls, sheet_patterns, sheet_label, dropbox_users, skipped_files):
    sheet = find_sheet(xls, sheet_patterns, "list", "review")
    if not sheet:
        return 0

    log("  Found " + sheet_label + " sheet: '" + sheet + "'")

    df = None
    header_row = None
    for h in range(6):
        try:
            temp_df = pd.read_excel(xls, sheet_name=sheet, header=h)
            temp_df.columns = [str(c).strip() for c in temp_df.columns]
            username_col = find_column(temp_df, USERNAME_PATTERNS)
            if username_col:
                df = temp_df
                header_row = h
                break
        except Exception:
            continue

    if df is None:
        log("  Could not find header with Username in " + sheet_label + ". Skipping.")
        skipped_files.append((os.path.basename(file_path), "No Username column in " + sheet_label))
        return 0

    log("  Header detected at row " + str(header_row) + " in " + sheet_label)

    status_col = find_column(df, STATUS_1_PATTERNS)
    if not status_col:
        log("  Status 1 not found in " + sheet_label + ", trying Status 2...")
        status_col = find_column(df, STATUS_2_PATTERNS)

    if not status_col:
        log("  No Status column found in " + sheet_label + ". Skipping.")
        skipped_files.append((os.path.basename(file_path), "No Status column in " + sheet_label))
        return 0

    log("  Status column in " + sheet_label + ": '" + status_col + "'")

    username_col = find_column(df, USERNAME_PATTERNS)
    if not username_col:
        log("  No Username column found in " + sheet_label + ". Skipping.")
        skipped_files.append((os.path.basename(file_path), "No Username column in " + sheet_label))
        return 0

    log("  Username column in " + sheet_label + ": '" + username_col + "'")

    campaign = extract_campaign_name(os.path.basename(file_path))
    country = extract_country_from_campaign(campaign)

    log("  Campaign: " + campaign + " | Country: " + country)

    extracted_count = 0
    for _, row in df.iterrows():
        status_val = str(row.get(status_col, "")).strip().lower()
        username_val = str(row.get(username_col, "")).strip().lower()

        if not username_val or username_val in ["nan", "none", "", "username"]:
            continue

        matched_status = match_status_flexible(status_val)
        if matched_status:
            if username_val not in dropbox_users:
                dropbox_users[username_val] = {
                    "status": matched_status,
                    "country": country,
                    "campaigns": [campaign],
                }
                extracted_count += 1
            else:
                if campaign not in dropbox_users[username_val]["campaigns"]:
                    dropbox_users[username_val]["campaigns"].append(campaign)

    log("  Extracted " + str(extracted_count) + " new users from " + sheet_label)
    return extracted_count


# =============================================================
#  READ EXISTING SHEET
# =============================================================

def read_pending_users(spreadsheet):
    """
    Read existing Pending Users sheet.
    Returns list of dicts preserving order.
    Each dict: {Username, Status, Updated Status, Added Date, Country, Campaigns}
    """
    try:
        ws = spreadsheet.worksheet(SHEET_NAME)
        records = ws.get_all_records()
        result = []
        for row in records:
            username = str(row.get("Username", "")).strip().lower()
            if username and username not in ["nan", "none", "", "username"]:
                result.append({
                    "Username": username,
                    "Status": str(row.get("Status", "")).strip(),
                    "Updated Status": str(row.get("Updated Status", "")).strip(),
                    "Added Date": str(row.get("Added Date", "")).strip(),
                    "Country": str(row.get("Country", "")).strip(),
                    "Campaigns": str(row.get("Campaigns", "")).strip(),
                })
        log("Read " + str(len(result)) + " users from '" + SHEET_NAME + "'")
        return result
    except gspread.WorksheetNotFound:
        log("'" + SHEET_NAME + "' not found — will create new")
        return None
    except Exception as e:
        log("Error reading '" + SHEET_NAME + "': " + str(e))
        return None


# =============================================================
#  MERGE LOGIC: Append-only
# =============================================================

def merge_append_only(existing_rows, dropbox_users):
    """
    Merge strategy: Append-only
    - Keep all existing rows in their original order
    - For new Dropbox users not in existing sheet, append at bottom
    - Status always comes from Dropbox (never changed by Updated Status)
    - Updated Status is preserved for existing rows (team writes it)
    - Added Date for new users = today's date
    - Country and Campaigns come from Dropbox

    Returns: list of rows (dicts) to write back
    """
    today = datetime.now().strftime("%d-%b-%Y")

    existing_usernames = {row["Username"] for row in existing_rows} if existing_rows else set()

    final_rows = existing_rows[:] if existing_rows else []

    new_users = []

    for username, data in dropbox_users.items():
        if username not in existing_usernames:
            campaigns_str = ", ".join(data["campaigns"])
            new_users.append({
                "Username": username,
                "Status": data["status"],
                "Updated Status": "",
                "Added Date": today,
                "Country": data["country"],
                "Campaigns": campaigns_str,
            })

    final_rows.extend(new_users)

    log("Merge results:")
    log("  Existing users preserved: " + str(len(existing_rows) if existing_rows else 0))
    log("  New users from Dropbox: " + str(len(new_users)))
    log("  Total in sheet: " + str(len(final_rows)))

    return final_rows, len(new_users)


# =============================================================
#  WRITE SHEET - APPEND NEW ROWS ONLY (NO CLEAR)
# =============================================================

def write_pending_users(spreadsheet, existing_rows, new_rows):
    """
    Write strategy: Append new rows only, preserve existing rows.
    - If sheet does not exist, create it with headers + all rows
    - If sheet exists, append new rows at the bottom
    - NEVER clears the sheet — preserves all existing data including extra columns
    """
    today = datetime.now().strftime("%d-%b-%Y")

    try:
        worksheet = spreadsheet.worksheet(SHEET_NAME)
        log("Found existing '" + SHEET_NAME + "'")

        if len(new_rows) == 0:
            log("No new users to add")
            return

        # Find the next empty row after existing data
        # Get all values to find the last row with data
        all_values = worksheet.get_all_values()
        last_row = len(all_values)

        log("Existing rows in sheet: " + str(last_row - 1) + " (excluding header)")
        log("Appending " + str(len(new_rows)) + " new users at row " + str(last_row + 1))

        # Append new rows starting from the next empty row
        start_row = last_row + 1
        data = []
        for row in new_rows:
            data.append([
                row["Username"],
                row["Status"],
                row["Updated Status"],
                row["Added Date"],
                row["Country"],
                row["Campaigns"],
            ])

        range_name = "A" + str(start_row) + ":F" + str(start_row + len(data) - 1)
        worksheet.update(values=data, range_name=range_name)
        log("Appended " + str(len(new_rows)) + " new users to '" + SHEET_NAME + "'")

    except gspread.WorksheetNotFound:
        log("Creating new '" + SHEET_NAME + "' with all users...")
        worksheet = spreadsheet.add_worksheet(title=SHEET_NAME, rows="10000", cols="20")

        # Write header + all rows (existing + new)
        all_rows = existing_rows + new_rows
        data = [["Username", "Status", "Updated Status", "Added Date", "Country", "Campaigns"]]
        for row in all_rows:
            data.append([
                row["Username"],
                row["Status"],
                row["Updated Status"],
                row["Added Date"],
                row["Country"],
                row["Campaigns"],
            ])

        worksheet.update(values=data, range_name="A1")
        log("Created '" + SHEET_NAME + "' with " + str(len(all_rows)) + " users")

    log("Sheet URL: https://docs.google.com/spreadsheets/d/" + SPREADSHEET_ID + "/edit")


# =============================================================
#  MAIN
# =============================================================

def extract_users_by_status():
    log("=" * 60)
    log("Version 3.4: Append New Rows Only (Preserve Existing)")
    log("=" * 60)
    log("Step 1: Scan Dropbox (Active + InActive)")
    log("Step 2: Deduplicate Dropbox users")
    log("Step 3: Read existing Pending Users sheet")
    log("Step 4: Merge (preserve existing, identify new)")
    log("Step 5: Append new rows to Pending Users (NO CLEAR)")
    log("=" * 60)
    log("Starting extraction...")

    files = collect_list_files()
    log("Found " + str(len(files)) + " files starting with 'List '")

    if not files:
        log("No files found!")
        return

    dropbox_users = {}
    skipped_files = []

    for i, file_path in enumerate(files, start=1):
        file_name = os.path.basename(file_path)
        log("")
        log("[" + str(i) + "/" + str(len(files)) + "] Processing: " + file_name)

        try:
            xls = pd.ExcelFile(file_path)
            active_count = process_sheet(file_path, xls, ACTIVE_LIST_PATTERNS, "Active List", dropbox_users, skipped_files)
            inactive_count = process_sheet(file_path, xls, INACTIVE_LIST_PATTERNS, "InActive List", dropbox_users, skipped_files)

            if active_count == 0 and inactive_count == 0:
                log("  No users extracted from either sheet.")
        except Exception as e:
            log("  Error: " + str(e))
            skipped_files.append((file_name, str(e)))

    log("")
    log("Step 1 complete. Dropbox unique users: " + str(len(dropbox_users)))

    log("")
    log("Step 2: Connecting to Google Sheets...")
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_JSON, scopes=scopes)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(SPREADSHEET_ID)

    log("")
    log("Step 3: Reading existing '" + SHEET_NAME + "'...")
    existing_rows = read_pending_users(spreadsheet)

    log("")
    log("Step 4: Merging (identify new users only)...")
    if existing_rows is None:
        log("  No existing sheet — all Dropbox users will be new")
        existing_rows = []

    final_rows, new_count = merge_append_only(existing_rows, dropbox_users)

    # Separate new rows from existing rows
    new_rows = final_rows[len(existing_rows):] if len(final_rows) > len(existing_rows) else []

    log("")
    log("Step 5: Writing to '" + SHEET_NAME + "'...")
    write_pending_users(spreadsheet, existing_rows, new_rows)

    log("")
    log("=" * 60)
    log("SUMMARY")
    log("=" * 60)
    log("Dropbox users found: " + str(len(dropbox_users)))
    log("Existing users in sheet: " + str(len(existing_rows)))
    log("New users added today: " + str(new_count))
    log("Total users in '" + SHEET_NAME + "': " + str(len(existing_rows) + new_count))

    status_counts = {}
    for row in final_rows:
        s = row["Status"]
        status_counts[s] = status_counts.get(s, 0) + 1
    for status, count in sorted(status_counts.items()):
        log("  " + status + ": " + str(count))

    country_counts = {}
    for row in final_rows:
        c = row["Country"]
        country_counts[c] = country_counts.get(c, 0) + 1
    log("")
    log("By Country:")
    for country, count in sorted(country_counts.items()):
        log("  " + country + ": " + str(count))

    if skipped_files:
        log("")
        log("Skipped files:")
        for fname, reason in skipped_files:
            log("   - " + fname + ": " + reason)

    log("")
    log("Done! Check your Google Sheet tab: '" + SHEET_NAME + "'")


# =============================================================
#  RUN
# =============================================================
if __name__ == "__main__":
    extract_users_by_status()
    print("")
    print("Press Enter to exit...")
    input()


# =============================================================
#  METHODOLOGY / HOW THIS SCRIPT WORKS (Version 3.4)
# =============================================================
#
#  OVERVIEW:
#  This script extracts influencers with specific statuses (Block, No Response,
#  Not Found) from Dropbox Excel files and maintains a single Google Sheet
#  called "Pending Users". The sheet grows over time — new users are appended
#  at the bottom, existing users and ALL their data are NEVER touched.
#
#  CRITICAL CHANGE IN VERSION 3.4:
#  - NO MORE worksheet.clear() — existing data is NEVER erased
#  - New users are APPENDED at the bottom of the sheet
#  - Existing rows (including "Updated Status", "Notes", "Assigned To", etc.)
#    are completely preserved
#  - If you add extra columns manually, they will remain untouched forever
#
#  ------------------------------------------------------------------------
#  STEP 1: SCAN DROPBOX
#  ------------------------------------------------------------------------
#  - Scans all folders in SOURCE_FOLDERS for Excel files starting with "List "
#  - Extracts campaign name from FILE NAME (after "List " prefix)
#  - Extracts country from CAMPAIGN NAME (not folder path)
#  - ALL GCC + Middle East countries supported:
#    KSA, UAE, Kuwait, Egypt, Qatar, Bahrain, Oman, Jordan, Lebanon, Iraq
#  - For each file, opens "Active List" and "InActive List" sheets
#  - Searches for columns: Username and Status 1 / Status 2 (flexible matching)
#  - Uses FLEXIBLE STATUS MATCHING to handle manual typos:
#      "Block"     matches: block, blok, bloc, blo, blc, bk
#      "No Response" matches: no response, noresponse, no resp, nores, etc.
#      "Not Found" matches: not found, notfound, not fnd, not fd, etc.
#  - If a user appears in multiple campaigns, all campaigns are collected
#  - Result: dict {username_lower: {status, country, campaigns: [list]}}
#
#  ------------------------------------------------------------------------
#  STEP 2: READ EXISTING "Pending Users" SHEET
#  ------------------------------------------------------------------------
#  - Connects to Google Sheets using Service Account
#  - Reads the "Pending Users" tab (if it exists)
#  - Columns read: "Username", "Status", "Updated Status", "Added Date", "Country", "Campaigns"
#  - Returns list of rows preserving original order
#  - If sheet does not exist, starts with empty list
#
#  ------------------------------------------------------------------------
#  STEP 3: MERGE (IDENTIFY NEW USERS ONLY)
#  ------------------------------------------------------------------------
#  For EACH user found in Dropbox:
#    IF user already exists in "Pending Users" sheet:
#       -> SKIP (leave row exactly as-is, including Updated Status, Notes, etc.)
#
#    IF user does NOT exist in "Pending Users" sheet:
#       -> MARK as new user with:
#          - Username: from Dropbox
#          - Status: from Dropbox (Block / No Response / Not Found)
#          - Updated Status: EMPTY (for Operations Team to fill)
#          - Added Date: today's date (e.g., "06-Jul-2026")
#          - Country: extracted from campaign name
#          - Campaigns: comma-separated list
#
#  IMPORTANT: The script does NOT check "Updated Status" at all.
#  The "Updated Status" column is purely for the Operations Team.
#
#  ------------------------------------------------------------------------
#  STEP 4: APPEND NEW ROWS ONLY (NO CLEAR)
#  ------------------------------------------------------------------------
#  - If sheet does not exist: Create it with headers + all rows
#  - If sheet exists:
#       -> Find the last row with data
#       -> Append new rows starting from the next empty row
#       -> Existing rows are NEVER modified or deleted
#  - The script ONLY writes columns A through F
#  - Any extra columns (G, H, I, etc.) are completely untouched
#
#  ------------------------------------------------------------------------
#  SHEET STRUCTURE: "Pending Users"
#  ------------------------------------------------------------------------
#  | A:Username | B:Status | C:Updated Status | D:Added Date | E:Country | F:Campaigns | G:Notes | H:Assigned To |
#  |------------|----------|------------------|--------------|-----------|-------------|---------|---------------|
#  | user1      | Block    | Sent             | 05-Jul-2026  | KSA       | Campaign A  | Done    | Ahmed         |
#  | user2      | No Resp  |                  | 05-Jul-2026  | UAE       | Campaign B  |         |               |
#  | user3      | Not Found| Reached          | 06-Jul-2026  | QA        | Camp A, C   | Call    | Sara          |
#
#  Columns A-F are managed by the script.
#  Columns G onwards are managed by the Operations Team and NEVER touched.
#
#  ------------------------------------------------------------------------
#  AUTHOR: DA-05 Analysis Team
#  VERSION: 3.4 (Append New Rows Only - Preserve All Existing Data)
#  DATE: 2026-07-06
#  =============================================================