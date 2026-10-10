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
        SUM(request_for_approval = 'pending') AS request_for_approval,
        SUM(confirmation_date = CURDATE()) AS Today_Visits,
        SUM(confirmation_date = CURDATE() + INTERVAL 1 DAY) AS Tomorrow_Visits,
        SUM(confirmation_date = CURDATE() + INTERVAL 2 DAY) AS Day_After
    FROM campaign_influencers
    WHERE deleted_at IS NULL
    GROUP BY campaign_id
)

SELECT
    c.name AS `Campaign Name`,

    CASE c.status
        WHEN 1 THEN 'On going'
        WHEN 2 THEN 'Finished'
        WHEN 4 THEN 'Upcoming'
        WHEN 6 THEN 'On Hold'
        ELSE 'Unknown'
    END AS `status`,

    CASE
        WHEN LOWER(c.name) REGEXP '(^|[^a-z])(ksa|k\\.s\\.a|saudi|saudi arabia)([^a-z]|$)' THEN 'KSA'
        WHEN LOWER(c.name) REGEXP '(^|[^a-z])(uae|u\\.a\\.e|emirates|united arab emirates)([^a-z]|$)' THEN 'UAE'
        WHEN LOWER(c.name) REGEXP '(^|[^a-z])(egypt|egy|e\\.g)([^a-z]|$)' THEN 'Egypt'
        WHEN LOWER(c.name) REGEXP '(^|[^a-z])(qatar|qa|qtr)([^a-z]|$)' THEN 'Qatar'
        WHEN LOWER(c.name) REGEXP '(^|[^a-z])(kuwait|kw)([^a-z]|$)' THEN 'Kuwait'
        WHEN LOWER(c.name) REGEXP '(^|[^a-z])(bahrain|bh)([^a-z]|$)' THEN 'Bahrain'
        WHEN LOWER(c.name) REGEXP '(^|[^a-z])(oman|om)([^a-z]|$)' THEN 'Oman'
        WHEN LOWER(c.name) REGEXP '(^|[^a-z])(jordan|jo)([^a-z]|$)' THEN 'Jordan'
        WHEN LOWER(c.name) REGEXP '(^|[^a-z])(morocco|ma)([^a-z]|$)' THEN 'Morocco'
        WHEN LOWER(c.name) REGEXP '(^|[^a-z])(algeria|dz)([^a-z]|$)' THEN 'Algeria'
        WHEN LOWER(c.name) REGEXP '(^|[^a-z])(tunisia|tn)([^a-z]|$)' THEN 'Tunisia'
        ELSE 'Unknown'
    END AS `Country`,

    CASE c.campaign_type
        WHEN 0 THEN 'Visit'
        WHEN 1 THEN 'Delivery'
        WHEN 2 THEN 'Mix'
        WHEN 3 THEN 'Share'
        WHEN 4 THEN 'Post Creation'
        ELSE 'Unknown'
    END AS `Type`,

    cs.total_list AS `Total List`,
    cs.Confirmations AS `Confirmations`,

    CASE c.campaign_type
        WHEN 0 THEN c.total_target_reach - IFNULL(c.extra_visit_target,0) -- visit
        WHEN 1 THEN c.total_target_reach - IFNULL(c.extra_delivery_target,0) -- delivery
        WHEN 2 THEN c.total_target_reach - (IFNULL(c.extra_visit_target,0) + IFNULL(c.extra_delivery_target,0)) -- mix
        WHEN 3 THEN c.total_target_reach - IFNULL(c.extra_delivery_target,0)  -- share
        WHEN 4 THEN c.total_target_reach - IFNULL(c.extra_delivery_target,0)  -- post creation
        ELSE c.total_target_reach
    END AS `Target`,

    cs.Visited AS `Visited`,
    cs.Coverage AS `Coverage`,
    cs.Missing_Coverage AS `Missing_coverage`,
    cs.missed_visit AS `missed_visit`,
    cs.Approved AS `Approved`,
    cs.Reject AS `Reject`,
    cs.request_for_approval,

    c.target_confirmation_collective_daily AS `Daily Target`,

    cs.Today_Visits AS `Today's Visits`,
    cs.Tomorrow_Visits AS `Tomorrow's Visits`,
    cs.Day_After AS `Day After`,

    CASE
        WHEN c.campaign_type = 1 THEN c.deliver_start_date
        ELSE c.visit_start_date
    END AS `Start Date`,

    CASE
        WHEN c.campaign_type = 1 THEN c.deliver_end_date
        ELSE c.visit_end_date
    END AS `End Date`

FROM ci_summary cs

JOIN campaigns c
    ON cs.campaign_id = c.id
    AND c.deleted_at IS NULL
    AND c.status IN (1,2,4,6)

JOIN brands b
    ON b.id = c.brand_id

LEFT JOIN brands p
    ON b.parent_id = p.id

WHERE b.parent_id NOT IN (3251,2395)

AND (
    (
        c.status IN (1,4)
        AND (
            CASE
                WHEN c.campaign_type = 1 THEN c.deliver_start_date
                ELSE c.visit_start_date
            END
        ) >= DATE_SUB(CURDATE(), INTERVAL 4 MONTH)
    )
    OR
    (
  
    c.status IN (2,6)
    AND (
        CASE
            WHEN c.campaign_type = 1 THEN c.deliver_end_date
            ELSE c.visit_end_date
        END
    ) BETWEEN DATE_SUB(CURDATE(), INTERVAL 5 DAY)
          AND DATE_SUB(CURDATE(), INTERVAL 1 DAY)
    )
)

ORDER BY `Campaign Name`;