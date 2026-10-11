import re
import pandas as pd
import numpy as np
from datetime import datetime, time
from typing import Dict, Tuple, List, Optional, Union, Any
from .config import SHIFT_HOURS, ACTIVE_INFLUENCER_STATUSES
from .data_loader import (
    load_raw_messages,
    load_whatsapp_lines,
    load_google_sheet_tasks,
    load_campaigns,
    load_campaign_influencers,
    load_influencers_master
)

TEST_ACCOUNTS = ['trainee01', 'Developers Team', 'IT Team']

def clean_messages_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans raw WhatsApp messages according to decided business rules:
    - Filters system messages (isSystem == '1')
    - Filters duplicates
    - Filters WhatsApp group IDs (18-digit IDs starting with '120...')
    - Filters test/admin accounts
    - Parses timestamps
    """
    d = df.copy()
    d = d.drop_duplicates()
    
    # Filter system messages
    if 'isSystem' in d.columns:
        d = d[d['isSystem'] != '1']
        
    # Filter test accounts
    if 'userName' in d.columns:
        d = d[~d['userName'].isin(TEST_ACCOUNTS)]
        
    # Filter group chats (18-digit phone numbers starting with '120')
    if 'phone' in d.columns:
        d = d[d['phone'].notna()]
        d = d[~d['phone'].str.startswith('120363')]
        d = d[d['phone'].str.len() <= 15]
        
    # Parse createdAt
    d['createdAt'] = pd.to_datetime(d['createdAt'], errors='coerce')
    d = d[d['createdAt'].notna()]
    
    d['whatsappAccId'] = d['whatsappAccId'].astype(str)
    d['isFromMe'] = d['isFromMe'].astype(str)
    
    return d.sort_values('createdAt')


def parse_time_str(t_str: str, default_t: str = "00:00") -> Optional[time]:
    """Parses time strings or full datetime strings into datetime.time."""
    if not t_str or str(t_str).strip() in ['', '-', 'nan', 'None']:
        return None
    s = str(t_str).strip()
    try:
        dt = pd.to_datetime(s)
        return dt.time()
    except Exception:
        pass
    for fmt in ('%I:%M %p', '%I:%M%p', '%H:%M:%S', '%H:%M'):
        try:
            return datetime.strptime(s, fmt).time()
        except ValueError:
            pass
    return None


def clean_tokens(s: str) -> set:
    """Extracts alphanumeric tokens for line matching."""
    if not s or pd.isna(s):
        return set()
    cleaned = re.sub(r'[^a-zA-Z0-9\u0600-\u06FF]+', ' ', str(s).lower()).strip()
    return set(cleaned.split())


def parse_roster_date(raw_date_str: str, default_year: int = 2026) -> Optional[datetime.date]:
    """Robust parser for varying date representations in Google Sheet task logs."""
    if not raw_date_str or str(raw_date_str).strip() in ['', 'nan', 'None']:
        return None
    s = str(raw_date_str).strip()
    try:
        dt = pd.to_datetime(s)
        return dt.date()
    except Exception:
        pass
    for fmt in ('%d %B', '%d %b', '%B %d', '%b %d', '%b-%d', '%B-%d', '%d-%b', '%d-%B'):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.replace(year=default_year).date()
        except ValueError:
            pass
    for fmt in ('%m/%d/%Y', '%Y-%m-%d', '%d/%m/%Y', '%m-%d', '%d-%m'):
        try:
            dt = datetime.strptime(s, fmt)
            if dt.year == 1900:
                dt = dt.replace(year=default_year)
            return dt.date()
        except ValueError:
            pass
    return None


def build_shift_interval(d: datetime.date, shift: str, t_start: Optional[time], t_end: Optional[time]) -> Tuple[datetime, datetime]:
    """
    Builds the active [start_dt, end_dt] window for a roster shift entry.
    Implements the ground truth fallback rule:
    If End Time is missing, assumes agent was active until the end of their shift.
    """
    shift_clean = str(shift).strip().capitalize()
    
    if shift_clean == 'Between':
        # Between Shift: 17:00 to 01:00 next day
        start_hour, start_min = (17, 0) if not t_start else (t_start.hour, t_start.minute)
        start_dt = datetime(d.year, d.month, d.day, start_hour, start_min)
        if not t_end:
            # Fallback to end of Between shift (01:00 next morning)
            end_dt = datetime(d.year, d.month, d.day, 1, 0) + pd.Timedelta(days=1)
        else:
            if t_end.hour < 12: # Crosses midnight into next morning
                end_dt = datetime(d.year, d.month, d.day, t_end.hour, t_end.minute) + pd.Timedelta(days=1)
            else:
                end_dt = datetime(d.year, d.month, d.day, t_end.hour, t_end.minute)
                
    elif shift_clean == 'Night':
        # Night Shift: 01:00 to 09:00 morning
        start_hour, start_min = (1, 0) if not t_start else (t_start.hour, t_start.minute)
        if start_hour >= 20: # Logged before midnight
            start_dt = datetime(d.year, d.month, d.day, start_hour, start_min) - pd.Timedelta(days=1)
        else:
            start_dt = datetime(d.year, d.month, d.day, start_hour, start_min)
        if not t_end:
            # Fallback to end of Night shift (09:00 morning)
            end_dt = datetime(d.year, d.month, d.day, 9, 0)
        else:
            if t_end.hour >= 20:
                end_dt = datetime(d.year, d.month, d.day, t_end.hour, t_end.minute) - pd.Timedelta(days=1)
            else:
                end_dt = datetime(d.year, d.month, d.day, t_end.hour, t_end.minute)
                
    else: # Morning Shift: 09:00 to 17:00
        start_hour, start_min = (9, 0) if not t_start else (t_start.hour, t_start.minute)
        start_dt = datetime(d.year, d.month, d.day, start_hour, start_min)
        if not t_end:
            # Fallback to end of Morning shift (17:00)
            end_dt = datetime(d.year, d.month, d.day, 17, 0)
        else:
            end_dt = datetime(d.year, d.month, d.day, t_end.hour, t_end.minute)
            if end_dt < start_dt:
                end_dt += pd.Timedelta(days=1)
                
    return start_dt, end_dt


def prepare_roster_df(tasks_df: pd.DataFrame, lines_df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepares the Google Sheet tasks into an indexed lookup table for message attribution.
    Maps line nicknames to whatsappAccId and pre-computes valid datetime intervals.
    """
    if tasks_df is None or tasks_df.empty:
        return pd.DataFrame()
        
    lines = lines_df.copy()
    lines['whatsappAccId'] = lines['whatsappAccId'].astype(str)
    
    line_profiles = []
    for _, r in lines.iterrows():
        acc_id = str(r['whatsappAccId'])
        name = str(r['line_name'])
        tokens = clean_tokens(name)
        core_tokens = {t for t in tokens if t not in ['line', 'number', 'no', 'campagin', 'campaign']}
        line_profiles.append({
            'acc_id': acc_id,
            'name': name,
            'raw_name_lower': name.lower(),
            'tokens': tokens,
            'core_tokens': core_tokens
        })

    def match_acc_ids(desc: str) -> List[str]:
        desc_lower = str(desc).lower().strip()
        if 'all lines' in desc_lower or 'all line' in desc_lower:
            return ['__ALL__']
        desc_tokens = clean_tokens(desc_lower)
        desc_core = {t for t in desc_tokens if t not in ['line', 'number', 'no', 'campagin', 'campaign']}
        matches = []
        for lp in line_profiles:
            if lp['raw_name_lower'] in desc_lower:
                matches.append(lp['acc_id'])
            elif lp['core_tokens'] and lp['core_tokens'].issubset(desc_core):
                matches.append(lp['acc_id'])
            elif len(lp['core_tokens']) == 1 and list(lp['core_tokens'])[0] in desc_lower:
                matches.append(lp['acc_id'])
        return matches

    t_df = tasks_df.copy()
    date_cols = [c for c in t_df.columns if 'date' in c.lower() or c in ['65', ',mggggggg', 'col_0']]
    name_cols = [c for c in t_df.columns if 'name' in c.lower()]
    shift_cols = [c for c in t_df.columns if 'shift' in c.lower()]
    camp_cols = [c for c in t_df.columns if 'campaign' in c.lower()]
    task_cols = [c for c in t_df.columns if 'task' in c.lower()]
    start_cols = [c for c in t_df.columns if 'start' in c.lower()]
    end_cols = [c for c in t_df.columns if 'end' in c.lower()]
    
    if not (date_cols and name_cols and shift_cols and task_cols):
        return pd.DataFrame()
        
    date_col = date_cols[0]
    name_col = name_cols[0]
    shift_col = shift_cols[0]
    camp_col = camp_cols[0] if camp_cols else name_col
    task_col = task_cols[0]
    start_col = start_cols[0] if start_cols else None
    end_col = end_cols[0] if end_cols else None
    
    records = []
    for _, r in t_df.iterrows():
        agent = str(r[name_col]).strip()
        task = str(r[task_col]).strip().lower()
        if not agent or agent in ['nan', 'None', '']:
            continue
            
        # Filter for live response shifts
        if 'live' not in task and 'response' not in task and 'sr.whatsapp' not in task:
            continue
            
        raw_d = None
        for dc in date_cols:
            val = r.get(dc)
            if pd.notna(val) and str(val).strip() not in ['', 'nan', 'None']:
                raw_d = str(val).strip()
                break
                
        d = parse_roster_date(raw_d)
        if not d:
            continue
            
        shift = str(r[shift_col]).strip()
        t_start = parse_time_str(r[start_col]) if start_col else None
        t_end = parse_time_str(r[end_col]) if end_col else None
        
        start_dt, end_dt = build_shift_interval(d, shift, t_start, t_end)
        line_desc = str(r[camp_col]).strip()
        acc_ids = match_acc_ids(line_desc)
        is_all = ('__ALL__' in acc_ids) or ('all lines' in line_desc.lower())
        
        records.append({
            'agent': agent,
            'shift': shift,
            'start_dt': start_dt,
            'end_dt': end_dt,
            'acc_ids': acc_ids,
            'is_all_lines': is_all
        })
        
    return pd.DataFrame(records)


def attribute_responder(
    created_at: datetime,
    line_id: str,
    orig_user: str,
    roster_records: Union[List[dict], Dict[Any, List[dict]], None]
) -> str:
    """
    Attributes an outgoing message to the responsible agent based on the roster schedule.
    Ground Truth Rules:
    1. If message already has a valid agent username (not 'original whatsapp'), keep it.
    2. Fallback to end of shift if end time was blank.
    3. If two or more agents were logged on the same line at the same time:
       KEEP AS 'original whatsapp' to avoid unfair misattribution.
    4. If 1 agent was on this line: attribute to that agent.
    5. If no specific agent on line, but 1 agent had 'All Lines Numbers': attribute to that agent.
    6. If ambiguous or outside shift: keep as 'original whatsapp'.
    """
    if orig_user and str(orig_user).strip() not in ['original whatsapp', 'nan', 'None', '']:
        return str(orig_user).strip()
        
    if not roster_records:
        return 'original whatsapp'
        
    # Get candidate shifts covering this specific date
    if isinstance(roster_records, dict):
        cands_date = roster_records.get(created_at.date(), [])
    else:
        cands_date = roster_records

    if not cands_date:
        return 'original whatsapp'

    # Filter candidate shifts covering created_at
    cands = [r for r in cands_date if r['start_dt'] <= created_at <= r['end_dt']]
    if not cands:
        return 'original whatsapp'
        
    line_str = str(line_id)
    # Check specific line assignment
    line_matches = [r for r in cands if line_str in r['acc_ids']]
    agents_line = list(set([r['agent'] for r in line_matches]))
    
    if len(agents_line) == 1:
        return agents_line[0]
    elif len(agents_line) > 1:
        # OVERLAP / CONFLICT: Two or more agents registered on the same line simultaneously!
        # Rule: Keep as 'original whatsapp' rather than guessing or penalizing anyone.
        return 'original whatsapp'
        
    # Fallback to 'All Lines Numbers'
    all_matches = [r for r in cands if r['is_all_lines']]
    agents_all = list(set([r['agent'] for r in all_matches]))
    if len(agents_all) == 1:
        return agents_all[0]
        
    return 'original whatsapp'


def run_conversation_analysis(
    messages_df: pd.DataFrame,
    roster_df: Optional[pd.DataFrame] = None,
    lines_df: Optional[pd.DataFrame] = None
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Runs the full conversation & burst analysis:
    - Identifies conversation threads (whatsappAccId + phone)
    - Groups into Inbound & Outbound Bursts
    - Applies Dynamic Unanswered rule (If influencer is the last sender in a chat, it is Unanswered)
    - Applies Roster Schedule attribution for 'original whatsapp' messages
    - Computes reply times in minutes
    """
    df = messages_df.copy().sort_values(['whatsappAccId', 'phone', 'createdAt'])
    
    # Pre-index roster by date for instantaneous O(1) date lookups
    roster_by_date: Dict[Any, List[dict]] = {}
    if roster_df is not None and not roster_df.empty:
        for r in roster_df.to_dict('records'):
            sd = r['start_dt'].date()
            ed = r['end_dt'].date()
            if sd not in roster_by_date:
                roster_by_date[sd] = []
            roster_by_date[sd].append(r)
            if ed != sd:
                if ed not in roster_by_date:
                    roster_by_date[ed] = []
                roster_by_date[ed].append(r)
        
    conversations_list = []
    bursts_list = []
    
    grouped = df.groupby(['whatsappAccId', 'phone'])
    
    for (line_id, phone), group in grouped:
        msgs = group.to_dict('records')
        if not msgs:
            continue
            
        total_msgs = len(msgs)
        inbound_count = sum(1 for m in msgs if m['isFromMe'] == '0')
        outbound_count = sum(1 for m in msgs if m['isFromMe'] == '1')
        
        first_msg = msgs[0]
        last_msg = msgs[-1]
        
        # Dynamic Unanswered Rule: If the last message was sent by the influencer, the conversation is UNANSWERED.
        is_unanswered = (last_msg['isFromMe'] == '0')
        
        # Analyze reply times across message bursts
        burst_sender = None
        burst_start_time = None
        burst_msgs_count = 0
        
        for idx, m in enumerate(msgs):
            current_sender = m['isFromMe']
            
            if burst_sender is None:
                burst_sender = current_sender
                burst_start_time = m['createdAt']
                burst_msgs_count = 1
            elif current_sender == burst_sender:
                burst_msgs_count += 1
            else:
                # Burst ended, transition to other side
                if burst_sender == '0': # Inbound burst answered by an outbound message
                    reply_time_min = (m['createdAt'] - burst_start_time).total_seconds() / 60.0
                    
                    # Apply Roster Attribution engine
                    responder = attribute_responder(
                        created_at=m['createdAt'],
                        line_id=line_id,
                        orig_user=m['userName'],
                        roster_records=roster_by_date
                    )
                    
                    bursts_list.append({
                        'whatsappAccId': line_id,
                        'phone': phone,
                        'burst_start': burst_start_time,
                        'reply_time': m['createdAt'],
                        'reply_duration_min': max(0.1, round(reply_time_min, 1)),
                        'responder': responder,
                        'is_answered': True,
                        'within_15m': reply_time_min <= 15.0,
                        'within_60m': reply_time_min <= 60.0
                    })
                    
                burst_sender = current_sender
                burst_start_time = m['createdAt']
                burst_msgs_count = 1
                
        # If last burst was from influencer and never got answered
        if burst_sender == '0':
            bursts_list.append({
                'whatsappAccId': line_id,
                'phone': phone,
                'burst_start': burst_start_time,
                'reply_time': None,
                'reply_duration_min': None,
                'responder': None,
                'is_answered': False,
                'within_15m': False,
                'within_60m': False
            })
            
        conversations_list.append({
            'whatsappAccId': line_id,
            'phone': phone,
            'first_message_time': first_msg['createdAt'],
            'last_message_time': last_msg['createdAt'],
            'last_sender': 'Influencer' if last_msg['isFromMe'] == '0' else 'Company',
            'is_unanswered': is_unanswered,
            'total_messages': total_msgs,
            'inbound_messages': inbound_count,
            'outbound_messages': outbound_count
        })
        
    df_convs = pd.DataFrame(conversations_list)
    df_bursts = pd.DataFrame(bursts_list)
    
    return df_convs, df_bursts
