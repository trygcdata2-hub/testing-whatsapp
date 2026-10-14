# WhatsApp Operations & Multi-Source Reconciliation Engine
**Last Updated:** 2026-10-14  
**Engine Version:** v2.5 (Live Google Sheets Integration • Universal Import Fallbacks • Full Cloud Module Sync)

---

## 1. System Overview & Current Status

This repository is an operational analytics and audit intelligence system connecting critical data streams for influencer operations:
1. **WhatsApp Stream:** Real-time messages, conversation threads, and reply SLA metrics (`data/last_month_s_data.parquet`).
2. **Google Sheets / Shift Roster:** Live task rosters fetched directly from Google Sheets (`Chat Team 's Tasks` spreadsheet) via `gspread` + service account, with fast parquet caching (`cached_whatsapp_tasks.parquet` & `cached_gc_tasks.parquet`). Total: **18,171** official shift tasks (6,856 WhatsApp + 12,265 GC).
3. **System Database:** Campaigns since 1 May 2026, campaign influencer booking statuses, and influencer master directory.
4. **Dropbox Client Sheets:** Manual campaign Excel workbooks (`Comp.` and `List` sheets) in `C:\Users\DA-05\Dropbox\GC - operation live\Campaign Source\...`.
5. **pCloud Coverage Drive:** Raw uploaded coverage media across active campaigns in KSA, UAE, KW, and EGY in `P:\Operation - Head Office\Coverages-Final\...`.

---

## 2. Core Modules & Engine Breakdown

### A. Roster Shift Attribution Engine (`src/pipeline.py`)
- **Problem Solved:** Raw outgoing phone messages sent as `original whatsapp` (~14.3k messages) lacked agent attribution.
- **Rules Applied:**
  - **Live Chat Filtering:** Only shift tasks designated for Instant Response (`'live'`, `'response'`, or `'sr.whatsapp'`) receive message credit. Creation, Calling, and Monitoring shifts are excluded.
  - **Shift Boundary Fallbacks:** Automatic fallback to shift end when `End Time` is missing (17:00 Morning, 01:00 next day Between, 09:00 Night).
  - **Strict Overlap Neutrality:** Simultaneous agent overlaps on the same line at the same time remain `original whatsapp` (no guessing, no unfair penalties).
  - **"All Lines Numbers" Assignment:** Unassigned line traffic falls back to agents on `All Lines Numbers` duty.
  - **Date-Indexed O(1) datetime lookup** for instantaneous processing across 50k messages.
- **Attribution Results:**
  - Total Agents recognized: Increased from **48** to **70** agents.
  - Successfully attributed: **4,784** messages reassigned to real agents.
  - Unattributed overlaps preserved: **9,554** messages remain `original whatsapp`.

### B. 3-Way Dropbox vs System Reconciliation Engine (`src/reconciliation.py`)
- **Problem Solved:** Audits discrepancies between manual Dropbox client sheets and official System Database bookings.
- **Rules Applied:**
  - **Dual-Phone Fallback (XLOOKUP):** Always queries Primary Phone first, falling back to WhatsApp Number.
  - **Right(8) Phone Normalization:** Strips non-digits, extracts last 8 digits (`clean_phone[-8:]`), neutralizing international country codes (+966, 00966, +965, +20).
  - **Username Matching:** Cleans and matches Instagram/TikTok handles against `influencers_master.csv`.
- **Reconciliation Metrics:**
  - **50** Dropbox campaign files parsed.
  - **30,092** total influencer rows audited.
  - **34** active campaigns matched between Dropbox and System DB.
  - **2,649** discrepant influencers identified (confirmed in Dropbox but missing `status=1` in System DB).

### C. pCloud Coverage vs. Status 7 Reconciliation Engine (`src/pcloud_reconciliation.py`)
- **Architecture Principle (System Active Campaigns as Driver):** Driven strictly by System Active Campaigns (based on `reference/active_campaigns.sql` criteria: `status IN (1, 4)` and recent `(2, 6)`), NOT the 392 raw folders in pCloud.
- **Smart Multi-Layer Token Matching Engine:**
  - Strict Country Guardrail (KSA, UAE, KW, EGY).
  - Core Brand Token Sorting (neutralizes token order variations, e.g. dates or country at the end).
  - Stopwords cleaning (`visit`, `delivery`, `highest platform`, `approach`, etc.).
  - Month/Year alignment and Jaccard token similarity (>= 0.50).
- **Active Campaigns Scope Findings:**
  - **35** active campaigns in System DB.
  - **28** active campaigns matched in pCloud folders (80% coverage).
  - **767** coverage uploads in active campaigns.
  - **403** aligned (`status == 7` in System DB).
  - **33 CRITICAL OPERATIONAL GAPS (Active Campaigns Missing Status 7):** Influencers who submitted coverage for active campaigns but are NOT updated to status 7 in the database!
    - Top active campaigns with gaps: `Table To - Visit - Highst platform - Ksa` (11), `Spice (jonesthegrocersa)` (6), `Beauty Secrets - delivery - ksa` (4), `Fnp(love)` (2), `Shrimp Zone Riyadh` (2), `Dopeamine` (2), `Jaderoom` (2), `legrenierapain.me` (1), `Drcafe` (1), `fnp(birthday)` (1).
- **All Monitored Campaigns Scope (Since 1 May):**
  - **203** total campaigns; **164** matched; **637** aligned; **239** missing Status 7 gaps.
- **Fast Caching Layer:** `data/cached_pcloud_recon_campaigns.parquet` (31 KB) & `data/cached_pcloud_recon_influencers.parquet` (214 KB).

### D. Live Operations Dashboard (`app.py`, `src/app.py`, `project/src/app.py`)
- Built with Streamlit, Plotly, and responsive dark-mode CSS cards.
- **Tab 1: Live Pulse & Alerts:** Unanswered conversations (Dynamic rule: Influencer sent last), SLA distribution (<15m, 15-60m, >60m). Full duration response time without artificial timeouts.
- **Tab 2: Agent Scorecards & KPIs:** Agent response volumes, median reply times, shift attribution status banner.
- **Tab 3: Influencer Intelligence:** Official database status breakdown, flakers & missed visits audit with dynamic column handling and phone masking.
- **Tab 4: Multi-Source Reconciliation (pCloud & Dropbox):**
  - **Sub-Tab 1 (pCloud Coverage Audit):** Active campaigns scope toggle (default: active campaigns under SQL criteria), drill-down table with masked phones, and one-click operational CSV export: `📥 تنزيل القائمة الإجرائية لتحديث الـ Status 7 (CSV)`.
  - **Sub-Tab 2 (Dropbox Reconciliation):** Campaign-level comparison (Target vs Sys Confirms vs Drop Confirms vs Gap) and influencer audit drill-down.
- **Tab 5: Line Health & Infrastructure Status:** WhatsApp lines inventory and monitoring.
- **Sidebar:** Dynamic operational controls with instant cache-clearing (`🔄 Force Reload / Clear Cache`), showing live counts for Roster, Dropbox, and pCloud gaps.

---

## 3. Ground Truth Rules & Constraints for AI Agents

1. **Google Spreadsheet Access:** Read-only (active key: `operations-511207-c2981485761f.json`; auto-discovered by `src/config.py`). Never mutate or write.
2. **Dropbox Folder Access:** Local files in `C:\Users\DA-05\Dropbox\...` are **STRICT READ-ONLY**. Never write or modify files there.
3. **pCloud Folder Access:** Local files in `P:\...` are **STRICT READ-ONLY**. Never write or modify files there.
4. **Active Influencer Definition:** Strictly based on `campaign_influencers.status` in `(2, 7, 8, 11, 13)`. Never use `influencers.active`.
5. **Phone Matching:** Always use dual-column fallback (`p1` then `p2`) and `Right(8)` normalization. Over 50% of matches rely on the second column!
6. **Active Campaigns SQL Scope & Migration Direction:** Active campaigns are driven by `reference/active_campaigns.sql` criteria. External directories (Dropbox, pCloud) are matched against System Active Campaigns, never the reverse. Future DB queries will restrict to active campaigns and recent message windows.
7. **Roster Fairness & Live Chat Rule:** Only shifts with tasks matching `live`, `response`, or `sr.whatsapp` are eligible. If 2+ agents are simultaneously logged on the same line, message remains `original whatsapp` (no guessing, no unfair penalties).
8. **Strict Full-Duration Response Time:** Response times measure from arrival to dispatch without artificial session forgiveness or 24-hour reset.
9. **Dynamic DB Migration Readiness:** Keep analysis functions parameterized accepting DataFrames so switching from CSV/Parquet to live SQL connections requires zero architectural changes.

---

## 4a. Changelog (v2.5 — Live Google Sheets & Cloud Deployment)

| Component | Change | Details |
| :--- | :--- | :--- |
| `src/data_loader.py` | Live Google Sheets integration | Roster tasks now fetched live from `Chat Team 's Tasks` spreadsheet (sheets: `what's app tasks` & `Tasks ( GC )`) via `gspread` + service account. Static `tasks.xlsx` retained as emergency fallback only. |
| `src/config.py` | Dynamic credential discovery | `_find_service_account_file()` auto-discovers the latest `operations-*.json` key across multiple search paths. Old key `eb43144fc000` replaced by active key `c2981485761f`. |
| `src/*.py` | Universal 3-tier import fallbacks | All modules (`data_loader`, `pipeline`, `metrics`, `reconciliation`, `pcloud_reconciliation`) now use `try: from .config` → `from src.config` → `from config` to prevent `ImportError` on Streamlit Cloud. |
| `project/src/` | Full module sync | `project/src/` now mirrors all `src/` engine modules (pipeline, metrics, reconciliation, pcloud_reconciliation, __init__), not just `app.py`. |
| `app.py` (sidebar) | Sync button | Added `🔄 Sync from Google Sheets` sidebar button for one-click live data refresh. |

## 4b. Changelog (v2.4 — Production Hardening)

| Component | Issue | Fix Applied | Result |
| :--- | :--- | :--- | :--- |
| `src/metrics.py:58` | `int(s_id)` raised `ValueError` when status IDs contained NaN/floats | Added safe `try/except` with `int(float(s_id))` | Zero crash on missing status fields |
| `src/metrics.py:72` | Hardcoded column selection caused `KeyError` if `booking_created_at` missing | Dynamically filters `flakers_df` by existing columns | Safe execution across all dataset schemas |
| `app.py:354`, `src/app.py:354`, `project/src/app.py:354` | Dashboard crashed when displaying flakers table if columns were missing | Added dynamic column list checking and phone masking guardrail | Stable rendering across all 3 app entrypoints |
| `src/pcloud_reconciliation.py:433` | Status lookup failed because `st_id` was float (e.g. `7.0`) while `STATUS_MAP` keys are ints | Added `int(st_id)` lookup cast | Status names (e.g., "Coverage") correctly displayed |
| `README.md` | Outdated documentation referencing incomplete tasks | Rewritten comprehensively with architecture diagrams, module details, and quickstarts | Full documentation alignment |

---

## 5. Deployment & Execution Instructions

```bash
# Launch Streamlit Dashboard Locally
streamlit run app.py

# Push and Sync with GitHub / Streamlit Cloud
push_to_github.bat
```

- **Remote GitHub Repository:** `https://github.com/trygcdata2-hub/testing-whatsapp`
- **Branch:** `main`
- **Entry Points Supported:**
  - `app.py`: Root entrypoint
  - `src/app.py`: Standard modular source
  - `project/src/app.py`: Forwarder for Streamlit Cloud subfolder configurations
