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

### D. Live Operations Dashboard (`src/app.py`)
- Built with Streamlit, Plotly, and responsive dark-mode CSS cards.
- **Tab 1: Live Pulse & Alerts:** Unanswered conversations (Dynamic rule: Influencer sent last), SLA distribution (<15m, 15-60m, >60m).
- **Tab 2: Agent Scorecards & KPIs:** Agent response volumes, median reply times, shift attribution status banner.
- **Tab 3: Influencer Intelligence:** Official database status breakdown, flakers & missed visits audit.
- **Tab 4: Multi-Source Reconciliation (pCloud & Dropbox):**
  - **Sub-Tab 1 (pCloud Coverage Audit):** Scope Selector toggle: Default is **"🔥 الحملات النشطة فقط (وفق معايير SQL - مستحسن)"** (showing the 35 active campaigns, 28 matched, 767 coverages, 403 aligned, 33 critical gaps), with full toggle to view all 203 campaigns.
  - Drill-down table with masked phones, radio filter (Missing Status 7, Not Booked, All), search, and one-click operational CSV export: `📥 تنزيل القائمة الإجرائية لتحديث الـ Status 7 (CSV)`.
  - **Sub-Tab 2 (Dropbox Reconciliation):** Campaign-level comparison (Target vs Sys Confirms vs Drop Confirms vs Gap) and influencer audit drill-down.
- **Tab 5: Line Health & Infrastructure Status:** WhatsApp lines inventory and monitoring.
- **Sidebar:** Dynamic operational controls with instant cache-clearing (`🔄 Force Reload / Clear Cache`), showing live counts for Roster, Dropbox, and pCloud gaps.

---

## 3. Ground Truth Rules & Constraints for AI Agents

1. **Google Spreadsheet Access:** Read-only (`operations-511207-eb43144fc000.json`). Never mutate or write.
2. **Dropbox Folder Access:** Local files in `C:\Users\DA-05\Dropbox\...` are **STRICT READ-ONLY**. Never write or modify files there.
3. **pCloud Folder Access:** Local files in `P:\...` are **STRICT READ-ONLY**. Never write or modify files there.
4. **Active Influencer Definition:** Strictly based on `campaign_influencers.status` in `(2, 7, 8, 11, 13)`. Never use `influencers.active`.
5. **Phone Matching:** Always use dual-column fallback (`p1` then `p2`) and `Right(8)` normalization. Over 50% of matches rely on the second column!
6. **Active Campaigns SQL Scope & Migration Direction:** Active campaigns are driven by `reference/active_campaigns.sql` criteria. External directories (Dropbox, pCloud) are matched against System Active Campaigns, never the reverse. Future DB queries will restrict to active campaigns and recent message windows.
7. **Roster Fairness & Live Chat Rule:** Only shifts with tasks matching `live`, `response`, or `sr.whatsapp` are eligible. If 2+ agents are simultaneously logged on the same line, message remains `original whatsapp` (no guessing, no unfair penalties).
8. **Dynamic DB Migration Readiness:** Keep analysis functions parameterized accepting DataFrames so switching from CSV/Parquet to live SQL connections requires zero architectural changes.

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

