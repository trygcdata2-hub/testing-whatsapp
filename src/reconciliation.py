import os
import re
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

try:
    from .config import DATA_DIR
except ImportError:
    from config import DATA_DIR

CACHE_RECON_CAMPAIGNS = DATA_DIR / "cached_dropbox_recon_campaigns.parquet"
CACHE_RECON_INFLUENCERS = DATA_DIR / "cached_dropbox_recon_influencers.parquet"

DEFAULT_DROPBOX_FOLDERS = [
    r"C:\Users\DA-05\Dropbox\GC - operation live\Campaign Source\4- KSA\Grand Community\Active Campaigns",
    r"C:\Users\DA-05\Dropbox\GC - operation live\Campaign Source\4- KSA\ELITE\Active Campigns",
    r"C:\Users\DA-05\Dropbox\GC - operation live\Campaign Source\3- UAE\Grand Community\Active Campaigns",
    r"C:\Users\DA-05\Dropbox\GC - operation live\Campaign Source\3- UAE\Elite\Active Campaigns",
    r"C:\Users\DA-05\Dropbox\GC - operation live\Campaign Source\2- KW\Grand Community\Active Campaigns",
    r"C:\Users\DA-05\Dropbox\GC - operation live\Campaign Source\2- KW\Elite\Active Campaigns",
    r"C:\Users\DA-05\Dropbox\GC - operation live\Campaign Source\1- EGY\Egypt Campigns\Active Campaigns",
]


def clean_phone_right8(val, length: int = 8) -> str:
    """
    Cleans phone number and extracts the rightmost `length` digits (default 8).
    Handles country codes (+966, 00966, 966, +965, +20, etc.), leading zeros, spaces, quotes.
    """
    if pd.isna(val) or val is None:
        return ""
    digits = re.sub(r"\D", "", str(val))
    if len(digits) < length:
        return digits
    return digits[-length:]


def clean_uname(val) -> str:
    """Cleans Instagram/TikTok handles by stripping spaces, @, and lowering."""
    if pd.isna(val) or val is None:
        return ""
    s = str(val).lower().strip().replace("@", "")
    return re.sub(r"\s+", "", s)


def get_smart_key(name: str) -> str:
    """
    Generates a normalized alphanumeric smart key from campaign name.
    Ignores common boilerplate words and dates.
    """
    if pd.isna(name) or name is None:
        return ""
    s = str(name).lower().strip()
    stopwords = [
        'tiktok', 'snapchat', 'instagram', '2026', '2025', '2024',
        'ksa', 'kw', 'egy', 'uae', 'sep', 'oct', 'aug', 'apr', 'may', 'jun', 'jul',
        'visit', 'delivery', 'campaign', 'active', 'highest platform', 'approach'
    ]
    for w in stopwords:
        s = s.replace(w, '')
    words = re.findall(r"[a-z0-9]+", s)
    return "".join(sorted(words))


def scan_dropbox_campaign_files(folders: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Scans local Dropbox folders in STRICT READ-ONLY mode.
    Collects Excel files containing 'Comp.' sheets or 'List' sheets.
    """
    target_folders = folders or DEFAULT_DROPBOX_FOLDERS
    collected = []
    
    for folder in target_folders:
        if not os.path.exists(folder):
            continue
        for root, dirs, files in os.walk(folder):
            for f in files:
                low = f.lower()
                if not low.endswith((".xlsx", ".xlsm")) or f.startswith("~$") or "conflicted copy" in low:
                    continue
                if "cam info" in low or "desktop.ini" in low:
                    continue
                    
                full_path = os.path.join(root, f)
                camp_folder_name = os.path.basename(root)
                is_list = "list" in low
                
                collected.append({
                    'camp_name': camp_folder_name,
                    'file_name': f,
                    'full_path': full_path,
                    'is_list': is_list,
                    'smart_key': get_smart_key(camp_folder_name)
                })
    return collected


def parse_dropbox_campaigns(files_list: List[Dict[str, Any]]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Parses COMP sheets and LIST sheets from scanned Dropbox files.
    Returns:
    - comp_summary_df: Aggregated stats per campaign (Confirmations, Visited, Coverage, etc.)
    - dropbox_influencers_df: Individual influencer records extracted from Dropbox (username, phone, status, campaign).
    """
    summary_rows = []
    influencer_records = []
    
    comp_files = [f for f in files_list if not f['is_list']]
    list_files = [f for f in files_list if f['is_list']]
    
    # 1. Parse COMP Sheets
    for item in comp_files:
        path = item['full_path']
        camp_name = item['camp_name']
        sk = item['smart_key']
        is_delivery = 'delivery' in camp_name.lower() or 'delivery' in item['file_name'].lower()
        
        try:
            xls = pd.ExcelFile(path)
            comp_sheet = next((s for s in xls.sheet_names if 'comp' in str(s).lower()), None)
            if not comp_sheet:
                continue
                
            header_row = 0
            for r in range(5):
                temp = pd.read_excel(xls, sheet_name=comp_sheet, header=r, nrows=0)
                if any('username' in str(c).lower() for c in temp.columns):
                    header_row = r
                    break
                    
            df = pd.read_excel(xls, sheet_name=comp_sheet, header=header_row)
            df.columns = [str(c).strip() for c in df.columns]
            col_map = {c.lower(): c for c in df.columns}
            
            def find_col(keys):
                for k in col_map:
                    if any(key in k for key in keys):
                        return col_map[k]
                return None
                
            uname_col = find_col(['username', 'user name', 'ig username'])
            date_col = find_col(['date'])
            visit_col = find_col(['delivery', 'delivery status', 'visited status', 'visit status', 'visit'])
            cov_col = find_col(['overall cov', 'covstate', 'coverage', 'cov. state'])
            
            if not uname_col:
                continue
                
            df_valid = df[df[uname_col].notna()].copy()
            conf_count = len(df_valid)
            conf_with_date = len(df_valid[df_valid[date_col].notna()]) if date_col else 0
            
            visited_count = 0
            if visit_col:
                if is_delivery:
                    visited_count = int(df_valid[visit_col].apply(lambda v: str(v).strip().lower() == 'delivered' if pd.notna(v) else False).sum())
                else:
                    visited_count = int(df_valid[visit_col].notna().sum())
                    
            coverage_count = int(df_valid[cov_col].notna().sum()) if cov_col else 0
            
            summary_rows.append({
                'camp_name': camp_name,
                'smart_key': sk,
                'dropbox_type': 'Delivery' if is_delivery else 'Visit',
                'dropbox_confirmations': conf_count,
                'dropbox_conf_with_date': conf_with_date,
                'dropbox_visited': visited_count,
                'dropbox_coverage': coverage_count
            })
            
            for _, r in df_valid.iterrows():
                u_raw = str(r[uname_col]).strip()
                influencer_records.append({
                    'camp_name': camp_name,
                    'smart_key': sk,
                    'source': 'Dropbox_Comp',
                    'username': u_raw,
                    'username_clean': clean_uname(u_raw),
                    'phone_clean': '',
                    'visit_status': str(r.get(visit_col, '')) if visit_col else '',
                    'coverage_status': str(r.get(cov_col, '')) if cov_col else '',
                    'is_confirmed_dropbox': True
                })
        except Exception:
            continue
            
    # 2. Parse LIST Sheets (to get phones and statuses)
    for item in list_files:
        path = item['full_path']
        camp_name = item['camp_name']
        sk = item['smart_key']
        
        try:
            xls = pd.ExcelFile(path)
            list_sheets = [s for s in xls.sheet_names if 'list' in str(s).lower() and 'review' not in str(s).lower()]
            if not list_sheets:
                continue
                
            for s in list_sheets:
                df = pd.read_excel(xls, sheet_name=s, header=2)
                df.columns = [str(c).strip() for c in df.columns]
                
                uname_col = next((c for c in df.columns if 'username' in c.lower()), None)
                phone_col = next((c for c in df.columns if 'phone' in c.lower() or 'mobile' in c.lower() or 'whats' in c.lower()), None)
                status_col = next((c for c in df.columns if 'status' in c.lower() or 'statu' in c.lower()), None)
                
                if not uname_col and not phone_col:
                    continue
                    
                for _, r in df.iterrows():
                    u = clean_uname(r.get(uname_col, '')) if uname_col else ''
                    p = clean_phone_right8(r.get(phone_col, '')) if phone_col else ''
                    st_val = str(r.get(status_col, '')).strip() if status_col else ''
                    
                    if not u and not p:
                        continue
                        
                    influencer_records.append({
                        'camp_name': camp_name,
                        'smart_key': sk,
                        'source': 'Dropbox_List',
                        'username': str(r.get(uname_col, '')).strip() if uname_col else '',
                        'username_clean': u,
                        'phone_clean': p,
                        'visit_status': st_val,
                        'coverage_status': '',
                        'is_confirmed_dropbox': ('confirm' in st_val.lower() or 'visit' in st_val.lower())
                    })
        except Exception:
            continue

    summary_df = pd.DataFrame(summary_rows)
    inf_df = pd.DataFrame(influencer_records)
    
    return summary_df, inf_df


def build_system_lookups(ci_df: pd.DataFrame, inf_master: pd.DataFrame) -> Dict[str, Any]:
    """
    Builds optimized Dual-Column Phone Maps and Username Maps from System DB.
    Enforces XLOOKUP fallback logic (Primary Phone -> WhatsApp Number -> Usernames).
    """
    # 1. Phone Lookups in CI
    ci_p1 = {}
    ci_p2 = {}
    for _, r in ci_df.iterrows():
        p1 = clean_phone_right8(r.get('influencer_phone'))
        p2 = clean_phone_right8(r.get('influencer_whats_number'))
        cid = r['campaign_id']
        name = str(r['influencer_name'])
        status_id = r['status_id']
        cname = str(r['campaign_name'])
        csk = get_smart_key(cname)
        
        info = {
            'campaign_id': cid,
            'campaign_name': cname,
            'smart_key': csk,
            'influencer_name': name,
            'status_id': status_id,
            'is_confirmed_system': (status_id in [1, 2, 7, 8, 11, 13])
        }
        if p1:
            if p1 not in ci_p1:
                ci_p1[p1] = []
            ci_p1[p1].append(info)
        if p2:
            if p2 not in ci_p2:
                ci_p2[p2] = []
            ci_p2[p2].append(info)
            
    # 2. Master Profiles Map
    master_p1 = {}
    master_p2 = {}
    master_insta = {}
    master_tiktok = {}
    
    for _, r in inf_master.iterrows():
        p1 = clean_phone_right8(r.get('phone'))
        p2 = clean_phone_right8(r.get('whats_number'))
        u_insta = clean_uname(r.get('insta_uname'))
        u_tiktok = clean_uname(r.get('tiktok_uname'))
        
        m_info = {
            'influencer_id': r['influencer_id'],
            'influencer_name': str(r['influencer_name']),
            'phone_p1': p1,
            'phone_p2': p2,
            'insta_uname': u_insta,
            'tiktok_uname': u_tiktok
        }
        if p1: master_p1[p1] = m_info
        if p2: master_p2[p2] = m_info
        if u_insta: master_insta[u_insta] = m_info
        if u_tiktok: master_tiktok[u_tiktok] = m_info

    return {
        'ci_p1': ci_p1,
        'ci_p2': ci_p2,
        'master_p1': master_p1,
        'master_p2': master_p2,
        'master_insta': master_insta,
        'master_tiktok': master_tiktok
    }


def reconcile_campaigns_and_influencers(
    campaigns_df: pd.DataFrame,
    ci_df: pd.DataFrame,
    inf_master: pd.DataFrame,
    dropbox_summary_df: pd.DataFrame,
    dropbox_inf_df: pd.DataFrame
) -> Dict[str, Any]:
    """
    Executes the 3-Way Reconciliation between System Database and Dropbox Sheets.
    Computes:
    1. Campaign Level Comparison (Target, Sys Confirms, Drop Confirms, Discrepancies)
    2. Influencer Level Discrepancies (Dropbox Only vs System Only)
    """
    sys_camps = campaigns_df.copy()
    sys_camps['smart_key'] = sys_camps['Campaign Name'].apply(get_smart_key)
    
    # Merge at Campaign Level
    merged_camps = []
    
    if not dropbox_summary_df.empty:
        # Group dropbox by smart_key to handle multiple branch folders
        drop_grouped = dropbox_summary_df.groupby('smart_key', as_index=False).agg({
            'camp_name': 'first',
            'dropbox_confirmations': 'sum',
            'dropbox_conf_with_date': 'sum',
            'dropbox_visited': 'sum',
            'dropbox_coverage': 'sum'
        })
        
        camp_recon = pd.merge(
            sys_camps,
            drop_grouped,
            on='smart_key',
            how='inner'
        )
    else:
        camp_recon = pd.DataFrame()
        
    if not camp_recon.empty:
        camp_recon['Target'] = camp_recon['Target'].fillna(0).astype(int)
        camp_recon['Confirmations'] = camp_recon['Confirmations'].fillna(0).astype(int)
        camp_recon['Diff_Confirmations'] = camp_recon['dropbox_confirmations'] - camp_recon['Confirmations']
        
        def assign_status(row):
            d = row['Diff_Confirmations']
            if d == 0:
                return 'Aligned'
            elif d > 0:
                return f'Dropbox Ahead (+{d} in Dropbox)'
            else:
                return f'System Ahead (+{abs(d)} in System)'
                
        camp_recon['Reconciliation_Status'] = camp_recon.apply(assign_status, axis=1)
    
    # Build Lookups
    lookups = build_system_lookups(ci_df, inf_master)
    
    # Identify Influencer Discrepancies
    # Case 1: In Dropbox Comp sheet but not confirmed in System DB
    dropbox_only = []
    if not dropbox_inf_df.empty:
        comp_records = dropbox_inf_df[dropbox_inf_df['source'] == 'Dropbox_Comp']
        for _, r in comp_records.iterrows():
            u = r['username_clean']
            sk = r['smart_key']
            
            # Lookup influencer in Master by username
            matched_master = lookups['master_insta'].get(u) or lookups['master_tiktok'].get(u)
            
            is_confirmed_in_sys = False
            sys_camp_name = ''
            
            if matched_master:
                # Check CI by phone
                p1 = matched_master['phone_p1']
                p2 = matched_master['phone_p2']
                ci_records = lookups['ci_p1'].get(p1, []) + lookups['ci_p2'].get(p2, [])
                for cir in ci_records:
                    if cir['smart_key'] == sk and cir['is_confirmed_system']:
                        is_confirmed_in_sys = True
                        sys_camp_name = cir['campaign_name']
                        break
                        
            if not is_confirmed_in_sys:
                dropbox_only.append({
                    'Campaign Name': r['camp_name'],
                    'Dropbox Username': r['username'],
                    'Influencer Name (DB)': matched_master['influencer_name'] if matched_master else 'Not Found in Master',
                    'Phone Clean': (matched_master['phone_p1'] or matched_master['phone_p2']) if matched_master else 'N/A',
                    'Issue': 'Logged in Dropbox, Missing Confirmation (status=1) in System DB'
                })
                
    df_dropbox_only = pd.DataFrame(dropbox_only)
    
    return {
        'campaign_recon': camp_recon,
        'dropbox_only_influencers': df_dropbox_only,
        'scanned_folders_count': len(dropbox_summary_df) if not dropbox_summary_df.empty else 0,
        'total_comp_records': len(dropbox_inf_df) if not dropbox_inf_df.empty else 0
    }


def get_cached_or_run_reconciliation(
    campaigns_df: pd.DataFrame,
    ci_df: pd.DataFrame,
    inf_master: pd.DataFrame,
    force_rescan: bool = False
) -> Dict[str, Any]:
    """
    Retrieves reconciliation results. Uses fast Parquet caching to load instantly in UI.
    Rescans only if cache missing or force_rescan is True.
    """
    if not force_rescan and CACHE_RECON_CAMPAIGNS.exists() and CACHE_RECON_INFLUENCERS.exists():
        try:
            drop_summary = pd.read_parquet(CACHE_RECON_CAMPAIGNS)
            drop_infs = pd.read_parquet(CACHE_RECON_INFLUENCERS)
            return reconcile_campaigns_and_influencers(campaigns_df, ci_df, inf_master, drop_summary, drop_infs)
        except Exception:
            pass
            
    # Fresh scan
    files = scan_dropbox_campaign_files()
    drop_summary, drop_infs = parse_dropbox_campaigns(files)
    
    # Save cache
    if not drop_summary.empty:
        drop_summary.to_parquet(CACHE_RECON_CAMPAIGNS, index=False)
    if not drop_infs.empty:
        drop_infs.to_parquet(CACHE_RECON_INFLUENCERS, index=False)
        
    return reconcile_campaigns_and_influencers(campaigns_df, ci_df, inf_master, drop_summary, drop_infs)
