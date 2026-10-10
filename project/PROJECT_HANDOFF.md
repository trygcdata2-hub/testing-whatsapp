# PROJECT HANDOFF — WhatsApp Pro tracking system

> Read this file top to bottom before touching any code. It records what was analysed, how, what was decided, and what to build next.
> The project owner writes Egyptian Arabic. Talk to them in Arabic; keep code, comments and docs in English. Arabic keywords inside regexes are intentional.

---

## 0. How to work with this file (instructions for the agent)

1. Read sections 1–3 first (goal, files, data). Do not run anything yet.
2. Read section 4 (what was already built) and section 5 (the campaign report script). Open the referenced files as you go.
3. Read section 6 (the design discussion) and section 8 (first tasks).
4. Before writing code, summarise back to the owner in Arabic, in 10 lines max: the goal, the three data sources, the join key, and what you plan to build first. Wait for a yes.
5. Never commit raw data, credentials, or phone numbers (see section 9).

---

## 1. Goal and context

The company runs influencer campaigns (restaurants, cafes, brands) in KSA, Kuwait, UAE and Egypt. An operations team ("WhatsApp Pro team", ~25 agents) talks to influencers on WhatsApp Pro: they send invitations, answer questions, chase confirmations, and send logistics (address, brief, code). Confirmed influencers then visit / receive a delivery and post coverage.

The owner is a data analyst who needs:

1. A **tracking system for the operations manager** to monitor the WhatsApp team (speed, unanswered chats, follow-up after yes, persuasion quality), and
2. A way to **tie that behaviour to real campaign outcomes** (confirmed, visited, covered) from the System database, and to the **Dropbox sheets** the team fills by hand.

So far (this conversation) we produced a monthly analysis workbook and a design for the system. The next step is to turn the analysis into a maintained pipeline + dashboard.

---

## 2. Folder layout and file index

Expected layout (the owner places the files; names may differ slightly, adjust paths if so):

```
project/
├── PROJECT_HANDOFF.md                      <- this file
├── data/                                   <- git-ignored, contains PII
│   └── last_month_s_data.csv               raw WhatsApp export (4 Sep -> 3 Oct 2026)
├── reference/
│   ├── agent_performance_oct3.xlsx         ONE-DAY analysis the owner built earlier (format template)
│   ├── agent_performance_last_month.xlsx   MONTHLY analysis produced in this conversation
│   ├── active_campaigns.sql                System DB query: daily report for active campaigns
│   ├── dropbox_vs_system_report.py         Owner's script: compares System sheet vs Dropbox, writes WhatsApp text report
│   └── analysis_pipeline/                  Python that produced the monthly workbook
│       ├── prep.py  analysis.py  tables.py  tables2.py  build.py
│       └── whatsapp_messages_extract.sql
└── docs/ERD images (Whatsapp Pro DB, System DB)  <- described in section 3
```

Read order and purpose:

| # | File | What it is | Why read it |
|---|------|-----------|-------------|
| 1 | `reference/agent_performance_oct3.xlsx` | One-day analysis (3 Oct 2026, 4,900 messages). Sheets: Playbook, Scorecard, Ranking, Persuasion, Templates, Message_Features, After_Yes, Objections, Notes, Baselines + evidence sheets (Response_Events, Agent_Threads, Messages, Turns, Yes_Events, Inbound_Msgs). | Defines the target format and the metric families the owner cares about. Read the `Notes` sheet first for definitions. |
| 2 | `reference/agent_performance_last_month.xlsx` | Same analysis over 30 days, plus new sheets (Daily_Trend, Hourly_Coverage, Weekly_Agent, Funnel_Segments). | The result of section 4. Read `Playbook` and `Notes` sheets. |
| 3 | `reference/analysis_pipeline/*.py` | The code that built #2. | Starting point for the ETL. See section 4 for how it works and what is fragile. |
| 4 | `reference/active_campaigns.sql` | System DB query returning one row per active campaign (targets, confirmations, visits, coverage...). | It is the source of System-side numbers (section 5). |
| 5 | `reference/dropbox_vs_system_report.py` | Owner's script. Reads the query output as an Excel sheet, scans Dropbox campaign files, compares both, generates a text report with tasks per team. | Shows how Dropbox sheets are structured and already-agreed business rules (section 5). |
| 6 | `data/last_month_s_data.csv` | Raw export, 183,152 rows. | Only open samples (`head`, not the full file in chat). Contains phone numbers and message text. |

---

## 3. Data sources

### 3.1 WhatsApp Pro DB (MySQL)

ERD (from the owner's diagram):

- `Message`: `id` (PK), `roomId` (FK -> Room), `whatsappAccId` (FK -> Whatsapp), `content`, `isFromMe`, `createdAt`. The export also uses `type`, `isRead`, `isSystem`, `userName`, `isInvitation`, `deletedAt` (not drawn in the ERD but present in the table).
- `Room`: `id`, `contactId` (FK -> Contact).
- `Contact`: `id`, `phone` = the **influencer's** phone.
- `Whatsapp`: `id`, `name`, `phone` = **our** number (the account the agents use).

Extraction query used for the monthly file (see `whatsapp_messages_extract.sql`):

```sql
SELECT c.phone, m.content, m.createdAt, m.`type`, m.isRead, m.isFromMe, m.isSystem,
       m.whatsappAccId, m.userName, m.isInvitation
FROM `Message` m
LEFT JOIN Room r    ON r.id = m.roomId
LEFT JOIN Contact c ON c.id = r.contactId
WHERE m.createdAt >= CURDATE() - INTERVAL 1 MONTH
  AND m.createdAt <  CURDATE()
  AND m.deletedAt IS NULL;
```

Column semantics learned from the data:

- `isFromMe = 0` -> message from the influencer.
- `isFromMe = 1` and `userName` is a real name -> sent by that agent from the platform.
- `isFromMe = 1` and `userName = 'original whatsapp'` -> sent from the phone itself. **Cannot be attributed to an agent.** 23,657 messages (about a quarter of all outgoing) after cleaning.
- `isSystem = 1` -> system rows ("Whatsapp number changed from X to Y"). Ignored.
- `isInvitation = 1` -> invitation sent by the platform. 10,450 rows in the month, but populated mostly for five accounts (Nada Seliman, Nour Zein, Mohamed Atia, Ahmed Almahdi, Khaled Mohamed). Other agents' pitches are detected by wording.
- `phone` can be NULL (about 13.8K rows: group chats, @mentions).
- Some `phone` values are 18 digits starting with `120` (about 5.8K rows). These look like **WhatsApp group IDs**, not influencer numbers. They were NOT excluded in the first run (see known issues).
- Raw export contains 831 exact duplicate rows.
- Test/admin accounts present: `trainee01`, `Developers Team`, `IT Team`.
- Timestamps are used as exported (no timezone conversion). Night-shift agents exist (messages around 00:00–05:00).

### 3.2 System DB (campaigns)

From the owner's diagram, the tables that matter:

- `campaigns` (name, brand_id, sub_brand_id, status, visit_start/end_date, deliver_start/end_date, campaign_type, target fields)
- `campaign_influencers` (campaign_id, influencers_id, status, branch_id, brand_id, confirmation_date, request_for_approval, deleted_at) — one row per influencer per campaign. **This is the ground truth for confirmed / visited / covered / missed.**
- `influencers` (phone, **whats_number**, country_id, state_id, city_id, usernames for instagram/tiktok/snapchat, nationality, active...)
- `campaign_influencer_coverages` and per-platform `*_stories` tables (coverage links, views, manual vs scraped)
- `brands` (parent_id, is_grand, is_elite, office_id), `branches`, `countries`, `states`, `cities`, `offices`, `feedback`, `users`.

### 3.3 Dropbox sheets (manual log)

Excel files per campaign under `Campaign Source/<country>/<Grand Community|Elite>/Active Campaigns/...`. Two relevant sheet types:

- A "COMP" sheet (confirmations list): username, date, visited/delivery status, overall coverage state.
- A "LIST" sheet (outreach list, header on row 3): `Statu 1` status values (Pending, Confirmed, Visited, No Response, Block, Paid ads, Not Found, Traveling, Cancelled By Client, Cancelled By Community, No Match, Refused) and counters `Inv.`, `Rem. 1`, `Rem. 2`, `Username`, `Notes`, `Send To Community`.

The WhatsApp Pro team writes into these sheets based on influencers' replies.

### 3.4 The cross-database link

The two databases are separate. The owner currently links them manually with XLOOKUP on the **influencer phone number**. The system should do this once, centrally, in the ETL (section 6.2).

---

## 4. What we built in this conversation (work log)

### 4.1 Request

The owner sent (a) the one-day workbook `agent_performance_oct3.xlsx` and (b) the monthly raw export, and asked for a **comprehensive monthly analysis in the same format as the one-day file, but stronger, and quickly**.

### 4.2 Reading the one-day workbook

I read every analysis sheet. Key points reused:

- Playbook structure: who persuades best / what wording works / where leads are lost / what influencers object to / do next.
- Scorecard: per agent counts, reply-time stats (median, avg, P90, %<=5/15/60 min), unanswered, influencer reply rate, positive replies, invitations, confirmations, template share, media.
- Ranking: composite with editable weights (blue input cells) and formulas.
- Persuasion: per agent accept rate vs *expected* (team accept rate for the same message-kind mix), lift, z-score, Wilson CI, verdict.
- Templates, Message_Features, After_Yes, Objections, Baselines, Notes.
- Evidence sheets: Response_Events, Agent_Threads, Messages, Turns, Yes_Events, Inbound_Msgs.

### 4.3 Pipeline (files in `analysis_pipeline/`)

Run order: `prep.py` -> `analysis.py` -> `tables.py` -> `tables2.py` -> `build.py`. Intermediate state is stored as pickles in `/home/claude` (change paths for local use). Dependencies: pandas, numpy, openpyxl. After `build.py`, the workbook formulas must be recalculated (I used LibreOffice headless; Excel recalculates on open).

**prep.py — cleaning**

- Load CSV as strings (`utf-8-sig`), drop exact duplicates (831), drop `isSystem = 1` and rows with NULL phone.
- Result: 163,979 messages; 92,167 outgoing, of which 68,510 attributed to an agent and 23,657 phone-sent.
- Adds `out`, `agent`, `phone_sent`, `inv`, `media`; sorts by phone, time.

**analysis.py — runs, response events, turns**

- Arabic text normalisation (`norm`): NFKC, lowercase, strip diacritics/tatweel, unify alef/yaa/taa-marbuta.
- Country from phone prefix: 966 KSA, 965 Kuwait, 971 UAE, 974 Qatar, 20x Egypt, else Other.
- **Runs**: consecutive messages in the same direction for the same phone.
- **Inbound burst** = an inbound run. **Reply** = start of the next outgoing run. `rt_min` = minutes from the burst's first message to that reply, credited to the agent who sent it (or "Phone (unattributed)").
- `closer_only`: burst made only of closing words/emoji/stickers (thanks, ok, 👍). Not counted as unanswered.
- **Unanswered** = no reply, or reply later than 24h; excluding closer-only bursts and bursts in the last 3 hours of the data (`pending`). Credited to the last agent who wrote in that conversation (`prev_agent`). Overnight gaps are included in reply time (use medians).
- **Turn** = consecutive outgoing messages in one conversation; a new turn starts when the run changes, the agent changes, or the gap between consecutive messages exceeds 30 minutes.
- Turn outcome: `replied` = the influencer wrote next within 24h. `accepted` = the first 1–3 short (<=40 chars) messages of that reply contain an acceptance word (تم، تمام، اوكي، ابشر، مناسب، ايوه، اكيد، yes، ok، 👍) without negation; zeroed if a decline regex matches (اعتذر، مشغول، مسافر ...). `payment_q` flags payment wording.
- **Message kind** (rule order): `isInvitation` flag -> PITCH; >=600 chars or logistics keywords (address, brief, maps links, order, code) -> LOGISTICS; confirmation wording -> CONFIRM; post-visit wording (review, repost, story) -> POST_VISIT; invitation wording and >=40 chars -> PITCH; chasing wording -> REMINDER; else CHAT. `ask_turn` = PITCH, REMINDER or CHAT.
- **Brand**: first match in a list of ~20 keyword patterns (Dopamine, Creation Burger, Bloomore/BMORE, Shrimp Zone, Jones the Grocer, Jade Room, Pilatta, Triowalite, Society by Sofleur, Dr. Scent, Black Tap, Tashas, Pizzarati, SO by Sora, Brands For Less, FNP, Table to, Riyadh book launch, Saudi National Day, Brunch & Cake); fallback to the most common brand in that phone's turns; else Unknown.
- Message features per turn: starts with emoji, greeting opener, "send تم" call-to-action, ends with question mark, urgency wording, perk/benefit wording, Gulf dialect markers, contains question, proposes day/time, closed question (question and <=80 chars), length bucket, `template_key` (first 45 normalised chars, only openings seen 15+ times).

**tables.py / tables2.py — aggregates**

- Baselines: accept/reply rate per message kind (ask-turns), and per kind × brand when >=50 turns.
- **Persuasion**: `expected_accepts = sum(baseline)`, `lift = actual / expected`, `z = (actual - expected) / sqrt(expected)`, Wilson 95% CI. Verdict uses the kind × brand z and requires 100+ ask-turns: z >= 3 clearly above, <= -3 clearly below, |z| 1.5–3 leaning, otherwise in line. Stricter than the one-day file because 30+ agents are compared at once.
- **Scorecard**: per-agent metrics. Roles: Inbox responder (>=100 replies), Outreach/templates (>=300 messages but few replies), Low volume, Test/admin. **Own-shift median**: only bursts arriving in hours that hold >=4% of that agent's messages, so night-shift agents are not penalised.
- **Ranking**: weights in editable cells (speed 35%, unanswered 25%, reply rate 20%, positive 20%), minimum 100 replies and 5 active days, ranks via COUNTIFS (live formulas).
- **Message_Features**: with/without comparison inside the same kind, brand-adjusted lift, two-proportion test, `Robust?` flag (>=100 in both groups, p < 0.01, adjusted lift same direction).
- Hour/length tables, brand/country/weekday segments, templates (openings used 40+ times).
- **After_Yes**: "real yes" = accepted ask-turn (excluding last 3 hours of data); followed = next agent turn in that thread within 24h; follow-up minutes from the influencer's reply.
- Objections: keyword topic tagging of inbound text (date/time, branch/location, content requirements, menu, payment, declines, delivery, code/discount, guests, reschedule) split by brand and country.
- Time series: Daily_Trend, Hourly_Coverage (inbound per day, agents active, inbound per active agent, median reply, unanswered rate by arrival hour), Weekly_Agent (W1–W4).
- Conversation funnel by phone: pitched -> replied -> real yes -> logistics sent after yes -> post-visit follow-up.

**build.py — workbook**

Builds `agent_performance_last_month.xlsx` with openpyxl: Playbook (text is generated from the computed numbers, so it stays consistent), Scorecard (rates and team totals as formulas), Ranking (formulas), the analysis sheets, charts on Daily_Trend and Hourly_Coverage, and evidence sheets (`Turns` text truncated to 300 chars, `Inbound_Msgs` limited to the first 15,000 topic-tagged messages).

### 4.4 Validation against the one-day file

I re-ran the turn logic on 3 Oct and compared it with the one-day `Turns` sheet (matching on phone + sent_at): 1,533 of 1,544 turns matched; `replied` agreed on 88%, `accepted` on 94%. Kind classification was tuned afterwards, and then the PITCH wording regex was broadened (added تفوت، متحمسين، جديد، عرض، تجربه، زياره، حمله). **That last change was not re-validated** (see known issues).

Numbers differ slightly from the one-day file because the monthly run includes every conversation (not only those where a named agent wrote) and splits turns by agent change / 30-minute gap. Compare agents only inside one file.

### 4.5 Main findings (month: 4 Sep – 3 Oct 2026)

Volume: 163,979 messages, 12,539 conversations, 40,265 inbound bursts, 76,509 agent turns, 24 real inbox responders.

- **Speed**: team median reply 39 min; 34% answered within 15 min, 59% within 60 min. Fastest own-shift medians: Fatma Elzahraa (11 min), Mostafa Mohamed (12). Slowest: Abdel Rahman Mohamed (142), Abdelhamid Mahrous (81), Madden Ahmed (79).
- **Unanswered**: 4,654 bursts (12.0% of answerable); 1,479 of them in conversations where no agent had written yet (influencer-initiated chats nobody picked up). Worst days: 23 Sep (24%) and 24 Sep (20%). 266 conversations were never answered at all.
- **Staffing gap**: about 4.7 agents active on average between 15:00 and 20:59 vs 8.6 at 12:00–14:59; only about 2.1 agents between 21:00 and 23:59, where the median reply time is 307–370 min. Load per active agent peaks around 16:00 (about 19 bursts per agent-hour).
- **After yes**: 8,724 real yeses; 6,874 credited to an agent and old enough to check. 19% (1,279) got no agent message within 24h; median time to follow-up 58 min.
- **Funnel (conversation level)**: 10,628 pitched -> 5,700 replied -> 3,593 real yes -> 1,303 received address/brief afterwards -> 888 post-visit follow-up. (Keyword-based, treat as a floor.)
- **Persuasion (kind × brand adjusted, 100+ turns)**: clearly above expected: Nour Zein (1.22x), Khaled Mohamed (1.31x), Mohamed abdelhamied (1.18x); Shawq Al-Ulayani 1.70x on only 229 turns. Clearly below: Youssef Mohammed Elsayed (0.60x), Hoda Ahmed (0.60x), Nada Seliman (0.71x), Esraa Ahmed (0.79x). Caveat: pitches that ask the influencer to send «تم» are easier to "accept", so template-heavy accounts get a head-start.
- **Wording (brand-adjusted)**: ending a pitch with a question lifts reply (60% vs 36%); urgency / "limited time" wording hurts (30% reply, 9.5% accept vs 41% / 14.0%); shared templates underperform personal pitches (34% / 11.7% vs 46% / 15.3%); asking to send «تم» raises accept (17.1% vs 11.3%) but lowers reply; in chat, short closed questions get more replies (79% vs 57%) and proposing a day/time lifts accept (19.6% vs 12.6%). Two one-day findings did **not** hold over a month: Gulf-dialect pitches and greeting openers.
- **Brands**: pitch accept rate best for Brands For Less (30%), Tashas (20%), Triowalite (18%); weakest Dr. Scent (4.4%, reply 17%), Jade Room (4.7%), SO by Sora (5.9%).
- **Countries**: ask-turn reply rate Kuwait 29% vs KSA 49%; accept 7.8% vs 13.7%.
- **Top influencer topics**: date/time (6,286 messages), branch/location (3,078), content requirements (2,847), payment (2,724).

### 4.6 Known issues and limitations (fix these when productionising)

1. **Group chats not excluded**: phones that are 18 digits starting with `120` are probably WhatsApp groups (about 5.8K rows, ~3.5%). Exclude them in the ETL.
2. **PITCH regex not re-validated** after it was broadened. Re-run the Oct-3 comparison and tune.
3. **Phone-sent messages** (23.7K) cannot be attributed; they count in conversations but not for any agent.
4. **Keyword-based** classification for yes, kind, brand and logistics is approximate. Real status must come from the System DB.
5. **No campaign id on messages**; brand is guessed from wording.
6. Shift detection is a heuristic (>=4% of an agent's messages in that hour). Shared WhatsApp accounts (`whatsappAccId`) and hand-offs blur individual responsibility.
7. Pipeline structure is fragile: `tables2.py` re-reads `tables.py` with `exec(... .split(...))`; intermediate pickles live in `/home/claude`; paths are hard-coded.
8. `Turns` and `Inbound_Msgs` evidence sheets are truncated; the full text is only in the CSV.
9. `isInvitation` is populated for only a few accounts.
10. Timestamps have no timezone conversion.

---

## 5. Active campaigns query and the Dropbox comparison script

### 5.1 `active_campaigns.sql`

Purpose: a daily report row per **active campaign** from the System DB. Structure:

- CTE `ci_summary` over `campaign_influencers` (not deleted), grouped by `campaign_id`, using status groups that are business definitions worth keeping:
  - Confirmations: status IN (1,2,3,7,8,11,13)
  - Visited: status IN (2,7,8,11,13)
  - Missing coverage: status IN (2,8)
  - Missed visit: status IN (3,9)
  - Coverage: status IN (7,11,13)
  - Approved: status = 15
  - Reject: status IN (10,17,18)
  - Request for approval: `request_for_approval = 'pending'`
  - Today / tomorrow / day after visits from `confirmation_date`.
- Main query joins `campaigns`, `brands` (and parent brand) and outputs campaign name, status label (1 On going, 2 Finished, 4 Upcoming, 6 On Hold), **country guessed by regex on the campaign name**, type label (0 Visit, 1 Delivery, 2 Mix, 3 Share, 4 Post Creation), total list, confirmations, **Target** (total_target_reach minus the extra visit/delivery target depending on type), visited, coverage, missing coverage, missed visit, approved, reject, request_for_approval, daily target, start/end dates (delivery campaigns use the deliver dates).
- Filters: parent brand not in (3251, 2395); on going / upcoming campaigns that started within 4 months; finished / on hold campaigns that ended between 5 days ago and yesterday.

Notes for the agent: the query returns no `Real Target` column, but the Python script reads one (it silently falls back to 0). Country detection by campaign name is brittle; prefer joining on branch/brand country if available.

### 5.2 `dropbox_vs_system_report.py`

Owner's script, Windows paths, runs manually. Steps:

1. **Extract from Dropbox** (`SOURCE_FOLDERS`: KSA, UAE, KW, EGY; Grand Community and Elite): for each Excel file find the COMP sheet and compute all confirmations, confirmations with date, visited / delivered, missing visit and missing coverage for old dates, coverage count; from LIST sheets compute counts of `Statu 1` values and `Inv.`, `Rem. 1`, `Rem. 2`, `Username`, `Notes`, `Send To Community`. Delivery vs visit is detected from the path or campaign name.
2. **Match with System**: reads the Excel produced by the query (sheet "Campaigns"), filters statuses (on going, on hold, upcoming, finished), matches campaigns with `smart_key` (lowercase, remove "tiktok", sort alphanumeric words) and writes `Drop: x | Sys: y` where the values differ.
3. **Generate a WhatsApp-style text report**: KPIs overall and per country, campaigns sorted CRITICAL (coverage < target and confirmations with date < target) vs OK, and **tasks per team**: Coverage (find missing links), Follow-up (missed visits), WhatsApp team (confirmation gap: remaining Inv / Rem1 / Rem2 funnel), Community (list too small: total list < 3× target, list exhausted, or <=3 days left and gap), Onboarding (look-alikes from approved profiles), Coordination (System vs Dropbox mismatch).

Known issues in the script: `CURRENT_DATE` is hard-coded (2026-09-01), Windows paths, name matching by `smart_key` can mis-match similar campaign names, interactive `input()` at the end, and the `Real Target` gap above.

---

## 6. Design discussion: the tracking system

### 6.1 How the three sources connect

- **Join key `phone_key`**: build it once in the ETL: digits only, strip `+` and `00`, fix a leading `0` using the influencer's country, keep country prefix; match against `influencers.phone` **and** `influencers.whats_number` and `Contact.phone`. Fallback: compare the last 8–9 digits. Exclude group IDs. This replaces the manual XLOOKUP.
- **WhatsApp = behaviour** (who answered, how fast, what was said).
- **System = outcome truth** (`campaign_influencers.status`, `confirmation_date`, visited, coverage). It replaces the keyword guess for "yes" and fills the "booking status" gap listed in the workbook's "Data to add".
- **Dropbox = manual log**. Use it as a cross-check: compare logged `Inv.` / `Rem. 1` / `Rem. 2` against actual invitations/reminders in WhatsApp, and logged "Confirmed" against the System status. This measures logging discipline. Long term, the team should record status directly in the System and Dropbox becomes legacy.
- **Attribution gap**: messages have no `campaign_id`. Infer: for a phone, find `campaign_influencers` rows active in a window around the message; if exactly one, attribute; otherwise mark `ambiguous`. Best fix: ask the developers to add `campaign_id` to `Message`.

### 6.2 Architecture decided

```
WhatsApp Pro DB ┐
System DB       ├─> Python ETL (read replica, incremental, ~15 min) -> Reporting DB -> Metrics & rules -> Outputs
Dropbox sheets  ┘                                                     (phone_key)                         ├ Manager board (Streamlit)
                                                                                                          ├ Agent self-view
                                                                                                          ├ Alerts (push)
                                                                                                          └ Daily report (txt + Excel)
```

- Run extraction on a **read replica**, with a watermark (`createdAt > last_run`) instead of a month-wide `LEFT JOIN` on production.
- Reporting DB tables (suggested): `dim_agent`, `dim_influencer` (phone_key), `dim_campaign`, `fact_message`, `fact_inbound_burst`, `fact_turn`, `fact_yes`, `fact_campaign_influencer`, `fact_dropbox_row`, plus daily/hourly aggregates.
- Port the logic of `analysis.py` / `tables*.py` into this ETL as tested functions, with the definitions of section 4.3 as the contract.
- Port the task logic of the campaign report script (CRITICAL/OK and tasks per team) as a metrics module.

### 6.3 Is Streamlit the right choice?

Yes for version 1, as a **thin display layer only**:

- Pros: Python-native (same pandas logic), fast to build, interactive filters, drill-down to a conversation.
- Cons: no real RBAC (manager vs agent) so put SSO/OIDC or a reverse proxy in front; it reruns the script on every interaction so read precomputed tables with caching; no scheduling or push alerts inside it (use cron/Prefect/Airflow for ETL and alerts); fine for roughly 10–30 users.
- Power BI / Metabase can sit on the same Reporting DB later if the manager wants free pivots. The value is in the data model; the UI is replaceable.

### 6.4 Manager views

1. **Live board** (refresh 5–15 min): unanswered now and oldest wait, "yes" waiting for follow-up, median reply today vs month, who is on shift vs inbound load, Dropbox/System mismatches.
2. **Team scorecard**: the monthly scorecard logic, own-shift medians, persuasion lift with CI, weekly trend.
3. **Campaign funnel**: pitched -> replied -> yes -> confirmed in System -> visited -> covered, by campaign and by agent; feeds the daily campaign report.
4. **Data quality**: System vs Dropbox mismatches, WhatsApp vs Dropbox logging gaps, phone-sent (unattributed) share, ambiguous campaign attribution.

Alerts to push (WhatsApp/Slack/email): influencer waiting > 15/30 min, yes without follow-up in 15 min, campaign short of target with <= 3 days left, evening coverage below N agents.

### 6.5 Fairness note

Agree metric definitions with the team before using them for evaluation (shifts, shared accounts, template-heavy roles, small samples). Show agents their own numbers; use the tool for coaching, not only ranking.

### 6.6 Phases (rough estimates)

- **Phase 0 (2–3 days)**: `phone_key`, Reporting DB schema, read-replica access, exclude groups, decide hosting.
- **Phase 1 (~1 week)**: ETL for WhatsApp + System, port analysis to tables, Streamlit manager v1 (live board + scorecard).
- **Phase 2**: funnel joined with System, Dropbox ingestion (reuse extraction functions from the script), data-quality tab, push alerts.
- **Phase 3**: login and roles, agent self-view, `campaign_id` on messages, move status logging from Dropbox to System.

---

## 7. Definitions cheat sheet

| Term | Definition |
|------|-----------|
| Inbound burst | Consecutive influencer messages in one conversation (one run). Clock starts at its first message. |
| Reply time | Minutes from burst start to the next outgoing message; credited to the sender. Includes overnight gaps; use medians. |
| Unanswered | No reply within 24h, excluding closer-only bursts and the last 3 hours of data; credited to the last agent who wrote in that conversation. |
| Turn | Run of consecutive outgoing messages (same agent, gaps <= 30 min). |
| Ask-turn | Turn of kind PITCH, REMINDER or CHAT. |
| Replied / Accepted | Influencer wrote next within 24h / that reply holds an acceptance word without negation or decline. |
| Real yes | An accepted ask-turn (acknowledgements after logistics are excluded). |
| Follow-up | Next outgoing turn in the same thread within 24h of the yes. |
| Expected accepts / Lift / z | Sum of team baseline per turn (by kind, and by kind × brand); actual ÷ expected; (actual − expected) ÷ sqrt(expected). |
| Own-shift median | Median reply time using only bursts that arrived in hours the agent normally works (>=4% of their messages). |
| Template share | Share of an agent's messages longer than 25 chars that the team sent verbatim 3+ times. |

---

## 8. Suggested first tasks for the agent (in order)

1. Create the repo structure of section 2 and a `.gitignore` for `data/`, `*.csv`, `*.xlsx`, `*.pkl`, `.env`.
2. Refactor `reference/analysis_pipeline` into a package: config (paths via env), `clean`, `runs`, `turns`, `features`, `metrics`, with unit tests using a small synthetic dataset.
3. Fix known issues 1, 2 and 7 from section 4.6 (exclude groups, re-validate PITCH rules against `agent_performance_oct3.xlsx`, remove the `exec` trick and pickles).
4. Write the `phone_key` normaliser with tests (KSA 966, Kuwait 965, UAE 971, Qatar 974, Egypt 20, leading zeros, `+`, `00`), and an audit script that reports how many WhatsApp phones match `influencers.phone` / `whats_number`.
5. Draft the Reporting DB schema (section 6.2) and an incremental ETL for `Message/Room/Contact`.
6. Add the System DB extract for `campaign_influencers` (status, confirmation_date, coverage) and compute the extended funnel.
7. Build Streamlit v1: live board + scorecard reading from the Reporting DB.
8. Wrap the Dropbox extraction functions from `dropbox_vs_system_report.py` as a scheduled job writing `fact_dropbox_row`.

---

## 9. Guardrails

- Do not commit or print real phone numbers, message text, or the CSV. Work on a small anonymised sample (hash phones, drop `content`) for tests and demos.
- No credentials in code or in this repo: use environment variables / a secrets manager. Use **read-only** DB users.
- Do not run heavy queries on the production primary; use the replica and incremental loads.
- Keep metric definitions in one module and document any change here.

---

## 10. Open questions to settle with the owner

1. Hosting: is there a server/DB for the Reporting DB (MySQL/Postgres), or start with a local DuckDB file?
2. Can the developers add `campaign_id` to `Message` and stop agents from sending from the phone directly?
3. Who is the audience: only the operations manager, or agents too? Is SSO available for login?
4. Which alerts and thresholds does the manager want (15 vs 30 min, evening coverage minimum)?
5. Target date for retiring the Dropbox sheets in favour of the System as the single source of truth.
