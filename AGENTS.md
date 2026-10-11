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
- If an agent logs `Start Time` without `End Time`, assume they worked until the end of their shift (`Morning`: 17:00, `Between`: 01:00 next day, `Night`: 09:00).
- **Simultaneous Overlap Rule (Strict Fairness):** If two or more agents are logged on the same line at the exact same time, **do not guess and do not penalize/reward either agent**—keep the sender as `original whatsapp`.
- If 1 agent is on the line, attribute to that agent. If no agent on that line, fallback to an agent assigned to `All Lines Numbers`.

## 6. Local Dropbox Access Policy
- **STRICT RULE:** Local Dropbox folders (`C:\Users\DA-05\Dropbox\GC - operation live\Campaign Source\...`) are **READ-ONLY**.
- **NEVER** write, modify, delete, or create files inside the Dropbox directory.
- Use `src/reconciliation.py` and the cached parquet layer for lightning-fast reads.
