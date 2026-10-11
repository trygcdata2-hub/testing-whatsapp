# Official Request: Read-Only Credentials for Live Operations Dashboard

**To:** Operations Management & IT / Engineering Team  
**From:** Data & Business Intelligence Team  
**Subject:** Request for Read-Only Access Credentials for Live WhatsApp & Campaign Tracking System  

---

### Executive Summary & Objective

To transition our operational reporting from manual static exports to an **Automated Live Real-Time Monitoring Dashboard (Streamlit)**, we require dedicated **Read-Only** access to our operational data sources.

This live tracking engine will provide management with:
1. **Real-time Live Response Tracking:** Instant alerts for unanswered influencer messages and response delays beyond agreed SLAs.
2. **Automated Team KPIs & Leaderboards:** Accurate evaluation of agent response times and chat conversion rates, dynamically linked to the daily shift roster.
3. **Automated Campaign Funnel Tracking:** Live reconciliation between WhatsApp confirmations, System bookings, and Dropbox logs without manual intervention.

---

## Required Access & Credentials Details

All requested access levels are **strictly READ-ONLY (`SELECT` permissions only)** to ensure absolute database security and zero risk to production systems.

```
+---------------------------------------------------------------------------------------------------+
| 1. WhatsApp Pro Database (MySQL / Read Replica)                                                  |
+---------------------------------------------------------------------------------------------------+
| Purpose: Live streaming of incoming messages, response times, and line attribution.             |
| Required Tables: `Message`, `Room`, `Contact`, `Whatsapp`                                         |
| Permissions Required: `SELECT` only (Read-Only)                                                   |
|                                                                                                   |
| Details Needed:                                                                                   |
|   - DB Host / IP: _________________________________________                                       |
|   - Port: __________________ (Default: 3306)                                                      |
|   - Database Name: _________________________________________                                      |
|   - Username: _____________________________________________                                       |
|   - Password: _____________________________________________                                       |
+---------------------------------------------------------------------------------------------------+

+---------------------------------------------------------------------------------------------------+
| 2. System / Operations Database (Core Platform DB)                                                |
+---------------------------------------------------------------------------------------------------+
| Purpose: Fetching daily active campaigns, confirmation statuses, attendance, and coverage.       |
| Permissions Required: `SELECT` only (Read-Only)                                                   |
|                                                                                                   |
| Details Needed:                                                                                   |
|   - DB Host / IP: _________________________________________                                       |
|   - Port: __________________                                                                      |
|   - Database Name: _________________________________________                                      |
|   - Username: _____________________________________________                                       |
|   - Password: _____________________________________________                                       |
+---------------------------------------------------------------------------------------------------+

+---------------------------------------------------------------------------------------------------+
| 3. Dropbox API Integration                                                                        |
+---------------------------------------------------------------------------------------------------+
| Purpose: Automated live reading of campaign confirmation sheets filled by operations team.        |
| Permissions Required: Read-only access to `/Campaigns` folder                                     |
|                                                                                                   |
| Details Needed (either option A or B):                                                            |
|   Option A (Dropbox Scoped App Token):                                                            |
|     - App Key: ____________________________________________                                       |
|     - App Secret: _________________________________________                                       |
|     - Refresh Token / Access Token: _______________________                                       |
|                                                                                                   |
|   Option B (Shared Folder Access / Webhook):                                                      |
|     - Service Email / Folder Share Link: __________________                                       |
+---------------------------------------------------------------------------------------------------+
```

---

## Security & Governance Safeguards

1. **Zero Write Operations:** User accounts will only have `GRANT SELECT` privileges. No `INSERT`, `UPDATE`, `DELETE`, or `DROP` permissions are required or requested.
2. **Read Replica Priority:** If a database read-replica exists, we prefer connecting to the replica to ensure zero load impact on primary production databases.
3. **Secure Secrets Storage:** Credentials will be stored exclusively in encrypted environment variables (`.env` ignored from version control) and will never be hardcoded.
4. **Data Privacy (PII Protection):** Sensitive customer data will be masked/hashed in reporting views.

---

### Approval & Sign-Off

- **Operations Manager Approval:** `[  ] Approved` `[  ] Pending`
- **Technical Lead / IT Sign-Off:** `[  ] Approved` `[  ] Pending`
- **Date:** ____ / ____ / 2026
