-- =============================================================================
-- FINAL FIXED DATABASE EXTRACTION QUERIES (SEPTEMBER 2026)
-- Fixes:
-- 1. Numeric c.status (1 = On going, 2 = Finished, 4 = Upcoming, 6 = On Hold)
-- 2. JSON country name parsing (co.name ->> '$.en' / '$.ar')
-- 3. Proper September 2026 date bounds (no 2022/2023 leaks)
-- 4. Target reach calculation per campaign_type
-- =============================================================================

-- =============================================================================
-- 1. WHATSAPP PRO DATABASE (MySQL - `Pro` DB)
-- Target: data/last_month_s_data.csv
-- =============================================================================

SELECT 
    c.phone, 
    m.content, 
    m.createdAt, 
    m.`type`, 
    m.isRead, 
    m.isFromMe, 
    m.isSystem,
    m.whatsappAccId, 
    m.userName, 
    m.isInvitation
FROM `Message` m
LEFT JOIN Room r    ON r.id = m.roomId
LEFT JOIN Contact c ON c.id = r.contactId
WHERE m.createdAt >= '2026-09-01 00:00:00'
  AND m.createdAt <= '2026-09-30 23:59:59'
  AND m.deletedAt IS NULL;


-- =============================================================================
-- 2. SYSTEM DB (`grandcp3_temp_production`)
-- Query A: Active Campaigns Summary Report (September 2026)
-- Target: data/active_campaigns.csv (or .xlsx)
-- =============================================================================

WITH ci_summary AS (
    SELECT
        campaign_id,
        COUNT(*) AS total_list,
        SUM(status IN (1,2,3,7,8,11,13)) AS Confirmations,
        SUM(status IN (2,7,8,11,13)) AS Visited,
        SUM(status IN (2,8)) AS Missing_Coverage,
        SUM(status IN (3,9)) AS missed_visit,
        SUM(status IN (7,11,13)) AS Coverage,
        SUM(status = 15) AS Approved,
        SUM(status IN (10,17,18)) AS Reject,
        SUM(request_for_approval = 'pending') AS request_for_approval
    FROM campaign_influencers
    WHERE deleted_at IS NULL
    GROUP BY campaign_id
)

SELECT
    c.id AS `campaign_id`,
    c.name AS `Campaign Name`,

    CASE c.status
        WHEN 1 THEN 'On going'
        WHEN 2 THEN 'Finished'
        WHEN 4 THEN 'Upcoming'
        WHEN 6 THEN 'On Hold'
        ELSE 'Unknown'
    END AS `status`,

    COALESCE(
        GROUP_CONCAT(DISTINCT 
            COALESCE(
                JSON_UNQUOTE(JSON_EXTRACT(co.name, '$.en')),
                JSON_UNQUOTE(JSON_EXTRACT(co.name, '$.ar')),
                co.name
            ) 
            SEPARATOR ', '
        ),
        CASE
            WHEN LOWER(c.name) REGEXP '(^|[^a-z])(ksa|k\\.s\\.a|saudi|saudi arabia)([^a-z]|$)' THEN 'Saudi Arabia'
            WHEN LOWER(c.name) REGEXP '(^|[^a-z])(uae|u\\.a\\.e|emirates|united arab emirates)([^a-z]|$)' THEN 'United Arab Emirates'
            WHEN LOWER(c.name) REGEXP '(^|[^a-z])(egypt|egy|e\\.g)([^a-z]|$)' THEN 'Egypt'
            WHEN LOWER(c.name) REGEXP '(^|[^a-z])(qatar|qa|qtr)([^a-z]|$)' THEN 'Qatar'
            WHEN LOWER(c.name) REGEXP '(^|[^a-z])(kuwait|kw)([^a-z]|$)' THEN 'Kuwait'
            WHEN LOWER(c.name) REGEXP '(^|[^a-z])(bahrain|bh)([^a-z]|$)' THEN 'Bahrain'
            WHEN LOWER(c.name) REGEXP '(^|[^a-z])(oman|om)([^a-z]|$)' THEN 'Oman'
            ELSE 'Unknown'
        END
    ) AS `Country`,

    CASE c.campaign_type
        WHEN 0 THEN 'Visit'
        WHEN 1 THEN 'Delivery'
        WHEN 2 THEN 'Mix'
        WHEN 3 THEN 'Share'
        WHEN 4 THEN 'Post Creation'
        ELSE 'Unknown'
    END AS `Type`,

    COALESCE(cs.total_list, 0) AS `Total List`,
    COALESCE(cs.Confirmations, 0) AS `Confirmations`,

    CASE c.campaign_type
        WHEN 0 THEN c.total_target_reach - IFNULL(c.extra_visit_target, 0)
        WHEN 1 THEN c.total_target_reach - IFNULL(c.extra_delivery_target, 0)
        WHEN 2 THEN c.total_target_reach - (IFNULL(c.extra_visit_target, 0) + IFNULL(c.extra_delivery_target, 0))
        WHEN 3 THEN c.total_target_reach - IFNULL(c.extra_delivery_target, 0)
        WHEN 4 THEN c.total_target_reach - IFNULL(c.extra_delivery_target, 0)
        ELSE c.total_target_reach
    END AS `Target`,

    COALESCE(cs.Visited, 0) AS `Visited`,
    COALESCE(cs.Coverage, 0) AS `Coverage`,
    COALESCE(cs.Missing_Coverage, 0) AS `Missing_coverage`,
    COALESCE(cs.missed_visit, 0) AS `missed_visit`,
    COALESCE(cs.Approved, 0) AS `Approved`,
    COALESCE(cs.Reject, 0) AS `Reject`,
    COALESCE(cs.request_for_approval, 0) AS `request_for_approval`,

    CASE
        WHEN c.campaign_type = 1 THEN c.deliver_start_date
        ELSE c.visit_start_date
    END AS `Start Date`,

    CASE
        WHEN c.campaign_type = 1 THEN c.deliver_end_date
        ELSE c.visit_end_date
    END AS `End Date`

FROM campaigns c

LEFT JOIN ci_summary cs
    ON cs.campaign_id = c.id

LEFT JOIN campaign_country_favourites ccf 
    ON ccf.campaign_id = c.id

LEFT JOIN campaign_country_favourites_v2 ccf2 
    ON ccf2.campaign_id = c.id

LEFT JOIN countries co 
    ON co.id = COALESCE(ccf2.country_id, ccf.country_id)

JOIN brands b
    ON b.id = c.brand_id

WHERE c.deleted_at IS NULL
  AND c.status IN (1, 2, 4, 6)
  AND b.parent_id NOT IN (3251, 2395)
  AND (
      -- Ongoing / Upcoming campaigns active in or around September 2026
      (
          c.status IN (1, 4)
          AND (
              CASE WHEN c.campaign_type = 1 THEN c.deliver_start_date ELSE c.visit_start_date END
          ) >= '2026-05-01'
          AND (
              CASE WHEN c.campaign_type = 1 THEN c.deliver_start_date ELSE c.visit_start_date END
          ) <= '2026-09-30'
      )
      OR
      -- Finished / On Hold campaigns that ended in September 2026
      (
          c.status IN (2, 6)
          AND (
              CASE WHEN c.campaign_type = 1 THEN c.deliver_end_date ELSE c.visit_end_date END
          ) BETWEEN '2026-08-25' AND '2026-09-30'
      )
  )

GROUP BY 
    c.id, c.name, c.status, c.campaign_type, 
    c.total_target_reach, c.extra_visit_target, c.extra_delivery_target,
    c.deliver_start_date, c.visit_start_date, c.deliver_end_date, c.visit_end_date,
    cs.total_list, cs.Confirmations, cs.Visited, cs.Coverage, cs.Missing_Coverage,
    cs.missed_visit, cs.Approved, cs.Reject, cs.request_for_approval

ORDER BY `Start Date` DESC, c.id DESC;


-- =============================================================================
-- 3. SYSTEM DB (`grandcp3_temp_production`)
-- Query B: Campaign Influencer Bookings & Outcomes (September 2026)
-- Target: data/campaign_influencers.csv
-- =============================================================================

SELECT 
    ci.id AS booking_id,
    ci.campaign_id,
    c.name AS campaign_name,
    COALESCE(
        GROUP_CONCAT(DISTINCT 
            COALESCE(
                JSON_UNQUOTE(JSON_EXTRACT(co.name, '$.en')),
                JSON_UNQUOTE(JSON_EXTRACT(co.name, '$.ar')),
                co.name
            ) 
            SEPARATOR ', '
        ),
        'Unknown'
    ) AS campaign_country,
    ci.influencer_id,
    i.name AS influencer_name,
    i.phone AS influencer_phone,
    i.whats_number AS influencer_whats_number,
    ci.status AS status_id,
    ci.created_at AS booking_created_at
FROM campaign_influencers ci
JOIN campaigns c ON c.id = ci.campaign_id
LEFT JOIN campaign_country_favourites ccf ON ccf.campaign_id = c.id
LEFT JOIN campaign_country_favourites_v2 ccf2 ON ccf2.campaign_id = c.id
LEFT JOIN countries co ON co.id = COALESCE(ccf2.country_id, ccf.country_id)
LEFT JOIN influencers i ON i.id = ci.influencer_id
WHERE ci.deleted_at IS NULL
  AND ci.created_at >= '2026-09-01 00:00:00'
  AND ci.created_at <= '2026-09-30 23:59:59'
GROUP BY ci.id, ci.campaign_id, c.name, ci.influencer_id, i.name, i.phone, i.whats_number, ci.status, ci.created_at
ORDER BY ci.id DESC;


-- =============================================================================
-- 4. SYSTEM DB (`grandcp3_temp_production`)
-- Query C: Influencers Master Profile (with Clean Country Name)
-- Target: data/influencers_master.csv
-- =============================================================================

SELECT 
    i.id AS influencer_id,
    i.name AS influencer_name,
    i.phone,
    i.whats_number,
    COALESCE(
        JSON_UNQUOTE(JSON_EXTRACT(co.name, '$.en')),
        JSON_UNQUOTE(JSON_EXTRACT(co.name, '$.ar')),
        co.name
    ) AS country_name,
    i.city_id,
    i.insta_uname,
    i.tiktok_uname,
    i.snapchat_uname
FROM influencers i
LEFT JOIN countries co ON co.id = i.country_id
WHERE i.deleted_at IS NULL
