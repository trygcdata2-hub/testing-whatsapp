import os
import re
import pandas as pd
from datetime import datetime

# ═══════════════════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════════════════
SYSTEM_FILE   = r"C:\Users\DA-05\Desktop\final_daily_report\active_01-sep.xlsx" # excel sheet from system dashboard
SYSTEM_SHEET  = "Campaigns"

CURRENT_DATE  = datetime(2026, 9, 1)  

OUTPUT_EXCEL  = r"C:\Users\DA-05\Desktop\final_daily_report\Final_Matched_Report.xlsx"
OUTPUT_TXT    = (
    r"C:\Users\DA-05\Desktop\final_daily_report"
    + rf"\Campaign_Report-{CURRENT_DATE.strftime('%d-%b').lower()}.txt"
)

ACTIVE_STATUSES = ["on going", "on hold", "upcoming", "finished"]

SOURCE_FOLDERS = [
    r"C:\Users\DA-05\Dropbox\GC - operation live\Campaign Source\4- KSA\Grand Community\Active Campaigns",
    r"C:\Users\DA-05\Dropbox\GC - operation live\Campaign Source\4- KSA\ELITE\Active Campaigns",
    r"C:\Users\DA-05\Dropbox\GC - operation live\Campaign Source\3- UAE\Grand Community\Active Campaigns",
    r"C:\Users\DA-05\Dropbox\GC - operation live\Campaign Source\3- UAE\Elite\Active Campaigns",
    r"C:\Users\DA-05\Dropbox\GC - operation live\Campaign Source\2- KW\Grand Community\Active Campaigns",
    r"C:\Users\DA-05\Dropbox\GC - operation live\Campaign Source\2- KW\Elite\Active Campaigns",
    r"C:\Users\DA-05\Dropbox\GC - operation live\Campaign Source\1- EGY\Active Campaigns\Active Campaigns",
]

STATUS_VALUES = [
    "Pending", "Confirmed", "Visited", "No Response", "Block", "Paid ads",
    "Not Found", "Traveling", "Cancelled By Client",
    "Cancelled By Community", "No Match", "Refused",
]
COUNT_COLUMNS = ["Inv.", "Rem. 1", "Rem. 2", "Username", "Notes", "Send To Community"]

# ═══════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════
def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def get_smart_key(name):
    if pd.isna(name):
        return ""
    name = str(name).lower().strip()
    name = name.replace("tiktok", "")
    words = re.findall(r"[a-z0-9]+", name)
    return "".join(sorted(words))


def parse_val(val, prefer="Sys"):
    if pd.isna(val):
        return 0
    s = str(val).strip()
    if not s:
        return 0
    if "|" in s:
        parts = s.split("|")
        data = {}
        for p in parts:
            m = re.search(r"(Drop|Sys|System)\s*:\s*([\d\.-]+)", p, re.IGNORECASE)
            if m:
                key = "Drop" if m.group(1).lower() == "drop" else "Sys"
                data[key] = int(float(m.group(2)))
        return data.get(prefer, list(data.values())[0] if data else 0)
    else:
        try:
            return int(float(s))
        except Exception:
            nums = re.findall(r"[\d\.-]+", s)
            return int(float(nums[0])) if nums else 0


def compare_values(val_drop, val_sys):
    v_drop = float(val_drop) if pd.notna(val_drop) and str(val_drop).strip() != "" else 0.0
    v_sys  = float(val_sys)  if pd.notna(val_sys)  and str(val_sys).strip()  != "" else 0.0
    if v_drop == v_sys:
        return int(v_drop)
    return f"Drop: {int(v_drop)} | Sys: {int(v_sys)}"


def clean_campaign_name(name):
    months  = r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)"
    cleaned = re.sub(rf"\s*-?\s*{months}\w*\s*-?\s*(20\d\d)?\s*$", "", name, flags=re.IGNORECASE).strip()
    cleaned = re.sub(rf"\s*-?\s*(20\d\d)\s*$", "", cleaned).strip()
    cleaned = re.sub(r"\s*-\s*$", "", cleaned).strip()
    return cleaned


def is_delivery_campaign(file_path, df, camp_name_col):
    if "delivery" in str(file_path).lower():
        return True
    if camp_name_col and not df[camp_name_col].dropna().empty:
        first_name = str(df[camp_name_col].dropna().iloc[0]).lower()
        if "delivery" in first_name:
            return True
    return False


def count_delivered(series):
    return int(series.apply(
        lambda v: str(v).strip().lower() == "delivered" if pd.notna(v) else False
    ).sum())


def get_col_safe(df, name, default=0):
    """
    Safely retrieve a column from a DataFrame.
    Tries exact match first, then case-insensitive strip match.
    Returns a Series of `default` if not found.
    """
    if name in df.columns:
        return df[name]
    match = next((c for c in df.columns if c.strip().lower() == name.strip().lower()), None)
    if match:
        log(f"  ⚠️  Column '{name}' not found — using '{match}' instead")
        return df[match]
    log(f"  ⚠️  Column '{name}' not found in DataFrame — defaulting to {default}")
    return pd.Series(default, index=df.index)


# ═══════════════════════════════════════════════════════════════
#  STEP 1 — EXTRACT FROM DROPBOX
# ═══════════════════════════════════════════════════════════════
def extract_comp_summary(all_files, max_header_search=5):
    summary_rows = []
    today = pd.to_datetime(CURRENT_DATE.date())

    for i, file_path in enumerate(all_files, start=1):
        log(f"[SUMMARY {i}/{len(all_files)}] {os.path.basename(file_path)}")
        try:
            xls         = pd.ExcelFile(file_path)
            sheet_names = [str(s).strip() for s in xls.sheet_names]
            comp_sheet  = next((s for s in sheet_names if "comp" in s.lower()), None)
            if not comp_sheet:
                continue

            header_row = None
            for r in range(max_header_search):
                temp = pd.read_excel(xls, sheet_name=comp_sheet, header=r, nrows=0)
                if any("username" in str(c).lower() for c in temp.columns):
                    header_row = r
                    break
            if header_row is None:
                continue

            df = pd.read_excel(xls, sheet_name=comp_sheet, header=header_row)
            df.columns = [str(c).strip() for c in df.columns]
            col_map    = {c.lower(): c for c in df.columns}

            def find_col(keys):
                for k in col_map:
                    if any(key in k for key in keys):
                        return col_map[k]
                return None

            username_col  = find_col(["username", "user name", "ig username", "igusername"])
            date_col      = find_col(["date"])
            visit_col     = find_col(["delivery", "delivery status", "visited status", "visit status", "visit"])
            coverage_col  = find_col(["overall cov. state", "overall cov", "covstate", "cov. state", "overallcov.state", "overallcovstate"])
            camp_name_col = find_col(["camp name", "campaign name", "camp"])

            if not username_col:
                continue
            if date_col:
                df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

            is_delivery = is_delivery_campaign(file_path, df, camp_name_col)

            all_conf       = df[username_col].notna().sum()
            conf_with_date = (df[df[username_col].notna() & df[date_col].notna()].shape[0]
                              if date_col else 0)

            if visit_col:
                if is_delivery:
                    visited = count_delivered(df[visit_col])
                else:
                    visited = int(df[visit_col].notna().sum())
            else:
                visited = 0

            coverage_count = int(df[df[coverage_col].notna()].shape[0]) if coverage_col else 0

            missing_visit = missing_coverage = 0
            if date_col and visit_col and coverage_col:
                old = df[date_col] < today
                if is_delivery:
                    delivered_mask   = df[visit_col].apply(
                        lambda v: str(v).strip().lower() == "delivered" if pd.notna(v) else False
                    )
                    missing_visit    = int(df[old & ~delivered_mask & df[coverage_col].isna()].shape[0])
                    missing_coverage = int(df[old &  delivered_mask & df[coverage_col].isna()].shape[0])
                else:
                    missing_visit    = int(df[old & df[visit_col].isna()  & df[coverage_col].isna()].shape[0])
                    missing_coverage = int(df[old & df[visit_col].notna() & df[coverage_col].isna()].shape[0])

            summary_rows.append({
                "Camp Name":                   os.path.basename(os.path.dirname(file_path)),
                "Type":                        "Delivery" if is_delivery else "Visit",
                "All Confirmations":            int(all_conf),
                "All Confirmations with Date":  int(conf_with_date),
                "Visited\\delivery":            visited,
                "Missing Visit (Old Dates)":    missing_visit,
                "Missing Coverage (Old Dates)": missing_coverage,
                "Coverage Count":               coverage_count,
            })
        except Exception as e:
            log(f"  ❌ {e}")

    return pd.DataFrame(summary_rows)


def extract_list_statistics(all_files):
    results = []
    for i, file_path in enumerate(all_files, start=1):
        log(f"[LIST  {i}/{len(all_files)}] {os.path.basename(file_path)}")
        try:
            xls         = pd.ExcelFile(file_path)
            list_sheets = [s for s in xls.sheet_names
                           if "list" in str(s).lower() and "reviewlist" not in str(s).lower()]
            if not list_sheets:
                continue

            combined_status = {s: 0 for s in STATUS_VALUES}
            combined_counts = {f"{col} Count": 0 for col in COUNT_COLUMNS}
            sheet_names_found = []

            for sheet in list_sheets:
                df = pd.read_excel(xls, sheet_name=sheet, header=2)
                df.columns = [str(c).strip() for c in df.columns]
                sheet_names_found.append(sheet)

                status_col = next(
                    (c for c in df.columns if c.strip().lower() in ["statu 1", "status 1", "statu1"]),
                    None,
                )
                if status_col:
                    sc = df[status_col].value_counts(dropna=False)
                    for s in STATUS_VALUES:
                        combined_status[s] += int(sc.get(s, 0))
                for col in COUNT_COLUMNS:
                    if col in df.columns:
                        combined_counts[f"{col} Count"] += int(df[col].notna().sum())

            row = {
                "File Name":       os.path.basename(file_path),
                "Camp Name":       os.path.basename(os.path.dirname(file_path)),
                "Sheets Combined": ", ".join(sheet_names_found),
            }
            row.update(combined_status)
            row.update(combined_counts)
            results.append(row)
        except Exception as e:
            log(f"  ❌ {e}")

    return pd.DataFrame(results)


def build_reviewing_camp(summary_df, list_df):
    list_cols = ["Inv. Count", "Rem. 1 Count", "Rem. 2 Count", "Username Count"]

    if not list_df.empty:
        agg_cols     = {c: "sum" for c in list_cols if c in list_df.columns}
        list_grouped = list_df.groupby("Camp Name", as_index=False).agg(agg_cols) if agg_cols else pd.DataFrame(columns=["Camp Name"] + list_cols)
    else:
        list_grouped = pd.DataFrame(columns=["Camp Name"] + list_cols)

    comp_cols = ["Camp Name", "All Confirmations", "All Confirmations with Date",
                 "Visited\\delivery", "Missing Visit (Old Dates)", "Missing Coverage (Old Dates)", "Coverage Count"]
    summary_side = summary_df[[c for c in comp_cols if c in summary_df.columns]].copy() if not summary_df.empty else pd.DataFrame(columns=comp_cols)

    reviewing = pd.merge(summary_side, list_grouped, on="Camp Name", how="outer")
    for col in list_cols + ["All Confirmations", "All Confirmations with Date",
                             "Visited\\delivery", "Missing Visit (Old Dates)",
                             "Missing Coverage (Old Dates)", "Coverage Count"]:
        if col in reviewing.columns:
            reviewing[col] = reviewing[col].fillna(0).astype(int)

    ordered = ["Camp Name", "All Confirmations", "All Confirmations with Date",
               "Visited\\delivery", "Missing Visit (Old Dates)", "Missing Coverage (Old Dates)",
               "Coverage Count", "Inv. Count", "Rem. 1 Count", "Rem. 2 Count", "Username Count"]
    reviewing = reviewing[[c for c in ordered if c in reviewing.columns]]
    return reviewing.sort_values("Camp Name").reset_index(drop=True)


def collect_files():
    comp_files = []
    all_files  = []
    out_name   = os.path.basename(OUTPUT_EXCEL).lower()
    for folder in SOURCE_FOLDERS:
        if not os.path.exists(folder):
            log(f"⚠️ Skipping missing folder: {folder}")
            continue
        for root, _, files in os.walk(folder):
            for f in files:
                low = f.lower()
                if not low.endswith((".xlsx", ".xlsm")):
                    continue
                if out_name in low or "conflicted copy" in low:
                    continue
                full = os.path.join(root, f)
                all_files.append(full)
                if "list" not in low and "cam info" not in low:
                    comp_files.append(full)
    return comp_files, all_files


# ═══════════════════════════════════════════════════════════════
#  STEP 2 — MERGE WITH SYSTEM FILE
# ═══════════════════════════════════════════════════════════════
def build_matched_report(reviewing_df):
    log("📂 Loading system file...")
    df_sys = pd.read_excel(SYSTEM_FILE, sheet_name=SYSTEM_SHEET)
    df_sys.columns = [str(c).strip() for c in df_sys.columns]

    # ── عرض كل الأعمدة الموجودة في الـ system file ──
    log("  📋 System file columns: " + str(list(df_sys.columns)))

    # ── عرض كل الـ statuses الموجودة في الـ system file ──
    all_statuses = df_sys["status"].value_counts(dropna=False)
    log("  📋 All statuses found in system file:")
    for st, cnt in all_statuses.items():
        log(f"      '{st}' → {cnt} campaign(s)")

    # ── فلتر الـ status ──
    before = len(df_sys)
    df_sys = df_sys[df_sys["status"].str.strip().str.lower().isin(
        [s.lower() for s in ACTIVE_STATUSES]
    )]
    after = len(df_sys)
    log(f"  🔍 Status filter: {before} → {after} campaigns  (kept: {ACTIVE_STATUSES})")

    reviewing_df["smart_key"] = reviewing_df["Camp Name"].apply(get_smart_key)
    df_sys["smart_key"]       = df_sys["Campaign Name"].apply(get_smart_key)

    merged = pd.merge(reviewing_df, df_sys, on="smart_key", how="inner", suffixes=("_drop", "_sys"))
    log(f"  ✅ Matched {len(merged)} campaigns")

    out = pd.DataFrame()
    out["Campaign Name"]               = merged["Camp Name"]
    out["status"]                      = merged["status"]
    out["Type"]                        = merged["Type"] if "Type" in merged.columns else "Visit"
    out["Country"]                     = get_col_safe(merged, "Country", "N/A")
    out["Daily Target"]                = get_col_safe(merged, "Daily Target", 0)
    out["Target"]                      = get_col_safe(merged, "Target", 0)
    out["All Confirmations"]           = merged["All Confirmations"]
    out["All Confirmations with Date"] = merged.apply(
        lambda r: compare_values(r["All Confirmations with Date"],
                                 get_col_safe(merged, "Confirmations", 0).loc[r.name]),
        axis=1
    )
    out["Today's Visits"]              = get_col_safe(merged, "Today's Visits", 0)
    out["Tomorrow's Visits"]           = get_col_safe(merged, "Tomorrow's Visits", 0)
    out["Day After"]                   = get_col_safe(merged, "Day After", 0)
    out["Visited"]                     = merged.apply(
        lambda r: compare_values(r["Visited\\delivery"],
                                 get_col_safe(merged, "Visited", 0).loc[r.name]),
        axis=1
    )
    out["missed_visit"]                = merged.apply(
        lambda r: compare_values(r["Missing Visit (Old Dates)"],
                                 get_col_safe(merged, "missed_visit", 0).loc[r.name]),
        axis=1
    )
    out["Missing_coverage"]            = merged.apply(
        lambda r: compare_values(r["Missing Coverage (Old Dates)"],
                                 get_col_safe(merged, "Missing_coverage", 0).loc[r.name]),
        axis=1
    )
    out["Coverage"]                    = merged.apply(
        lambda r: compare_values(r["Coverage Count"],
                                 get_col_safe(merged, "Coverage", 0).loc[r.name]),
        axis=1
    )
    out["Total_list"]                  = merged["Username Count"] if "Username Count" in merged.columns else 0
    out["Inv. Count"]                  = merged["Inv. Count"]     if "Inv. Count"     in merged.columns else 0
    out["Rem. 1 Count"]                = merged["Rem. 1 Count"]   if "Rem. 1 Count"   in merged.columns else 0
    out["Rem. 2 Count"]                = merged["Rem. 2 Count"]   if "Rem. 2 Count"   in merged.columns else 0
    out["request_for_approval"]        = get_col_safe(merged, "request_for_approval", 0)
    out["Approved"]                    = get_col_safe(merged, "Approved", 0)
    out["Reject"]                      = get_col_safe(merged, "Reject", 0)
    out["Start Date"]                  = get_col_safe(merged, "Start Date", pd.NaT)
    out["End Date"]                    = get_col_safe(merged, "End Date",   pd.NaT)

    return out


# ═══════════════════════════════════════════════════════════════
#  STEP 3 — GENERATE WHATSAPP REPORT
# ═══════════════════════════════════════════════════════════════
def generate_report(matched_df):
    df = matched_df.copy()

    df["Confirmations_Sys"]  = df["All Confirmations with Date"].apply(lambda x: parse_val(x, "Sys"))
    df["Confirmations_Drop"] = df["All Confirmations with Date"].apply(lambda x: parse_val(x, "Drop"))
    df["Visited_Sys"]        = df["Visited"].apply(lambda x: parse_val(x, "Sys"))
    df["Visited_Drop"]       = df["Visited"].apply(lambda x: parse_val(x, "Drop"))
    df["Missed_Sys"]         = df["missed_visit"].apply(lambda x: parse_val(x, "Sys"))
    df["Missed_Drop"]        = df["missed_visit"].apply(lambda x: parse_val(x, "Drop"))
    df["Missing_Sys"]        = df["Missing_coverage"].apply(lambda x: parse_val(x, "Sys"))
    df["Missing_Drop"]       = df["Missing_coverage"].apply(lambda x: parse_val(x, "Drop"))
    df["Coverage_Sys"]       = df["Coverage"].apply(lambda x: parse_val(x, "Sys"))
    df["Coverage_Drop"]      = df["Coverage"].apply(lambda x: parse_val(x, "Drop"))

    for col in ["Target", "All Confirmations", "Total_list", "request_for_approval", "Approved", "Reject",
                "Inv. Count", "Rem. 1 Count", "Rem. 2 Count"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    df["Today_Visits"]    = pd.to_numeric(df["Today's Visits"],    errors="coerce").fillna(0).astype(int)
    df["Tomorrow_Visits"] = pd.to_numeric(df["Tomorrow's Visits"], errors="coerce").fillna(0).astype(int)
    df["Day After"]       = pd.to_numeric(df["Day After"],         errors="coerce").fillna(0).astype(int)
    df["Start Date"]      = pd.to_datetime(df["Start Date"], errors="coerce")
    df["End Date"]        = pd.to_datetime(df["End Date"],   errors="coerce")
    df["Country"]         = df["Country"].astype(str).str.upper().str.strip()

    df["Cov_Pct"]         = (df["Coverage_Sys"] / df["Target"] * 100).fillna(0)
    df["Days_Left"]       = (df["End Date"] - CURRENT_DATE).dt.days.fillna(999)
    df["Conf_Gap"]        = (df["Target"] - df["Confirmations_Sys"]).clip(lower=0)

    def get_sort_order(row):
        if row["Days_Left"] <= 0:
            if row["Coverage_Sys"] >= row["Target"]:
                return 1
            return 0
        if row["Coverage_Sys"] >= row["Target"] or row["Confirmations_Sys"] >= row["Target"]:
            return 1
        return 0

    df["Sort_Order"] = df.apply(get_sort_order, axis=1)
    df_sorted = df.sort_values(by=["Sort_Order", "Days_Left", "Conf_Gap"], ascending=[True, True, False])

    # KPIs
    total_visited             = df["Visited_Sys"].sum()
    total_request_for_approval = df["request_for_approval"].sum()
    total_approved            = df["Approved"].sum()
    total_reject              = df["Reject"].sum()
    total_coverage            = df["Coverage_Sys"].sum()
    total_confirmations       = df["All Confirmations"].sum()
    total_target              = df["Target"].sum()
    total_missing             = df["Missing_Sys"].sum()
    total_missed              = df["Missed_Sys"].sum()
    num_critical              = (df["Sort_Order"] == 0).sum()
    num_ok                    = (df["Sort_Order"] == 1).sum()

    STATUS_LABEL = {0: "🚨 CRITICAL", 1: "🟢 OK"}

    R = []

    R.append(f"📊 *CAMPAIGN REPORT — {CURRENT_DATE.strftime('%d %b %Y')}*")
    R.append("")
    R.append("🚨 CRITICAL = Coverage < Target  &  Conf with Date < Target")
    R.append("🟢 OK       = Coverage >= Target  OR  Conf with Date >= Target")
    R.append("")

    R.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    R.append("📈 *OVERALL PERFORMANCE*")
    R.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    status_counts  = df["status"].str.strip().value_counts()
    status_summary = "  |  ".join([f"{s}: {c}" for s, c in status_counts.items()])
    R.append(f"Active Campaigns:  {len(df)}   🚨{num_critical}  🟢{num_ok}")
    R.append(f"  ↳ {status_summary}")
    R.append("")
    R.append(f"Target:            {total_target:,}")
    R.append(f"Coverage:          {total_coverage:,}")
    R.append(f"Confirmations:     {total_confirmations:,}")
    R.append(f"Visited:           {total_visited:,}")
    R.append(f"Missing Coverage:  {total_missing:,}")
    R.append(f"Missed Visit:      {total_missed:,}")
    R.append(f"request_for_approval:{total_request_for_approval:,}")
    R.append(f"Approved:          {total_approved:,}")
    R.append(f"Reject:            {total_reject:,}")
    R.append("")

    total_community_tasks    = 0
    total_whatsapp_tasks     = 0
    total_onboarding_tasks   = 0
    total_followup_tasks     = 0
    total_coverage_tasks     = 0
    total_coordination_tasks = 0

    for country in df_sorted["Country"].unique():
        c_df       = df_sorted[df_sorted["Country"] == country]
        c_target   = c_df["Target"].sum()
        c_coverage = c_df["Coverage_Sys"].sum()
        c_conf_d   = c_df["Confirmations_Sys"].sum()
        c_missing  = c_df["Missing_Sys"].sum()
        c_missed   = c_df["Missed_Sys"].sum()
        c_visited  = c_df["Visited_Sys"].sum()
        c_cov_pct  = round(c_coverage / c_target * 100, 1) if c_target else 0
        c_critical = (c_df["Sort_Order"] == 0).sum()
        c_ok       = (c_df["Sort_Order"] == 1).sum()

        R.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        R.append(f"🌍 *{country}*   🚨{c_critical}  🟢{c_ok}")
        R.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        R.append(f"Target:            {c_target}")
        R.append(f"Coverage:          {c_coverage}  ({c_cov_pct}%)")
        R.append(f"Conf with Date:    {c_conf_d}")
        R.append(f"Missing Coverage:  {c_missing}")
        R.append(f"Visited:           {c_visited}")
        R.append(f"Missed Visit:      {c_missed}")
        R.append("")

        for _, row in c_df.iterrows():
            label     = STATUS_LABEL[row["Sort_Order"]]
            camp_name = clean_campaign_name(str(row["Campaign Name"]))
            brand     = camp_name.split("-")[0].strip()
            end_str   = row["End Date"].strftime("%d %b %Y")   if pd.notna(row["End Date"])   else "N/A"
            start_str = row["Start Date"].strftime("%d %b %Y") if pd.notna(row["Start Date"]) else "N/A"
            days_left = int(row["Days_Left"])

            R.append(label)
            R.append(f"*{camp_name}*")
            R.append("")
            R.append(f"status: {row['status']}")
            R.append(f"Brand: {brand}")
            R.append(f"Type:  {row.get('Type', 'Visit')}")
            R.append(f"Start_date:📅 {start_str} → End_Date: {end_str}  ({days_left}d left)")
            R.append(f"Daily Target:       {int(row['Daily Target']) if pd.notna(row.get('Daily Target')) else 0}")
            R.append(f"Target:             {row['Target']}")
            R.append(f"Coverage:           {row['Coverage_Sys']}  ({row['Cov_Pct']:.1f}%)")
            R.append(f"Conf with Date:     {row['Confirmations_Sys']}")
            R.append(f"All Confirmations:  {row['All Confirmations']}")
            camp_type     = str(row.get("Type", "Visit")).strip().lower()
            visited_value = row["Visited_Drop"] if camp_type == "delivery" else row["Visited_Sys"]
            R.append(f"Visited:            {visited_value}")
            R.append(f"Missing Coverage:   {row['Missing_Sys']}")
            R.append(f"Missed Visit:       {row['Missed_Sys']}")
            R.append(f"request_for_approval:           {row['request_for_approval']}")
            R.append(f"Approved:           {row['Approved']}")
            R.append(f"Reject:             {row['Reject']}")
            R.append(f"Total List:         {row['Total_list']}")
            R.append(f"Inv:                {row['Inv. Count']}")
            R.append(f"Rem 1:              {row['Rem. 1 Count']}")
            R.append(f"Rem 2:              {row['Rem. 2 Count']}")
            R.append(f"Today Conf:         {row['Today_Visits']}")
            R.append(f"Tomorrow Conf:      {row['Tomorrow_Visits']}")
            R.append(f"Day After Conf:     {row['Day After']}")

            # ── Coordination Team (Sync check) ──
            discrepancies = []
            if row["Confirmations_Sys"] != row["Confirmations_Drop"]:
                diff = row["Confirmations_Sys"] - row["Confirmations_Drop"]
                discrepancies.append(f"  Conf with Date:   SYS {row['Confirmations_Sys']} / DROP {row['Confirmations_Drop']}  (Δ {diff:+})")
            if row["Visited_Sys"] != row["Visited_Drop"]:
                diff = row["Visited_Sys"] - row["Visited_Drop"]
                discrepancies.append(f"  Visited:          SYS {row['Visited_Sys']} / DROP {row['Visited_Drop']}  (Δ {diff:+})")
            if row["Missing_Sys"] != row["Missing_Drop"]:
                diff = row["Missing_Sys"] - row["Missing_Drop"]
                discrepancies.append(f"  Missing Coverage: SYS {row['Missing_Sys']} / DROP {row['Missing_Drop']}  (Δ {diff:+})")
            if row["Coverage_Sys"] != row["Coverage_Drop"]:
                diff = row["Coverage_Sys"] - row["Coverage_Drop"]
                discrepancies.append(f"  Coverage:         SYS {row['Coverage_Sys']} / DROP {row['Coverage_Drop']}  (Δ {diff:+})")

            R.append("")
            if discrepancies:
                R.append("🔄 Coordination Team:")
                R.append("  Problem : Data mismatch between System and Dropbox sheets")
                R.extend(discrepancies)
                R.append("  Action  : Review client sheets on Dropbox and align with System numbers")
                total_coordination_tasks += 1
            else:
                R.append("✔ Data aligned — System & Dropbox match")

            R.append("")
            R.append("📋 *Tasks by Team:*")
            has_task = False

            cov_gap        = row["Target"] - row["Coverage_Sys"]
            conf_gap       = row["Target"] - row["Confirmations_Sys"]
            visited_no_cov = max(0, row["Visited_Sys"] - row["Coverage_Sys"])
            rem_inv        = max(0, row["Total_list"]   - row["Inv. Count"])
            rem_rem1       = max(0, row["Inv. Count"]   - row["Rem. 1 Count"])
            rem_rem2       = max(0, row["Rem. 1 Count"] - row["Rem. 2 Count"])
            triple_target  = row["Target"] * 3

            # 👁 Coverage Team
            total_no_cov = max(visited_no_cov, row["Missing_Sys"])
            if total_no_cov > 0:
                R.append("")
                R.append("👁 Coverage Team:")
                R.append(f"  Problem : {total_no_cov} influencer(s) with no coverage submitted yet  ({row['Coverage_Sys']}/{row['Target']} coverage)")
                R.append(f"  Action  : Search their accounts — find & log any posted content links")
                total_coverage_tasks += 1
                has_task = True

            # 📞 Follow-up Team
            if row["Missed_Sys"] > 0:
                R.append("")
                R.append("📞 Follow-up Team:")
                R.append(f"  Problem : {row['Missed_Sys']} influencer(s) missed their scheduled visit")
                R.append(f"  Action  : Contact each one individually —")
                R.append(f"            ✓ If visited  → request coverage link immediately")
                R.append(f"            ✗ If not visited → agree on a new visit date")
                total_followup_tasks += 1
                has_task = True

            # 💬 WhatsApp Team
            if conf_gap > 0:
                R.append("")
                R.append("💬 WhatsApp Team:")
                R.append(f"  Problem : Only {row['Confirmations_Sys']}/{row['Target']} confirmed with date  (need {conf_gap} more)")
                if rem_inv > 0 or rem_rem1 > 0 or rem_rem2 > 0:
                    R.append(f"  Action  : Work the funnel — Inv {rem_inv}  |  Rem1 {rem_rem1}  |  Rem2 {rem_rem2}")
                else:
                    R.append(f"  Action  : List fully exhausted — escalate to Community Team for new list")
                total_whatsapp_tasks += 1
                has_task = True

            # 👥 Community Team — new/larger list needed
            list_too_small = row["Total_list"] < triple_target
            list_exhausted = conf_gap > 0 and rem_inv == 0 and rem_rem1 == 0 and rem_rem2 == 0

            if list_exhausted or list_too_small:
                R.append("")
                R.append("👥 Community Team:")
                if list_exhausted and list_too_small:
                    R.append(f"  Problem : List exhausted AND too small  (Total List {row['Total_list']} < {int(triple_target)} = Target×3)")
                    R.append(f"  Action  : Upload a larger new list immediately (minimum {int(triple_target)} profiles needed)")
                elif list_exhausted:
                    R.append(f"  Problem : Current list completely exhausted — no leads left to contact")
                    R.append(f"  Action  : Upload a new list immediately to resume confirmations")
                else:
                    R.append(f"  Problem : Total List ({row['Total_list']}) is below 3× Target ({int(triple_target)}) — list is too small")
                    R.append(f"  Action  : Search for influencers who previously worked on similar brand campaigns and are still active, to reach at least {int(triple_target)} total")
                total_community_tasks += 1
                has_task = True

            # 👥 Community Team — call pending users (low confirmations, campaign ending soon)
            ending_soon = 0 <= row["Days_Left"] <= 3
            if conf_gap > 0 and ending_soon:
                R.append("")
                R.append("👥 Community Team:")
                R.append(f"  Problem : Only {row['Coverage_Sys']}/{row['Target']} Covered  (need {cov_gap} more coverage) and Only {row['Confirmations_Sys']}/{row['Target']} confirmed with date (need {conf_gap} more confirmations), "
                          f"and only {int(row['Days_Left'])}d left before the campaign ends")
                R.append(f"  Action  : Call all pending users in the list and obtain their confirmation urgently")
                total_community_tasks += 1
                has_task = True

            # 🎯 Onboarding Team
            if conf_gap > 0 and row["Approved"] > 0:
                R.append("")
                R.append("🎯 Onboarding Team:")
                R.append(f"  Problem : Confirmation gap of {conf_gap} — approved profiles available to leverage")
                R.append(f"  Action  : Source Look-Alike influencers based on {row['Approved']} approved profile(s)")
                total_onboarding_tasks += 1
                has_task = True

            if not has_task:
                R.append("  ✔ No issues — campaign running smoothly")

            R.append("")
            R.append("——————————————————————————————")
            R.append("")

    R.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    R.append("👥 *TASK SUMMARY BY TEAM*")
    R.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    R.append(f"Coverage Team:      {total_coverage_tasks} campaign(s) — find & log missing content")
    R.append(f"Follow-up Team:     {total_followup_tasks} campaign(s) — missed visits follow-up")
    R.append(f"WhatsApp Team:      {total_whatsapp_tasks} campaign(s) — funnel actions")
    R.append(f"Community Team:     {total_community_tasks} campaign(s) — new/larger lists needed / need Confirmations from calls")
    R.append(f"Onboarding Team:    {total_onboarding_tasks} campaign(s) — look-alike sourcing")
    R.append(f"Coordination Team:  {total_coordination_tasks} campaign(s) — fix System vs Dropbox mismatch")
    R.append("")
    R.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    R.append("✅ End of Report")
    R.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    return "\n".join(R)


# ═══════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════
def main():
    log("🚀 Starting full pipeline...")

    for path in [OUTPUT_EXCEL, OUTPUT_TXT]:
        d = os.path.dirname(path)
        if d and not os.path.exists(d):
            os.makedirs(d)

    # Step 1 — extract from Dropbox
    log("\n── STEP 1: Extract from Dropbox ──")
    comp_files, all_files = collect_files()
    log(f"COMP files: {len(comp_files)}  |  All Excel files: {len(all_files)}")
    summary_df   = extract_comp_summary(comp_files)
    list_df      = extract_list_statistics(all_files)
    reviewing_df = build_reviewing_camp(summary_df, list_df)

    # Step 2 — merge with system
    log("\n── STEP 2: Match with System file ──")
    matched_df = build_matched_report(reviewing_df)

    # Save intermediate Excel
    log(f"\n💾 Saving Excel → {OUTPUT_EXCEL}")
    with pd.ExcelWriter(OUTPUT_EXCEL, engine="openpyxl") as writer:
        matched_df.to_excel(writer,   sheet_name="Sheet1",         index=False)
        reviewing_df.to_excel(writer, sheet_name="Reviewing Camp",  index=False)
        summary_df.to_excel(writer,   sheet_name="COMP Summary",    index=False)
        list_df.to_excel(writer,      sheet_name="LIST Statistics",  index=False)

    # Step 3 — generate WhatsApp report
    log("\n── STEP 3: Generate WhatsApp report ──")
    report_text = generate_report(matched_df)

    with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
        f.write(report_text)

    log(f"\n✅ DONE!")
    log(f"   Excel  → {OUTPUT_EXCEL}")
    log(f"   Report → {OUTPUT_TXT}")


if __name__ == "__main__":
    main()
    print("\n✨ Press Enter to exit...")
    input()