# Database Extraction Guide & SQL Queries (1 September 2026 until Now)

> **Execution Strategy:**  
> All queries are unified to extract continuous, up-to-date data starting from **`2026-09-01 00:00:00` up to the current moment (Live Window)**.  
> This covers the entire month of September plus the latest days of October for a full live testing dataset.

---

## 📋 File Destination & Summary Table

| # | Query Description | Source Database | Save As (Exact Path) | Time Window |
|---|-------------------|-----------------|----------------------|-------------|
| **Q1** | **WhatsApp Messages Stream** | WhatsApp Pro DB | `data/last_month_s_data.csv` | `2026-09-01` ➔ Current Date |
| **Q2** | **Active Campaigns Summary** | System DB (`grandcp3_temp_production`) | `data/active_campaigns.csv` | Live Active Campaigns |
| **Q3** | **Campaign Influencer Bookings** | System DB (`grandcp3_temp_production`) | `data/campaign_influencers.csv` | `2026-09-01` ➔ Current Date |
| **Q4** | **Influencers Master Directory** | System DB (`grandcp3_temp_production`) | `data/influencers_master.csv` | All Active Profiles |

---

## 🗄️ SQL Queries to Execute

See [DATABASE_QUERIES_FOR_SAMPLES.sql](file:///c:/Users/DA-05/Downloads/Project/DATABASE_QUERIES_FOR_SAMPLES.sql) for the exact executable script.
