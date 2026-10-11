import os
import re
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

def get_smart_key(name: str) -> str:
    """Canonical alphanumeric token key neutralizing case, stopwords, dates, and whitespace."""
    if pd.isna(name) or name is None:
        return ""
    s = str(name).lower().strip()
    stopwords = [
        'tiktok', 'snapchat', 'instagram', '2026', '2025', '2024',
        'ksa', 'kw', 'egy', 'uae', 'sep', 'oct', 'aug', 'apr', 'may', 'jun', 'jul',
        'visit', 'delivery', 'campaign', 'active', 'highest platform', 'highestplatform', 'approach', 'all', 'shortcut'
    ]
    for w in stopwords:
        s = s.replace(w, '')
    words = re.findall(r"[a-z0-9]+", s)
    return "".join(sorted(words))

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
    """
    Ultra-fast extractor of influencer coverage uploads.
    Extracts raw_name and source_type.
    """
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
    """
    Full scan of pCloud directories across regions.
    Returns (df_campaigns, df_influencers).
    """
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
        sk = get_smart_key(c['campaign_name'])
        camp_rows.append({
            'campaign_name': c['campaign_name'],
            'region': c['region'],
            'brand': c['brand'],
            'smart_key': sk,
            'pcloud_coverage_count': len(raw_infs),
            'campaign_path': c['campaign_path']
        })
        for raw_name, source_type in raw_infs:
            inf_rows.append({
                'campaign_name': c['campaign_name'],
                'region': c['region'],
                'brand': c['brand'],
                'smart_key': sk,
                'raw_name': raw_name,
                'username_clean': clean_uname(raw_name),
                'source_type': source_type
            })

    return pd.DataFrame(camp_rows), pd.DataFrame(inf_rows)

def reconcile_pcloud_with_system(
    df_pcloud_camps: pd.DataFrame,
    df_pcloud_infs: pd.DataFrame,
    ci_df: pd.DataFrame,
    inf_master: pd.DataFrame
) -> Dict[str, Any]:
    """
    Reconciles pCloud coverage uploads with the System Database.
    Identifies influencers who uploaded coverage in pCloud but are NOT marked status=7 in system.
    """
    if df_pcloud_infs.empty:
        return {
            'campaign_summary': pd.DataFrame(),
            'influencer_audit': pd.DataFrame(),
            'total_coverages': 0,
            'aligned_count': 0,
            'missing_7_count': 0,
            'not_booked_count': 0,
            'unknown_users_count': 0
        }

    # Prepare DB lookups
    ci_work = ci_df.copy()
    if 'smart_key' not in ci_work.columns and 'campaign_name' in ci_work.columns:
        ci_work['smart_key'] = ci_work['campaign_name'].apply(get_smart_key)

    # 1. Influencer lookup by username
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

    # 2. Fast booking lookup: (smart_key, influencer_id) -> status_id
    booking_lookup = {}
    for _, r in ci_work.iterrows():
        k = (r['smart_key'], r['influencer_id'])
        if k not in booking_lookup:
            booking_lookup[k] = r['status_id']

    # 3. Match pCloud coverages
    recon_records = []
    aligned_count = 0
    missing_7_count = 0
    not_booked_count = 0
    unknown_users_count = 0

    for _, r in df_pcloud_infs.iterrows():
        u = r['username_clean']
        sk = r['smart_key']
        
        info = user_to_info.get(u, None)
        if info:
            iid = info['id']
            name = info['name']
            phone = info['phone']
            wa = info['wa']
            
            status_id = booking_lookup.get((sk, iid), None)
            if status_id is not None:
                status_name = STATUS_MAP.get(status_id, f"Status {status_id}")
                if status_id == 7:
                    aligned_count += 1
                    recon_status = 'Aligned (محدث بـ 7 بالسيستم)'
                    gap_type = 'Aligned'
                else:
                    missing_7_count += 1
                    recon_status = f'Missing Status 7 (مرفوع بـ pCloud وحالته بالسيستم: {status_name})'
                    gap_type = 'Missing Status 7'
            else:
                not_booked_count += 1
                status_id = np.nan
                status_name = "Not Booked"
                recon_status = 'Not Booked in System (مرفوع بـ pCloud وغير مسجل بالحملة بالسيستم)'
                gap_type = 'Not Booked'
        else:
            unknown_users_count += 1
            iid = np.nan
            name = r['raw_name']
            phone = ''
            wa = ''
            status_id = np.nan
            status_name = "Unknown User"
            recon_status = 'Unknown Influencer (يوزر غير مسجل بقاعدة البيانات)'
            gap_type = 'Unknown User'
            
        recon_records.append({
            'campaign_name': r['campaign_name'],
            'region': r['region'],
            'brand': r['brand'],
            'smart_key': sk,
            'username_clean': u,
            'raw_name': r['raw_name'],
            'influencer_id': iid,
            'influencer_name': name,
            'phone': phone,
            'whats_number': wa,
            'system_status_id': status_id,
            'system_status_name': status_name,
            'gap_type': gap_type,
            'reconciliation_status': recon_status,
            'source_type': r.get('source_type', 'Folder')
        })

    df_recon = pd.DataFrame(recon_records)

    # Campaign aggregation
    camp_agg = df_recon.groupby(['campaign_name', 'region', 'brand', 'smart_key']).agg(
        total_pcloud_coverages=('username_clean', 'count'),
        aligned_status_7=('gap_type', lambda x: (x == 'Aligned').sum()),
        gap_missing_status_7=('gap_type', lambda x: (x == 'Missing Status 7').sum()),
        gap_not_booked=('gap_type', lambda x: (x == 'Not Booked').sum()),
        unknown_users=('gap_type', lambda x: (x == 'Unknown User').sum())
    ).reset_index()

    camp_agg['total_gaps'] = camp_agg['gap_missing_status_7'] + camp_agg['gap_not_booked']

    def assign_camp_alert(row):
        if row['gap_missing_status_7'] > 0:
            return f"🚨 خلل: {row['gap_missing_status_7']} مؤثر لم يُسجل بـ 7"
        elif row['gap_not_booked'] > 0:
            return f"⚠️ {row['gap_not_booked']} تغطية غير مسجلة بالسيستم"
        elif row['aligned_status_7'] > 0:
            return "✅ جميع التغطيات محدثة بـ 7"
        else:
            return "ℹ️ يوزرات غير مسجلة بالسيستم"

    camp_agg['status_alert'] = camp_agg.apply(assign_camp_alert, axis=1)

    return {
        'campaign_summary': camp_agg,
        'influencer_audit': df_recon,
        'total_coverages': len(df_recon),
        'aligned_count': aligned_count,
        'missing_7_count': missing_7_count,
        'not_booked_count': not_booked_count,
        'unknown_users_count': unknown_users_count
    }

def get_cached_or_run_pcloud_reconciliation(
    ci_df: pd.DataFrame,
    inf_master: pd.DataFrame,
    force_rescan: bool = False
) -> Dict[str, Any]:
    """
    High-performance entrypoint. Reads from fast Parquet cache if available (<20ms),
    or runs fresh scan if cache missing or force_rescan=True.
    """
    if not force_rescan and CACHE_PCLOUD_CAMPAIGNS.exists() and CACHE_PCLOUD_INFLUENCERS.exists():
        try:
            df_camps = pd.read_parquet(CACHE_PCLOUD_CAMPAIGNS)
            df_infs = pd.read_parquet(CACHE_PCLOUD_INFLUENCERS)
            return reconcile_pcloud_with_system(df_camps, df_infs, ci_df, inf_master)
        except Exception:
            pass

    # Fresh scan
    df_camps, df_infs = run_pcloud_scan()

    if not df_camps.empty and not df_infs.empty:
        try:
            df_camps.to_parquet(CACHE_PCLOUD_CAMPAIGNS, index=False)
            df_infs.to_parquet(CACHE_PCLOUD_INFLUENCERS, index=False)
        except Exception:
            pass

    return reconcile_pcloud_with_system(df_camps, df_infs, ci_df, inf_master)
