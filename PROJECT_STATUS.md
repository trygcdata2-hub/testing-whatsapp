# WhatsApp Operations & Multi-Source Reconciliation Engine
**Last Updated:** 2026-10-11
**Engine Version:** v2.1 (Roster Attribution + 3-Way Dropbox/System Reconciliation)

---

## 1. System Overview & Current Status

This repository is an operational analytics and audit intelligence system connecting three critical data streams for influencer operations:
1. **WhatsApp Stream:** Real-time messages, conversation threads, and reply SLA metrics (`last_month_s_data.parquet`).
2. **Google Sheets / Shift Roster:** Live task rosters attributing phone messages to agents during their shifts (`tasks.xlsx` & cached parquets).
3. **System Database:** Campaigns since 1 May 2026, campaign influencer booking statuses, and influencer master directory.
4. **Dropbox Client Sheets:** Manual campaign Excel workbooks (`Comp.` and `List` sheets) in `C:\Users\DA-05\Dropbox\GC - operation live\Campaign Source\...`.

---

## 2. Core Modules Implemented

### A. Roster Shift Attribution Engine (`src/pipeline.py`)
- **Problem Solved:** Raw outgoing phone messages sent as `original whatsapp` (~14.3k messages) lacked agent attribution.
- **Rules Applied:**
  - Fallback to shift end when `End Time` is missing (17:00 Morning, 01:00 next day Between, 09:00 Night).
  - Strict Fairness Rule: Simultaneous agent overlaps on the same line at the same time remain `original whatsapp` (no guessing, no unfair penalties).
  - Date-Indexed O(1) datetime lookup for instantaneous processing across 50k messages.
- **Attribution Results:**
  - Total Agents recognized: Increased from **48** to **70** agents.
  - Successfully attributed: **4,784** messages reassigned to real agents.
  - Unattributed overlaps preserved: **9,554** messages remain `original whatsapp`.

### B. 3-Way Dropbox vs System Reconciliation Engine (`src/reconciliation.py`)
- **Problem Solved:** Audits discrepancy between manual Dropbox client sheets and official System Database bookings.
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
- **New Operational Data Source:** pCloud coverage repository (`P:\Operation - Head Office\Coverages-Final\...`).
- **Scanned Scope:** 392 active campaigns scanned across KSA, UAE, KW, and EGY; **16,293** coverage upload records extracted.
- **Status 7 Audit Rule:** Influencers who uploaded coverage files to pCloud MUST have `campaign_influencers.status_id = 7` (Posted / Completed Coverage).
- **Audit Findings:**
  - **Aligned:** **637** influencers uploaded coverage and are properly marked `status=7` in the database.
  - **CRITICAL OPERATIONAL GAP (Missing Status 7):** **239** influencers uploaded coverage to pCloud but their status in the database was NOT updated to 7! (Top affected campaigns: `Society by Sofleur` (93), `Dr.Scent` (66), `dopeamine` (19), `brunch & cake` (14), `Table To` (11)).
  - **Not Booked in System:** **12,995** coverages uploaded in pCloud without booking records in `campaign_influencers.csv` (older campaigns or external bookings).
- **Fast Caching Layer:** `data/cached_pcloud_recon_campaigns.parquet` (31 KB) & `data/cached_pcloud_recon_influencers.parquet` (214 KB).

### D. Live Operations Dashboard (`src/app.py`)
- Built with Streamlit, Plotly, and responsive dark-mode CSS cards.
- **Tab 1: Live Pulse & Alerts:** Unanswered conversations (Dynamic rule: Influencer sent last), SLA distribution (<15m, 15-60m, >60m).
- **Tab 2: Agent Scorecards & KPIs:** Agent response volumes, median reply times, shift attribution status banner.
- **Tab 3: Influencer Intelligence:** Official database status breakdown, flakers & missed visits audit.
- **Tab 4: Multi-Source Reconciliation (pCloud & Dropbox):**
  - **Sub-Tab 1 (pCloud Coverage Audit):** 4 KPI summary cards, campaign coverage status table, influencer audit drill-down with filters (Missing 7, Not Booked), search, and one-click CSV export for operational teams.
  - **Sub-Tab 2 (Dropbox Reconciliation):** Campaign-level comparison (Target vs Sys Confirms vs Drop Confirms vs Gap) and influencer audit drill-down.
- **Tab 5: Line Health & Infrastructure Status:** WhatsApp lines inventory and monitoring.
- **Sidebar:** Dynamic operational controls with instant cache-clearing (`🔄 Force Reload / Clear Cache`), showing live counts for Roster, Dropbox, and pCloud gaps.

---

## 3. Ground Truth Rules & Constraints for AI Agents

1. **Google Spreadsheet Access:** Read-only (`operations-511207-eb43144fc000.json`). Never mutate or write.
2. **Dropbox Folder Access:** Local files in `C:\Users\DA-05\Dropbox\...` are **STRICT READ-ONLY**. Never write or modify files there.
3. **Active Influencer Definition:** Strictly based on `campaign_influencers.status` in `(2, 7, 8, 11, 13)`. Never use `influencers.active`.
4. **Phone Matching:** Always use dual-column fallback (`p1` then `p2`) and `Right(8)` normalization. Over 50% of matches rely on the second column!
5. **Dynamic DB Migration Readiness:** Keep analysis functions parameterized accepting DataFrames so switching from CSV/Parquet to live SQL connections requires zero architectural changes.

---

## 4. How to Run Locally

```bash
# Launch Streamlit Dashboard
python -m streamlit run src/app.py --server.headless true --server.port 8501

# Localtunnel for Public External Sharing
npx -y localtunnel --port 8501
```
- **Local URL:** `http://localhost:8501`
- **Cached Parquet Layer:** Located in `data/cached_*.parquet` for instant <50ms reloads.

---

## 5. GitHub Integration & Streamlit Cloud Deployment

- **Remote GitHub Repository:** `https://github.com/trygcdata2-hub/testing-whatsapp`
- **Branch:** `main`
- **One-Click Sync Script:** `push_to_github.bat` (automatically stages, commits, and pushes to `main`).
- **Deployment Compatibility Architecture:**
  - `src/app.py`: Primary application source code.
  - `project/src/app.py`: Seamless backward-compatibility forwarder bridging existing Streamlit Cloud configurations pointing to `project/src/app.py`.
  - `app.py`: Root entrypoint bridge.
  - Streamlit Cloud automatically listens to GitHub webhooks on `main` and refreshes the live production dashboard in real time upon every push.

