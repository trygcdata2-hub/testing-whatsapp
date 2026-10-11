# Ops Manager Brief — What to Watch, What to Ask, What Blocks the System

> Period analysed: 4 Sep – 3 Oct 2026. All times (WhatsApp DB, System, Dropbox) are **Egypt time** → no conversion needed.
> Full background: `OPERATIONS_RECOMMENDATIONS.md`.

---

## 1. Numbers to keep an eye on

| Metric | Value | Why it matters |
|--------|-------|----------------|
| Median reply time (team) | 39 min; 34% within 15 min, 59% within 60 min | Baseline to improve |
| Unanswered inbound bursts | 4,654 (12%) | Baseline from initial run. In the new system: simple dynamic rule — if the influencer was the last sender and no agent replied, it is Unanswered (pure dynamic logic, no keyword exceptions) |
| ↳ of which in chats the influencer started and no agent had written yet | 1,479 (part of the 4,654) | No owner in initial run → assigned dynamically to line holder via roster |
| Conversations never answered (entire chat has 0 agent replies all month) | 266 | Completely dropped chats |
| Worst days | 23 Sep (24%), 24 Sep (20%) | Ask manager what happened |
| Agents active 12:00–14:59 / 15:00–20:59 / 21:00–23:59 | 8.6 / 4.7 / 2.1 | Evening understaffed |
| Median reply 21:00–23:59 | 307–370 min | Same |
| Peak load | ~16:00, ~19 bursts per agent-hour | Same |
| Messages sent outside the platform (`original whatsapp`) | 23,657 (~25% of outgoing) | Cannot be credited to an agent (see examples below) |
| Kuwait vs KSA reply / accept | 29% / 7.8% vs 49% / 13.7% | Kuwait needs a plan |
| Funnel & "after yes" (3,593 → 1,303; 19% no follow-up) | **Not reliable yet** | Keyword-based; verify with examples before using |

**📌 Examples: Messages sent outside the platform (AnyDesk/Phone) vs Platform**
When messages are sent from outside the platform (e.g. AnyDesk or phone app), the system logs the user as `original whatsapp`. We know the WhatsApp line (`whatsappAccId`), but the agent's name is lost.

*Sent from outside (User: `original whatsapp`):*
- **Line 226** (2026-09-29 12:38:27): `شكرا كتير لك`
- **Line 146** (2026-09-07 13:19:14): `فور التوافر بنرسلك`
- **Line 357** (2026-09-16 11:35:32): `يمكنك الاطلاع على العلامات التجارية المتاحة معنا:- https://try-gc.com`
- **Line 306** (2026-09-09 12:02:42): `و`
- **Line 226** (2026-09-18 13:38:46): `" بيوتي سيكرت | اطياف مول https://maps.app.goo...`
- **Line 226** (2026-09-29 11:42:38): `اي ساعه بتناسبك ؟`
- **Line 357** (2026-09-17 13:56:17): `ان شاء الله ارسل لنا عالرقم متل ما قلت لك والقسم المختص ف اقرب وقت بيرسلك التفاصيل وحبيت خبرك...`
- **Line 307** (2026-09-21 06:58:10): `تمام بس كيف طريقتها بالتاسك مانجر ؟`
- **Line 226** (2026-09-05 08:48:53): `هلا في انتظار اسال فيديو حق كافي لعتمادها من الاداره`
- **Line 226** (2026-09-09 19:30:54): `نحن فقط حابين نوضحلك ان دعواتنا بتكون ك تجربه شخصيه وبتكون مقابل تغطيه بسيطه باسلوبك الخاص وبيكون...`

*Sent from the Platform (User = Agent Name):*
- **Line 146 (Abdelhamid Mahrous)** (2026-09-10 11:01:24): `مساء الخير 🤍 حابة أتأكد منك، هل يناسبك نأكد موعدك مع سوسيتي لبكرة؟ ✨`
- **Line 127 (Nada Seliman)** (2026-09-30 12:53:47): `🐟✨ خلك أول من يجرب الجديد في شرمب زون! السيباس المشوي بنكهتين...`
- **Line 279 (Youssef Mohammed Elsayed)** (2026-09-29 18:43:12): `هلا 🤍 حبيت أذكّرك بدعوتك للبرانش في Society by Sofleur ✨ يسعدنا تأكيد حضورك...`
- **Line 226 (Nour Zein)** (2026-09-14 23:22:51): `🍋✨ A Little Treat | اكتشفوا Triowalite تجربة خاصة من @lemonhappyday...`
- **Line 146 (Asmaa Abdelhamid Ahmed)** (2026-09-28 07:28:32): `لا تفوت دعوتك الحصرية من Society by Sofleur 🤍 بانتظارك لتعيشي تجربة برانش مميزة واستثنائية! أرسل «تم»...`
- **Line 279 (Esraa Ahmed)** (2026-09-05 12:46:10): `اي ساعة ؟`
- **Line 146 (Mohamed Gamal)** (2026-09-06 21:34:30): `https://maps.app.goo.gl/8T8R9YTVWKo7GErd6`
- **Line 191 (Nada Seliman)** (2026-09-12 14:04:27): `https://www.instagram.com/g3w8 https://www.tiktok.com/@o.4n هذه مو حساباتك ؟`
- **Line 146 (Ahmed Rabea)** (2026-10-02 06:35:18): `اضا امكن تخبرني السبب ان شاء الله ما يكون صار شي زعلت منا `
- **Line 271 (Abdel Rahman Mohamed)** (2026-09-07 23:12:38): `code AQB302 `

---

## 2. What to ask / request from the Operations Manager

| # | Request | Why |
|---|---------|-----|
| M1 | **Shift roster** per day: agent, role (Inbox vs Outreach), WhatsApp line (name/phone), start, end | Owner of every inbound message = who held the line at that time + enables fair ranking per role |
| M2 | What happened on 23–24 Sep? | Highest unanswered days |
| M3 | Agree the rules (section 4) with the team | Fairness before using numbers for evaluation |
| M4 | List of phrases agents send when they confirm an influencer («تم التأكيد», «تم تسجيلك» ...) | Interim "yes" tracking from agent messages |
| M5 | Proposal: clickable Yes button / poll in chat that writes to the System | Removes keyword guessing |
| M6 | *(Merged into M1)* Agent role: Inbox vs Outreach | Covered directly inside the Shift Roster sheet |
| M7 | Any internal / test accounts besides `trainee01`, `Developers Team`, `IT Team` | Exclusion list |
| M8 | Evening staffing: move 2–3 agents to 15:00–21:00, min 3 agents until 24:00 | Section 1 numbers |
| M9 | Campaign card per campaign (dates, branches, content rules, payment) | Top questions: date/time 6,286, location 3,078, content 2,847, payment 2,724 |
| M10 | A/B test on wording for 2 weeks (end with a question, no urgency, personal not template, propose day/time) | Brand-adjusted lifts in v1 |

---

## 3. Things that can block the system if misunderstood now

| # | Topic | Current understanding | Decision / what to confirm |
|---|-------|----------------------|----------------------------|
| S1 | `whatsappAccId` | = **our WhatsApp line** (row in `Whatsapp` table), **not** an agent. 30 lines sent messages; 29 of them also have messages with `userName = 'original whatsapp'` (21 also used by named agents on the platform, 8 only outside it) | Keep. Roster (M1) must use the same line identifier |
| S2 | `original whatsapp` messages | Sent outside the platform (AnyDesk / phone). Mixed personal + campaign content | **Keep** in conversation metrics; **not credited** to any agent; with roster (M1) they can be credited to the line holder |
| S3 | Group IDs (`phone` 18 digits, `120363...`) | 5,728 rows, 53 chats — WhatsApp group format | **Exclude** (no real phone starts with 120). Confirm with developers only if unsure |
| S4 | `phone` NULL | Internal team chats | **Exclude** (closed) |
| S5 | Test accounts | `trainee01`, `Developers Team`, `IT Team` | **Exclude** + M7 |
| S6 | `isSystem = 1`, exact duplicates | System notices / 831 duplicates | **Exclude** |
| S7 | Responsibility | Inbound message → agent holding the line when it arrived (not the inviter) | Decided |
| S8 | Credit for a yes | Agent holding the line when the influencer replied | Decided |
| S9 | Influencer reply window | No limit | Decided |
| S10 | Last message / Unanswered logic | If the influencer sent the last message and no reply came, it is Unanswered (pure dynamic rule, no keyword exceptions) | Decided |
| S11 | "Yes" detection | From agent confirmation phrases (M4), later button (M5) | Need M4 list |
| S12 | Campaign attribution | Brand in chat + date + Dropbox confirmation sheet + System; **no** direct join to `campaign_influencers` | Decided |
| S13 | `isInvitation` | Unreliable (agents forget the flag); message kinds are computed from text, not DB columns | Validate ~200 labelled messages |
| S14 | Country | Phone prefix = `influencers.country_id` | Closed |
| S15 | Timezone | All sources Egypt time | Closed, no conversion |
| S16 | `active_campaigns.sql` vs comparison script | Correct campaign-level query, matches the script | Closed — 2 small gaps in section 5 |

---

## 4. Rules for the team (to agree with the manager)

1. **The Dynamic Unanswered Rule:** The agent must always be the last sender in the chat. If the influencer is the last one who sent a message, the system will dynamically count this chat as "Unanswered", regardless of what the conversation was about.
2. The line holder at the time of the message owns the reply and any confirmation in it, and logs it in Dropbox + System.
3. Send from the platform when possible (otherwise the message is credited to the line holder via roster, not by name).

---

## 5. Note on `active_campaigns.sql` (S16)

The file now holds the correct query: one row per active campaign, status groups (Confirmations 1,2,3,7,8,11,13 / Visited 2,7,8,11,13 / Coverage 7,11,13 / Missing coverage 2,8 / Missed 3,9 / Approved 15 / Reject 10,17,18), campaign filters (on going/upcoming started within 4 months; finished/on hold ended 1–5 days ago). It matches what the comparison script expects.

- `Real Target` is not stored in the System (comes from Dropbox) → removed from the script.
- Country from the campaign name is reliable: every campaign name contains its country.
