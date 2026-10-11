# Workspace Rules & Constraints

## 1. Google Sheets Access Policy
- **Spreadsheet Link:** `https://docs.google.com/spreadsheets/d/1cmG2xWjcbF-76YOcvPKyn1x_BciElT3F3gyFemE_Kq0/edit`
- **STRICT RULE:** This Google Spreadsheet is **READ-ONLY**.
- **NEVER** write, edit, update, delete, append, or modify any data, cells, or sheets in this Google Spreadsheet under any circumstances.
- Only perform read operations using the service account credentials (`operations-511207-eb43144fc000.json`).

## 2. Influencer Activity Definition (CRITICAL RULE)
- **DO NOT** rely on `influencers.active` to determine if an influencer is active or has participated.
- **GROUND TRUTH RULE:** An active / participating influencer is determined strictly from `campaign_influencers.status` having a value in `(2, 7, 8, 11, 13)`.
  - `2`: Visit (زار)
  - `7`: Posted / Coverage (عمل العملية كاملة ونزل التغطية)
  - `8`: Delivery (استلم دليفري)
  - `11`: Share (اتسجل إنه هيعمل الشير)
  - `13`: Post (اتسجل إنه هينزل بوست)

## 3. Campaign & Data Files Mapping
- `data/campaigns_since_1may.csv`: Active/ongoing campaigns created or active since 1 May 2026.
- `data/campaign_influencers.csv`: Individual influencer campaign booking statuses.
- `data/influencers_master.csv`: Influencer profiles directory.
- `data/last_month_s_data.parquet` / `data/last_month_s_data.csv`: WhatsApp messages stream for September 2026.
- `data/documentations for the database.xlsx`: Official database status dictionary.
- `data/cached_whatsapp_tasks.parquet` & `data/cached_gc_tasks.parquet`: Fast cached shift roster records.
- `data/cached_dropbox_recon_campaigns.parquet` & `data/cached_dropbox_recon_influencers.parquet`: Fast cached Dropbox reconciliation records.

## 4. Phone Mapping & Normalization Rule (CRITICAL)
- **Two Phone Columns Rule:** Always check **both** phone columns with an XLOOKUP fallback logic:
  - In `campaign_influencers`: Primary is `influencer_phone`; Fallback is `influencer_whats_number`.
  - In `influencers_master`: Primary is `phone`; Fallback is `whats_number`.
  - Never query only the primary column; over 50% of active WhatsApp users have their WhatsApp number only in the 2nd column!
- **Right(8) Normalization:** Normalize all phone numbers by stripping non-digits and taking the last 8 digits (`clean_phone[-8:]`). This eliminates variations in country codes (`+966`, `00966`, `966`, `+965`, `+20`, etc.), leading zeros, and formatting.

## 5. Roster Shift Attribution Rules
- **Live Chat Task Filtering:** Only roster records where the task is designated for Live Chat / Instant Response (`'live'`, `'response'`, or `'sr.whatsapp'` in task description) are eligible for message attribution. Tasks for creation, calls, or monitoring are strictly ignored.
- **End-of-Shift Fallback:** If an agent logs `Start Time` without `End Time`, assume they worked until the end of their shift (`Morning`: 17:00, `Between`: 01:00 next day, `Night`: 09:00).
- **Simultaneous Overlap Rule (Strict Fairness):** If two or more agents are logged on the same line at the exact same time, **do not guess and do not penalize/reward either agent**—keep the sender as `original whatsapp`.
- **All Lines Numbers Fallback:** If 1 agent is on the line, attribute to that agent. If no agent is on that line, fallback to an agent assigned to `All Lines Numbers`. If multiple agents are assigned to `All Lines Numbers` at that time, keep as `original whatsapp`.

## 6. Local Dropbox Access Policy
- **STRICT RULE:** Local Dropbox folders (`C:\Users\DA-05\Dropbox\GC - operation live\Campaign Source\...`) are **READ-ONLY**.
- **NEVER** write, modify, delete, or create files inside the Dropbox directory.
- Use `src/reconciliation.py` and the cached parquet layer for lightning-fast reads.

## 7. Local pCloud Access & Coverage Status 7 Audit Policy
- **STRICT RULE:** Local pCloud folders (`P:\Operation - Head Office\Coverages-Final\...` or `P:\pCloud Drive\...`) are **READ-ONLY**. Never mutate or write to pCloud.
- **Source Definition:** pCloud stores raw uploaded coverage media (images, videos, reels, stories) across active campaigns in KSA, UAE, KW, and EGY.
- **Status 7 Ground Truth Rule:** An influencer with coverage uploaded to pCloud must have `campaign_influencers.status_id = 7` (Posted / Completed Coverage). Any influencer present in pCloud coverage but having `status_id != 7` represents an Operational Gap (Missing Status 7).
- **Fast Parquet Layer:** Always read/write through `src/pcloud_reconciliation.py` and cached parquets (`data/cached_pcloud_recon_campaigns.parquet` & `data/cached_pcloud_recon_influencers.parquet`) for zero-latency UI performance and cloud deployment resilience.

## 8. Active Campaigns SQL Scope & Future Migration Direction (CRITICAL)
- **Single Source of Truth:** Active campaigns are defined strictly by the logic in `reference/active_campaigns.sql` (`c.status IN (1, 4)` or recent `(2, 6)` within 30 days, or visit date window).
- **Driver Direction Rule:** Do **NOT** treat external directory structures (e.g., ~392 raw folders in pCloud) as the master list of active campaigns. Always drive reconciliation and monitoring from the **System Active Campaigns** outwards.
- **Migration Preparedness:** The operational architecture is shifting towards pulling *strictly active campaigns* and bounded recent WhatsApp message streams. All pipeline modules must remain modular and filter by active campaign criteria so database migrations occur seamlessly without code breakage.

## 9. Multi-Layer Campaign Matching Architecture
- **Problem:** Campaign names differ between System DB and local drives (Dropbox/pCloud) due to token ordering (e.g., date at end vs. country at end), spacing variations, boilerplate stopwords, and regional prefixes.
- **Mandatory 4-Tier Matching Hierarchy:**
  1. **Strict Country Guardrail:** Never match campaigns across different country boundaries (e.g. KSA to KW or UAE).
  2. **Core Brand Token Sorting:** Strip boilerplate stopwords (`visit`, `delivery`, `highest platform`, `approach`, etc.), clean special characters, and sort brand tokens alphabetically to neutralize token order differences (e.g., `Brand Oct KSA` == `KSA Brand Oct`).
  3. **Month & Year Alignment:** Prevent matching campaigns with identical brand names across different operational months.
  4. **Jaccard Token Similarity & Fuzzy Matching:** Fallback to token intersection similarity (threshold >= 0.50) to catch minor typos (e.g., `Withdrw` vs `Withdraw`).

## 10. Master Business Rules & AI Model Memory (MANDATORY FOR ALL FUTURE AGENTS)
- **Live Chat Duty Exclusive:** Outbound messages sent as `original whatsapp` can ONLY be attributed to agents whose shift task is explicitly Live Chat / Instant Response (`'live'`, `'response'`, `'sr.whatsapp'`). Non-chat tasks (Creation, Calling, Monitoring) are strictly forbidden from receiving message credit.
- **Strict Overlap Neutrality:** If 2 or more agents have overlapping Live Chat duties on the same line at the exact time of message dispatch, the message MUST REMAIN `original whatsapp`. Never guess, split, or arbitrarily award messages.
- **Strict Full-Duration Response Time (No Session Timeout / No Forgiveness):** If an influencer was the last sender awaiting a reply, the reply duration MUST be measured in full from the influencer's message timestamp until the agent's reply is dispatched (`reply_time - burst_start_time`), regardless of how many hours or days elapsed. Never artificially forgive, drop, or reset waiting time with a 24-hour session timeout; customer waiting time is a real operational metric and SLA breach that must be accurately exposed.
- **System DB as the Driver:** Reconciliation NEVER treats external drives (pCloud's ~392 folders or Dropbox workbooks) as the master source of campaigns. Reconciliation ALWAYS starts from System Active Campaigns (`reference/active_campaigns.sql`) and looks outward to verify external assets.
- **Dynamic Database Migration Direction:** Future system updates will migrate from static files (May-to-date CSVs, all-time WhatsApp messages) to bounded live SQL queries targeting strictly active campaigns and bounded recent WhatsApp windows. All code modules must accept DataFrames and remain fully decoupled from file paths to ensure zero breakage upon live SQL cutover.




