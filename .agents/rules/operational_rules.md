# Master Operational Rules & Business Logic

## 1. Active Campaigns as Primary Driver
- Always drive reconciliation and analysis from System Active Campaigns defined by `reference/active_campaigns.sql` criteria.
- Never use external drive folders (e.g., pCloud's 392 raw folders or Dropbox) as the master campaign list.
- Use the 4-tier token matcher (Country Guardrail, Core Brand Token Sorting, Month/Year alignment, Jaccard overlap >= 0.50) to bridge naming variations (token ordering, spaces, stopwords).

## 2. Roster Shift Attribution for Live Chat
- **Live Chat Only:** Only roster tasks containing `'live'`, `'response'`, or `'sr.whatsapp'` qualify for message attribution. Tasks for Creation, Calling, or Monitoring are strictly excluded.
- **Strict Neutrality on Overlap:** If two or more agents have live chat duties on the same line at the exact time of an outgoing message, the sender MUST REMAIN `'original whatsapp'`. Never guess or assign credit.
- **End-of-Shift Fallback:** If `End Time` is missing, fallback to shift end (17:00 Morning, 01:00 next day Between, 09:00 Night).

## 3. Database Migration Preparedness
- System architecture is transitioning towards querying live active campaigns and recent message time windows.
- All core functions in `src/pipeline.py`, `src/pcloud_reconciliation.py`, and `src/reconciliation.py` are parameterized to accept DataFrames to guarantee seamless zero-downtime database migration.
