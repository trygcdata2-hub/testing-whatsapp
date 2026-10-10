# Operations Recommendations & Open Points (v2 — final)

> Source: monthly analysis (4 Sep – 3 Oct 2026), `agent_performance_last_month.xlsx`, `PROJECT_HANDOFF.md`, and the owner's review of v1.
> Structure:
> - **Part A** – recommendations for the operations manager, each with its reason and status.
> - **Part B** – points that were unclear in v1: what we now know (decided), and what is still open.
> - **Part C** – action list (who does what).
> - **Part D** – metric rules that change because of the clarifications.
>
> Removed from v1 (owner decision): A9 (weak brands — brands have different priorities and get less experienced influencers on purpose), A10 (move logging from Dropbox to System), A11 (developer requests: `campaign_id` on messages, fix `isInvitation`). Old B8 (objection topic tagging) was dropped as unclear / low value.

---

## Summary

| # | Recommendation | Status | Depends on |
|---|----------------|--------|------------|
| A1 | More agents from 15:00 to 24:00 | Ready after roster check | B4, B11 |
| A2 | Link the shift roster to unanswered messages to assign ownership | **Decided** | B11 (roster sheet) |
| A3 | Clickable "Yes" button / poll in chat; meanwhile track agent-sent confirmation phrases | **Decided** | B2 |
| A3.1 | Verify the funnel / after-yes numbers with real examples before acting | Open | B5 |
| A4 | All sending through the platform only (no phone app) | **Decided** (covers the attribution gap in A3) | B3 |
| A5 | Improve invitation wording (A/B test) | Unchanged | B2, B6 |
| A6 | Ready replies for frequent questions | Unchanged | — |
| A7 | Persuasion coaching (not evaluation) | Unchanged, low confidence | B2, B6, B10 |
| A8 | Kuwait-specific plan | Unchanged | — (B9 closed) |

---

## Part A — Recommendations

### A1. Staff the afternoon / evening better
**Reason (`Hourly_Coverage`):**
- Avg active agents: **8.6** at 12:00–14:59, **4.7** at 15:00–20:59, **2.1** at 21:00–23:59.
- Load peaks ~16:00 (~19 inbound bursts per active agent-hour).
- Median reply at 21:00–23:59: **307–370 min**.
- Worst unanswered days: 23 Sep (24%), 24 Sep (20%) — ask the manager what happened (leave, big launch?).

**Action:** move 2–3 agents from the midday block into 15:00–21:00; an evening shift to 24:00 with at least 3 agents; a minimum-coverage-per-hour rule.
**Before acting:** confirm hours with the real roster (B11). Timezone is fine today (B4) but will shift by 1 hour when Egypt leaves summer time.

---

### A2. Ownership of unanswered messages via the shift roster (decided)
**Problem:** the analysis credits an unanswered message to "the last agent who wrote in the conversation". For 1,479 bursts in influencer-started chats nobody had written yet, so they have no owner at all.

**Solution:** join the **shift roster (task sheet)** to the messages: for each inbound burst, the owner is **the agent holding that WhatsApp line (`whatsappAccId`) at the time the message arrived**. This assigns an owner to:
- the **1,479** unanswered bursts in influencer-started chats,
- all **4,654** unanswered bursts (replaces the "last agent who wrote" rule),
- the **266** conversations never answered.

**Data needed:** roster with `agent`, `whatsappAccId` (or line phone/name), `shift_start`, `shift_end`, date (see C1).
**Note:** the counts above will change once the rules in Part D are applied (no closer-only exclusion, groups removed).

---

### A3. Capture "yes" as a structured event (decided)
**Problem:** "yes" is currently detected by guessing from the influencer's words (تمام، تم، اوكي ...). That is noisy.

**Target solution (proposal):** a **clickable button / poll** in the chat ("Yes, I confirm" / "No"). When the influencer taps Yes, the confirmation is recorded in the System automatically.

**Interim tracking (until the button exists):** detect confirmation from **messages sent by agents**, not from the influencer. When the team registers a confirmation, they send a confirmation message. We will keep a maintained list of these agent-side phrases, e.g. «تم التأكيد», «تم تأكيد حجزك», «تم تسجيلك», «تم» (when sent as a confirmation) — the owner/manager to finalise the list (C4).
- An agent message matching the list = **confirmed event**, credited to the agent holding the line at that time (Part D, rule D3).

### A3.1 Funnel / after-yes numbers — must be verified with examples first
The v1 numbers looked illogical, and the owner is right to doubt them. Answers to the questions raised:

| v1 number | What it actually measured | Why it can be misleading |
|-----------|---------------------------|--------------------------|
| 3,593 conversations with a "yes" → only 1,303 got address/brief afterwards | Whole month, conversation level. "Yes" = influencer reply containing an acceptance word. "Address/brief" = a **later** agent message classified as LOGISTICS by keywords (address, brief, maps link, code, ≥600 chars). | (1) many "yes" are not real confirmations (e.g. «تمام» = "noted"); (2) logistics may have been sent **before** the yes (inside the invitation) — not counted; (3) logistics sent from the phone app or with wording not in the keyword list — not counted; (4) logistics may come days later or via another channel. So 1,303 is a **floor**, not "we lose two thirds". |
| 19% (1,279) got no agent message within 24h after yes | Only the 24h window was checked. | We did **not** check whether a message came after 24h. Some or many of them probably did. Also, under rule D2 the agent must always reply, so a message within 24h should exist in every case — these 1,279 are worth reviewing. |
| 8,724 yeses, 6,874 attributable | The 1,850 difference = yeses where the turn before the yes was **sent from the phone app** (`original whatsapp`, no agent name) **plus** yeses in the last 3 hours of data (too recent to judge). | Phone-app part is solved by A4 (platform-only sending) or by getting the phone-app login logs per account (C3). |

**Action (C5):** I will produce an example sheet: 30 random conversations from each bucket ("yes + logistics", "yes + no logistics", "yes + no follow-up in 24h") with phone (masked in shared copies), time, agent, and the message sequence, plus a column "agent message after 24h? when?". The owner reviews them by eye, then we fix the definitions and recompute.

---

### A4. Platform-only sending (decided)
**Reason:** 23,657 outgoing messages (~25%) are `userName = 'original whatsapp'` → sent from the phone app, no agent name. This hides who answered, who followed up, and who got the yes (A3.1).
**Data check done (7 Oct):** these messages are spread across **29 different `whatsappAccId` accounts**, not one. Top account (226) = 15%, top 3 = 31%. So it is **not** only the UAE number (see B3).
**Action:** either (a) all sending from the platform only, or (b) request the phone-app session logs (who was logged in on which account and when) to attribute these messages (C3).

---

### A5. Invitation wording (unchanged — `Message_Features`, brand-adjusted)
| Do | Reason |
|----|--------|
| End the pitch with a question | reply 60% vs 36% |
| Avoid "limited time / hurry" wording | reply 30%, accept 9.5% vs 41% / 14% |
| Personalise instead of copy-paste templates | template 34% / 11.7% vs personal 46% / 15.3% |
| In chat: short closed questions | reply 79% vs 57% |
| Propose a specific day/time | accept 19.6% vs 12.6% |
| "Send تم": use carefully | raises accept (17.1% vs 11.3%) but lowers reply; may inflate "yes" (B2) |

Correlation, not causation → run as a 2-week **A/B test** on two campaigns, measured with real confirmations (Dropbox/System).

### A6. Ready replies for frequent questions (unchanged)
Most common influencer topics: date/time (6,286 messages), branch/location (3,078), content requirements (2,847), payment (2,724).
**Action:** one "campaign card" per campaign: available dates, branches + location links, content requirements, payment policy. Agents reply from it.

### A7. Persuasion coaching (unchanged)
- Above expected: Nour Zein (1.22x), Khaled Mohamed (1.31x), Mohamed abdelhamied (1.18x); Shawq Al-Ulayani 1.70x on only 229 turns.
- Below expected: Youssef Mohammed Elsayed (0.60x), Hoda Ahmed (0.60x), Nada Seliman (0.71x), Esraa Ahmed (0.79x).

Use for coaching only. **Do not use for evaluation** until B2 and B6 are closed and credit is re-assigned by the line-holder rule (D3) — rankings may change significantly.

### A8. Kuwait (unchanged)
Reply 29% vs KSA 49%; accept 7.8% vs 13.7%. Review wording/dialect and campaign mix offered in Kuwait. Country definition is confirmed (B9).

---

## Part B — Points to understand

### B1. Phones that are 18 digits starting with `120` — OPEN (explanation for asking)
**What we see (data check 7 Oct):** 5,728 rows, **53 distinct values**, all starting with `120363`.
**What it most likely is:** WhatsApp internally identifies every chat by an ID ("JID"):
- a person: `<country code><number>@s.whatsapp.net`, e.g. `9665XXXXXXXX@s.whatsapp.net`
- a **group**: `120363XXXXXXXXXXXX@g.us` — an 18-digit number starting with `120363`.

The platform probably stores the part before `@` in `Contact.phone`, so group chats appear as "phones" starting with `120363`. No real phone number in KSA/KW/UAE/EGY starts with `120`.
**Questions to ask the developers:**
1. Does `Contact.phone` store the WhatsApp JID without the suffix? Is there a column that marks groups (e.g. `isGroup`, or the full JID with `@g.us`)?
2. Are these team/internal groups or influencer groups?

**Impact if they are groups:** exclude them; unanswered counts and reply times will improve slightly (~3.5% of rows).

### B2. "Yes" detection — DECIDED (see A3)
Move from influencer keywords to **agent-sent confirmation phrases** now, and to a clickable button later. Open item: the final phrase list (C4).

### B3. `userName = 'original whatsapp'` — PARTLY CLOSED, new finding
**Owner's info:** one UAE line is used for personal-ish messages and is probably the only special case → ask about it or exclude it (C2).
**Data check:** phone-app messages exist on **29 accounts** (top: 226, 319, 303, 282, 244). So excluding the UAE line alone will not remove the gap. Also note the label `original whatsapp` appears on inbound rows too; it only means "not sent from the platform" when `isFromMe = 1`.
**Action:** identify the UAE line's `whatsappAccId` (can be checked from the `Whatsapp` table: `id`, `name`, `phone`) and exclude it; for the remaining 28 accounts apply A4.

### B4. Timezone — CLOSED for now, with one caveat
**Owner's info:** Dropbox sheets use Saudi time; the database uses Egypt time; today they are identical.
**What UTC means (simple):** UTC is the world "reference clock" (London time in winter). Every country is UTC plus/minus some hours:
- Saudi Arabia = **UTC+3 all year**.
- Egypt = **UTC+3 in summer** (daylight saving, ~late April to late October) and **UTC+2 in winter**.

So right now Egypt = Saudi time. **After Egypt ends summer time (last Thursday of October)**, database times will be **1 hour behind** Saudi time. Example: a message at 21:00 Riyadh time will show 20:00 in the database.
**Action:** store all timestamps converted to Saudi time (`Asia/Riyadh`) in the ETL so the roster join (A2), shifts (A1) and Dropbox dates stay aligned all year (C6). Also confirm with developers that `createdAt` is really stored as Egypt local time and not UTC (if it were UTC, today's numbers would be 3 hours off — the owner's observation suggests it is not).

### B5. Who sends the last message — DECIDED (rule D2)
Agents must always send the last message; even "thanks" needs a reply («العفو»). The v1 exclusion of "closer-only" messages (thanks/ok/👍) from unanswered is **removed**. Unanswered counts will rise.

### B6. Message kind / `isInvitation` — CLARIFIED
**Owner's info:** the raw export has no kind/feature columns; `isInvitation` is the only flag and is not reliable (agents forget to set it).
**Explanation:** `kind` (PITCH, REMINDER, LOGISTICS, CONFIRM, POST_VISIT, CHAT), "template", "ends with question", etc. are **not database columns**. They were **computed by the analysis code** from the message text. `isInvitation` is used as a hint only.
**Still open:** the PITCH wording rules were broadened and not re-validated. Validate by manually labelling ~200 random agent messages (C7). Affects A5 and A7.

### B7. Campaign / brand attribution — CLOSED (approach agreed)
**Agreed approach:** no direct WhatsApp DB ↔ `campaign_influencers` join. Campaign is inferred by combining:
1. brand mentioned in the chat (keywords),
2. message date → which campaign of that brand was active then,
3. Dropbox confirmation sheet (username/date),
4. System campaign data.

This also detects confirmations taken in chat but not logged in Dropbox/System (a logging-gap metric). Unknown/ambiguous cases are flagged, not guessed.

### B8. Removed.

### B9. Country — CLOSED
Phone prefix and `influencers.country_id` are the same thing for our purpose (country of residence), and influencers are added to a campaign only if they are in its country. No action.

### B10. Responsibility and influencer reply window — DECIDED (rules D1, D3, D4)
- There is no deadline for the influencer to reply; a reply after 24h is normal.
- Whoever **holds the line when the influencer replies** owns that reply and any yes in it — not the agent who sent the invitation — because that agent must log it in Dropbox and the System.

### B11. Shift roster — ACTION
Request the sheet showing who holds which line and when (C1). Required for A1, A2, D1, D3.

### B12. Dropbox vs System statuses — CHECKED, partly open
I read the code:
- `dropbox_vs_system_report.py` reads an **Excel exported from the System dashboard** (sheet "Campaigns", already aggregated with labels) and counts Dropbox `Statu 1` values (Pending, Confirmed, Visited, No Response, Block, Paid ads, Not Found, Traveling, Cancelled By Client, Cancelled By Community, No Match, Refused) and the columns `Inv.`, `Rem. 1`, `Rem. 2`, `Username`, `Notes`, `Send To Community` as **counts of filled cells**. It compares numbers per campaign; it does **not** map status codes itself.
- `reference/active_campaigns.sql` in the folder is **not** the campaign-level query described in the handoff. It is an influencer-activity query (last confirmation per influencer, `ci.status IN (2,7,8,11,13)` = visited/covered).

**Still open:** the full meaning of each `campaign_influencers.status` code (1–18) is not in any file. The handoff groups (confirmations 1,2,3,7,8,11,13; visited 2,7,8,11,13; missed 3,9; approved 15; reject 10,17,18) came from the original campaign query → please share that query or a status lookup table (C8).

### B13. Other small items
- `phone` = NULL (13,339 rows): **closed** — internal team chats; correctly excluded.
- Test accounts `trainee01`, `Developers Team`, `IT Team`: excluded. Confirm no other internal accounts exist (C9).
- `Real Target` column read by the script but not produced by the query → falls back to 0. Open.
- Campaign country guessed from campaign name in the original query → can mis-classify. Open (low priority).

---

## Part C — Action list

| # | Action | Owner | For |
|---|--------|-------|-----|
| C1 | Get the shift roster: agent, line (`whatsappAccId`/name/phone), date, start, end | Owner → Ops manager | A1, A2, D1, D3 |
| C2 | Identify the UAE personal-use line and decide: exclude | Owner | B3 |
| C3 | Ask for phone-app session logs per account, or enforce platform-only sending | Owner → Ops manager / developers | A4, A3.1 |
| C4 | Finalise the list of agent-sent confirmation phrases | Owner + Ops manager | A3, D3 |
| C5 | Produce the funnel/after-yes example sheet for manual review | Data (me) | A3.1 |
| C6 | Convert all timestamps to `Asia/Riyadh` in the ETL; confirm DB timezone with developers | Data + developers | B4 |
| C7 | Manually label ~200 agent messages to validate kind rules | Data + Owner | B6 |
| C8 | Share the campaign-level System query or a status code lookup | Owner | B12 |
| C9 | Confirm full list of internal/test accounts | Owner | B13 |
| C10 | Ask developers about group IDs (`120363...`) | Owner → developers | B1 |
| C11 | Propose the clickable Yes button / poll to product/developers | Owner | A3 |

---

## Part D — Metric rules changed by this review

| Rule | Old (v1) | New |
|------|----------|-----|
| D1 – Unanswered owner | Last agent who wrote in the conversation | Agent holding the line (roster) when the inbound message arrived |
| D2 – What needs a reply | Closer-only messages (thanks/ok/👍) excluded | **Every** inbound message needs a reply; agents send the last message |
| D3 – Credit for a yes / confirmation | Agent who sent the ask-turn | Agent holding the line when the influencer replied; confirmation detected from agent-sent phrases |
| D4 – Influencer reply window | Reply counted only within 24h | No limit for the influencer; agent reply time still measured from the inbound message |
| D5 – Exclusions | Groups not excluded | Exclude `120363...` IDs (after C10), the UAE personal line (C2), NULL phones, test accounts |
| D6 – Time | As exported | Converted to Saudi time |

After C1, C4 and C5 are done, all v1 numbers in Part A will be recomputed with these rules.
