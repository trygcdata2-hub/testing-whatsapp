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
- `data/last_month_s_data.csv`: WhatsApp messages stream for September 2026.
- `data/documentations for the database.xlsx`: Official database status dictionary.
