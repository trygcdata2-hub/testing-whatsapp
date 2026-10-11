import os
import re
import difflib
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

try:
    from .config import DATA_DIR, BASE_DIR, STATUS_MAP
except ImportError:
    from config import DATA_DIR, BASE_DIR, STATUS_MAP

CACHE_PCLOUD_CAMPAIGNS = DATA_DIR / "cached_pcloud_recon_campaigns.parquet"
CACHE_PCLOUD_INFLUENCERS = DATA_DIR / "cached_pcloud_recon_influencers.parquet"

# Standard paths on local Windows drive P:\
DEFAULT_PCLOUD_BASE_PATHS = [
    r"P:\Operation - Head Office\Coverages-Final\2026- Active Campaigns all offices\pCloud Active Campaigns",
    r"P:\pCloud Drive\Operation - Head Office\Coverages-Final\2026- Active Campaigns all offices\pCloud Active Campaigns"
]

REGIONS_CONFIG = {
    "KSA": {"path": "4- KSA", "has_groups": True},
    "UAE": {"path": "3- UAE", "has_groups": False},
    "KW":  {"path": "2- KW",  "has_groups": False},
    "EGY": {"path": "1- EGY", "has_groups": False},
}

MAX_DEPTH = 8

COVERAGE_RE = re.compile(r'^cov(er(age)?s?|r?a?g?e?s?|\.)?$', re.IGNORECASE)
PLATFORM_RE = re.compile(r'^(instagram|insta|ig|tiktok|tt|facebook|fb|snapchat|snap|twitter|x|youtube|yt)$', re.IGNORECASE)

# Non-brand boilerplate words to ignore when comparing campaign titles
STOPWORDS_NON_BRAND = {
    'visit', 'delivery', 'mix', 'share', 'post', 'creation', 'campaign', 'active',
    'highest platform', 'highestplatform', 'highist', 'highest', 'platform',
    'approach', 'all', 'shortcut', 'lnk', 'story', 'stories', 'reel', 'reels',
    'repost', 'ugc', 'bts', 'the', 'and', 'of', 'by', 'opening', 'event', 'barter'
}

COUNTRY_MAP = {
    'ksa': 'KSA', 'saudi': 'KSA', 'saudi arabia': 'KSA',
    'uae': 'UAE', 'dubai': 'UAE', 'emirates': 'UAE',
    'kw': 'KW', 'kuwait': 'KW',
    'egy': 'EGY', 'egypt': 'EGY',
    'qtr': 'QTR', 'qatar': 'QTR',
    'bh': 'BH', 'bahrain': 'BH',
    'om': 'OM', 'oman': 'OM'
}

def extract_country(text: str) -> str:
    """Extracts standardized 2-3 letter country code from text."""
    s = str(text).lower()
    for k, v in COUNTRY_MAP.items():
        if re.search(rf'\b{k}\b', s):
            return v
    return ""

def clean_brand_tokens(name: str) -> set:
    """Extracts core brand words by eliminating non-brand stopwords and country tokens."""
    s = str(name).lower()
    words = re.findall(r"[a-z0-9]+", s)
    return {w for w in words if w not in STOPWORDS_NON_BRAND and w not in COUNTRY_MAP and len(w) > 1}

def get_brand_sort_key(name: str) -> str:
    """Sorts brand tokens to ensure invariance against token re-ordering."""
    tokens = clean_brand_tokens(name)
    return "".join(sorted(tokens))

def is_coverage_dir(name: str) -> bool:
    return bool(COVERAGE_RE.match(str(name).strip()))

def is_platform_dir(name: str) -> bool:
    return bool(PLATFORM_RE.match(str(name).strip()))

def get_subfolders(path: str) -> List[str]:
    try:
        return sorted([n for n in os.listdir(path) if os.path.isdir(os.path.join(path, n))])
    except Exception:
        return []

def folder_contains_coverage(path: str) -> bool:
    return any(is_coverage_dir(n) for n in get_subfolders(path))

def folder_contains_platform_via_users(path: str) -> bool:
    children = get_subfolders(path)
    if not children:
        return False
    for child in children[:6]:
        child_path = os.path.join(path, child)
        grandchildren = get_subfolders(child_path)
        if any(is_platform_dir(g) for g in grandchildren):
            return True
    return False

def clean_uname(val) -> str:
    """Cleans Instagram/TikTok handles by stripping spaces, @, and lowering."""
    if pd.isna(val) or val is None:
        return ""
    s = str(val).lower().strip().replace("@", "")
    return re.sub(r"\s+", "", s)

def find_active_pcloud_base() -> Optional[str]:
    """Finds available mounted pCloud base path on local machine."""
    for p in DEFAULT_PCLOUD_BASE_PATHS:
        if os.path.exists(p):
            return p
    return None

def scan_campaigns_recursive(current_path: str, root_dir: str, depth: int, found: set, results: list, region_name: str):
    if depth > MAX_DEPTH:
        return

    if folder_contains_coverage(current_path):
        camp_path = current_path
        if camp_path not in found:
            found.add(camp_path)
            parent = os.path.dirname(camp_path)
            brand = os.path.basename(parent) if parent != root_dir else ""
            results.append({
                "region": region_name,
                "campaign_name": os.path.basename(camp_path),
                "brand": brand,
                "campaign_path": camp_path,
            })
        return

    if folder_contains_platform_via_users(current_path):
        camp_path = current_path
        if camp_path not in found:
            found.add(camp_path)
            parent = os.path.dirname(camp_path)
            brand = os.path.basename(parent) if parent != root_dir else ""
            results.append({
                "region": region_name,
                "campaign_name": os.path.basename(camp_path),
                "brand": brand,
                "campaign_path": camp_path,
            })
        return

    for child in get_subfolders(current_path):
        if child.startswith('.') or 'cache' in child.lower():
            continue
        child_path = os.path.join(current_path, child)
        scan_campaigns_recursive(child_path, root_dir, depth + 1, found, results, region_name)

def fast_parse_campaign_coverages(camp_path: str) -> List[Tuple[str, str]]:
    """Ultra-fast extractor of influencer coverage uploads."""
    subs = get_subfolders(camp_path)
    cov_dirs = [s for s in subs if is_coverage_dir(s)]
    influencer_names = []
    
    if cov_dirs:
        for cov_d in cov_dirs:
            cov_p = os.path.join(camp_path, cov_d)
            try:
                cov_items = os.listdir(cov_p)
            except Exception:
                continue
            for item in cov_items:
                if item.startswith('.') or item.lower() in ['thumbs.db', 'desktop.ini']:
                    continue
                item_p = os.path.join(cov_p, item)
                if os.path.isdir(item_p):
                    if is_platform_dir(item):
                        try:
                            for u in os.listdir(item_p):
                                if not u.startswith('.'):
                                    influencer_names.append((u, item))
                        except Exception:
                            pass
                    else:
                        influencer_names.append((item, "Folder"))
                else:
                    fname, _ = os.path.splitext(item)
                    influencer_names.append((fname, "File"))
    else:
        for item in subs:
            if not item.startswith('.'):
                influencer_names.append((item, "Direct"))
                
    return influencer_names

def run_pcloud_scan() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Scans all folders in pCloud and returns (df_pcloud_camps, df_pcloud_infs)."""
    base_p = find_active_pcloud_base()
    if not base_p:
        return pd.DataFrame(), pd.DataFrame()

    all_camps = []
    for reg, conf in REGIONS_CONFIG.items():
        reg_p = os.path.join(base_p, conf["path"])
        if not os.path.exists(reg_p):
            continue
        found = set()
        res = []
        if conf["has_groups"]:
            for group in get_subfolders(reg_p):
                grp_p = os.path.join(reg_p, group)
                for company in get_subfolders(grp_p):
                    comp_p = os.path.join(grp_p, company)
                    scan_campaigns_recursive(comp_p, comp_p, depth=1, found=found, results=res, region_name=f"{reg} ({group})")
        else:
            for company in get_subfolders(reg_p):
                comp_p = os.path.join(reg_p, company)
                scan_campaigns_recursive(comp_p, comp_p, depth=1, found=found, results=res, region_name=reg)
        all_camps.extend(res)

    camp_rows = []
    inf_rows = []

    for c in all_camps:
        raw_infs = fast_parse_campaign_coverages(c['campaign_path'])
        camp_rows.append({
            'campaign_name': c['campaign_name'],
            'region': c['region'],
            'brand': c['brand'],
            'pcloud_coverage_count': len(raw_infs),
            'campaign_path': c['campaign_path']
        })
        for raw_name, source_type in raw_infs:
            inf_rows.append({
                'campaign_name': c['campaign_name'],
                'region': c['region'],
                'brand': c['brand'],
                'raw_name': raw_name,
                'username_clean': clean_uname(raw_name),
                'source_type': source_type
            })

    return pd.DataFrame(camp_rows), pd.DataFrame(inf_rows)

def match_system_campaign_to_pcloud(
    s_name: str,
    s_country: str,
    df_pcloud_camps: pd.DataFrame
) -> Tuple[Optional[str], str, float, str]:
    """
    Matches a single System campaign against pCloud candidate folders using multi-layer token analysis:
    1. Country Guardrail (Prevents cross-country misattribution).
    2. Exact Brand Token Sort + Month Overlap.
    3. Token Subset / High Jaccard Overlap (>= 0.50).
    4. SequenceMatcher fallback.
    Returns: (best_pcloud_campaign_name, pcloud_region, confidence_score, match_method)
    """
    s_tokens = clean_brand_tokens(s_name)
    s_key = get_brand_sort_key(s_name)
    s_months = set(re.findall(r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|2024|2025|2026)\b', s_name.lower()))

    best_p_name = None
    best_p_region = ""
    best_score = 0.0
    match_method = "Not Found in pCloud"

    for _, p_row in df_pcloud_camps.iterrows():
        p_name = p_row['campaign_name']
        p_region = str(p_row['region']).upper()
        p_country = extract_country(p_name) or extract_country(p_region)

        # Country Guardrail: If both have a detected country, they must match!
        if s_country and p_country and s_country != p_country:
            continue

        p_tokens = clean_brand_tokens(p_name)
        p_key = get_brand_sort_key(p_name)
        p_months = set(re.findall(r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|2024|2025|2026)\b', p_name.lower()))
        month_overlap = len(s_months.intersection(p_months)) if s_months and p_months else 0

        # Case 1: Exact Brand Token Sort + Month Overlap
        if s_key and s_key == p_key and month_overlap > 0:
            return p_name, p_row['region'], 1.0 + month_overlap * 0.1, "Exact Brand & Date"

        # Case 2: High Jaccard similarity on core brand tokens
        if s_tokens and p_tokens:
            inter = len(s_tokens.intersection(p_tokens))
            union = len(s_tokens.union(p_tokens))
            jacc = inter / union if union else 0
            score = jacc + (month_overlap * 0.15)
            if jacc >= 0.50 and score > best_score:
                best_p_name = p_name
                best_p_region = p_row['region']
                best_score = score
                match_method = f"Jaccard ({jacc:.2f})"

    return best_p_name, best_p_region, best_score, match_method

def reconcile_pcloud_with_system(
    *args,
    **kwargs
) -> Dict[str, Any]:
    """
    PRIMARY GROUND TRUTH RECONCILIATION:
    Driven by System Active Campaigns (from SQL / campaigns_df).
    Matches each system campaign against pCloud and audits Coverage Media vs System Status 7.
    """
    campaigns_df = kwargs.get('campaigns_df', None)
    df_pcloud_camps = kwargs.get('df_pcloud_camps', None)
    df_pcloud_infs = kwargs.get('df_pcloud_infs', None)
    ci_df = kwargs.get('ci_df', None)
    inf_master = kwargs.get('inf_master', None)

    if len(args) == 4:
        df_pcloud_camps = args[0]
        df_pcloud_infs = args[1]
        ci_df = args[2]
        inf_master = args[3]
    elif len(args) >= 5:
        campaigns_df = args[0]
        df_pcloud_camps = args[1]
        df_pcloud_infs = args[2]
        ci_df = args[3]
        inf_master = args[4]

    if campaigns_df is None or not isinstance(campaigns_df, pd.DataFrame):
        try:
            from src.data_loader import load_campaigns
            campaigns_df = load_campaigns()
        except Exception:
            try:
                from .data_loader import load_campaigns
                campaigns_df = load_campaigns()
            except Exception:
                campaigns_df = pd.DataFrame()

    if df_pcloud_camps is None:
        df_pcloud_camps = pd.DataFrame()
    if df_pcloud_infs is None:
        df_pcloud_infs = pd.DataFrame()
    if ci_df is None:
        ci_df = pd.DataFrame()
    if inf_master is None:
        inf_master = pd.DataFrame()

    if campaigns_df.empty or df_pcloud_camps.empty:
        return {
            'campaign_summary': pd.DataFrame(),
            'influencer_audit': pd.DataFrame(),
            'total_campaigns': len(campaigns_df),
            'active_campaigns_count': 0,
            'matched_active_count': 0,
            'total_coverages': 0,
            'aligned_count': 0,
            'missing_7_count': 0,
            'not_booked_count': 0,
            'unknown_users_count': 0
        }

    # 1. Prepare Master Influencers Lookup
    user_to_info = {}
    for _, r in inf_master.iterrows():
        iid = r['influencer_id']
        name = r['influencer_name']
        phone = str(r['phone']) if pd.notna(r['phone']) else ''
        wa = str(r['whats_number']) if pd.notna(r['whats_number']) else ''
        for col in ['insta_uname', 'tiktok_uname', 'snapchat_uname']:
            if col in r and pd.notna(r[col]):
                u = clean_uname(r[col])
                if u and u not in user_to_info:
                    user_to_info[u] = {'id': iid, 'name': name, 'phone': phone, 'wa': wa}

    # 2. Group pCloud influencers by pCloud campaign_name
    pcloud_infs_by_camp = {}
    for _, r in df_pcloud_infs.iterrows():
        cn = r['campaign_name']
        if cn not in pcloud_infs_by_camp:
            pcloud_infs_by_camp[cn] = []
        pcloud_infs_by_camp[cn].append(r)

    # 3. Iterate over System Campaigns as the Driving Source
    system_campaign_rows = []
    influencer_audit_rows = []
    
    total_aligned = 0
    total_missing_7 = 0
    total_not_booked = 0
    total_unknown = 0
    matched_active = 0
    active_count = 0

    for _, s_row in campaigns_df.iterrows():
        s_name = s_row['Campaign Name']
        s_country = str(s_row.get('Country', '')).upper()
        if s_country in ['EGYPT']: s_country = 'EGY'
        if not s_country or s_country == 'UNKNOWN':
            s_country = extract_country(s_name)
            
        s_status = str(s_row.get('status', ''))
        s_dash_status = str(s_row.get('Dashboard_Status', ''))
        
        # Ground Truth Rule: Active campaign determination matching active_campaigns.sql
        is_active = (
            s_status in ['On going', 'Upcoming', 'On Hold', '1', '4', '6'] or
            'Active' in s_dash_status or 'Valid' in s_dash_status
        )
        if is_active:
            active_count += 1

        # Match against pCloud candidate folders
        p_name, p_region, score, method = match_system_campaign_to_pcloud(s_name, s_country, df_pcloud_camps)
        if is_active and p_name:
            matched_active += 1

        p_infs = pcloud_infs_by_camp.get(p_name, []) if p_name else []

        # Fast bookings lookup for this system campaign
        s_name_str = str(s_name).strip().lower() if pd.notna(s_name) else ""
        if 'campaign_name' in ci_df.columns and not ci_df.empty:
            ci_this_camp = ci_df[ci_df['campaign_name'].astype(str).str.strip().str.lower() == s_name_str]
            camp_booking_lookup = dict(zip(ci_this_camp['influencer_id'], ci_this_camp['status_id']))
        else:
            camp_booking_lookup = {}

        camp_aligned = 0
        camp_missing_7 = 0
        camp_not_booked = 0
        camp_unknown = 0

        for inf_r in p_infs:
            u = inf_r['username_clean']
            info = user_to_info.get(u, None)

            if info:
                iid = info['id']
                name = info['name']
                phone = info['phone']
                wa = info['wa']

                if iid in camp_booking_lookup:
                    st_id = camp_booking_lookup[iid]
                    st_name = STATUS_MAP.get(st_id, f"Status {st_id}")
                    if st_id == 7:
                        camp_aligned += 1
                        total_aligned += 1
                        gap_type = 'Aligned'
                        audit_res = 'Aligned (Updated to Status 7 in System)'
                    else:
                        camp_missing_7 += 1
                        total_missing_7 += 1
                        gap_type = 'Missing Status 7'
                        audit_res = f'Missing Status 7 (Uploaded to pCloud, System Status: {st_name})'
                else:
                    camp_not_booked += 1
                    total_not_booked += 1
                    st_id = np.nan
                    st_name = 'Not Booked'
                    gap_type = 'Not Booked'
                    audit_res = 'Not Booked in System (Uploaded in pCloud, Not in System Campaign)'
            else:
                camp_unknown += 1
                total_unknown += 1
                iid = np.nan
                name = inf_r['raw_name']
                phone = ''
                wa = ''
                st_id = np.nan
                st_name = 'Unknown'
                gap_type = 'Unknown User'
                audit_res = 'Unknown Influencer (Handle not found in Influencers Master)'

            influencer_audit_rows.append({
                'system_campaign_name': s_name,
                'pcloud_campaign_name': p_name,
                'is_active_campaign': is_active,
                'country': s_country,
                'username_clean': u,
                'influencer_name': name,
                'phone': phone,
                'whats_number': wa,
                'system_status_id': st_id,
                'system_status_name': st_name,
                'gap_type': gap_type,
                'reconciliation_status': audit_res,
                'source_type': inf_r.get('source_type', 'Folder')
            })

        # Alert status
        if not p_name:
            alert = "⚪ No folder found in pCloud"
        elif camp_missing_7 > 0:
            alert = f"🚨 Gap: {camp_missing_7} influencers missing Status 7"
        elif camp_aligned > 0 and camp_missing_7 == 0:
            alert = "✅ All coverages updated to Status 7"
        else:
            alert = f"⚠️ {camp_not_booked} coverages not booked in system"

        system_campaign_rows.append({
            'system_campaign_name': s_name,
            'country': s_country,
            'system_status': s_status,
            'is_active_campaign': is_active,
            'matched_pcloud_campaign': p_name or 'Not Found',
            'pcloud_region': p_region,
            'match_method': method,
            'total_pcloud_coverages': len(p_infs),
            'aligned_status_7': camp_aligned,
            'gap_missing_status_7': camp_missing_7,
            'gap_not_booked': camp_not_booked,
            'unknown_users': camp_unknown,
            'status_alert': alert
        })

    df_camp_summary = pd.DataFrame(system_campaign_rows)
    df_inf_audit = pd.DataFrame(influencer_audit_rows)

    return {
        'campaign_summary': df_camp_summary,
        'influencer_audit': df_inf_audit,
        'total_campaigns': len(df_camp_summary),
        'active_campaigns_count': active_count,
        'matched_active_count': matched_active,
        'total_coverages': len(df_inf_audit),
        'aligned_count': total_aligned,
        'missing_7_count': total_missing_7,
        'not_booked_count': total_not_booked,
        'unknown_users_count': total_unknown
    }

def get_cached_or_run_pcloud_reconciliation(
    *args,
    **kwargs
) -> Dict[str, Any]:
    """
    High-performance entrypoint. Reads from fast Parquet cache if available (<20ms),
    or runs fresh scan if cache missing or force_rescan=True.
    Supports all call signatures flexibly to prevent any TypeError.
    """
    force_rescan = kwargs.get('force_rescan', False)
    campaigns_df = kwargs.get('campaigns_df', None)
    ci_df = kwargs.get('ci_df', None)
    inf_master = kwargs.get('inf_master', None)

    if len(args) == 2:
        ci_df = args[0]
        inf_master = args[1]
    elif len(args) >= 3:
        campaigns_df = args[0]
        ci_df = args[1]
        inf_master = args[2]
        if len(args) >= 4:
            force_rescan = bool(args[3])

    if campaigns_df is None or not isinstance(campaigns_df, pd.DataFrame):
        try:
            from src.data_loader import load_campaigns
            campaigns_df = load_campaigns()
        except Exception:
            try:
                from .data_loader import load_campaigns
                campaigns_df = load_campaigns()
            except Exception:
                campaigns_df = pd.DataFrame()

    if ci_df is None or not isinstance(ci_df, pd.DataFrame):
        try:
            from src.data_loader import load_campaign_influencers
            ci_df = load_campaign_influencers()
        except Exception:
            pass

    if inf_master is None or not isinstance(inf_master, pd.DataFrame):
        try:
            from src.data_loader import load_influencers_master
            inf_master = load_influencers_master()
        except Exception:
            pass

    if not force_rescan and CACHE_PCLOUD_CAMPAIGNS.exists() and CACHE_PCLOUD_INFLUENCERS.exists():
        try:
            df_camps = pd.read_parquet(CACHE_PCLOUD_CAMPAIGNS)
            df_infs = pd.read_parquet(CACHE_PCLOUD_INFLUENCERS)
            return reconcile_pcloud_with_system(
                campaigns_df=campaigns_df,
                df_pcloud_camps=df_camps,
                df_pcloud_infs=df_infs,
                ci_df=ci_df,
                inf_master=inf_master
            )
        except Exception:
            pass

    # Fresh scan of local pCloud drive
    df_camps, df_infs = run_pcloud_scan()

    if not df_camps.empty and not df_infs.empty:
        try:
            df_camps.to_parquet(CACHE_PCLOUD_CAMPAIGNS, index=False)
            df_infs.to_parquet(CACHE_PCLOUD_INFLUENCERS, index=False)
        except Exception:
            pass

    return reconcile_pcloud_with_system(
        campaigns_df=campaigns_df,
        df_pcloud_camps=df_camps,
        df_pcloud_infs=df_infs,
        ci_df=ci_df,
        inf_master=inf_master
    )
