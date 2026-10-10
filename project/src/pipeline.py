import re
import pandas as pd
import numpy as np
from datetime import datetime, time
from typing import Dict, Tuple, List, Optional
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
    """Parses time strings like '2:59 PM', '11:26 AM', '14:30' into datetime.time."""
    if not t_str or str(t_str).strip() in ['', '-', 'nan', 'None']:
        return None
    t_clean = str(t_str).strip()
    for fmt in ('%I:%M %p', '%I:%M%p', '%H:%M:%S', '%H:%M'):
        try:
            return datetime.strptime(t_clean, fmt).time()
        except ValueError:
            pass
    return None


def prepare_roster_df(tasks_df: pd.DataFrame, lines_df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepares the Google Sheet tasks into an indexed lookup table for message attribution.
    """
    t_df = tasks_df.copy()
    
    # Normalize column names
    date_col = [c for c in t_df.columns if 'date' in c.lower() or c in ['65', ',mggggggg', 'col_0']][0]
    name_col = [c for c in t_df.columns if 'name' in c.lower()][0]
    shift_col = [c for c in t_df.columns if 'shift' in c.lower()][0]
    camp_col = [c for c in t_df.columns if 'campaign' in c.lower()][0]
    task_col = [c for c in t_df.columns if 'task' in c.lower()][0]
    start_col = [c for c in t_df.columns if 'start' in c.lower()][0]
    end_col = [c for c in t_df.columns if 'end' in c.lower()][0]
    
    records = []
    for _, r in t_df.iterrows():
        agent_name = str(r[name_col]).strip()
        task_name = str(r[task_col]).strip()
        line_desc = str(r[camp_col]).strip().lower()
        shift_name = str(r[shift_col]).strip().capitalize()
        raw_date = str(r[date_col]).strip()
        
        if not agent_name or agent_name == 'nan' or not raw_date or raw_date == 'nan':
            continue
            
        t_start = parse_time_str(r[start_col])
        t_end = parse_time_str(r[end_col])
        
        # Fallback to shift hours if time is missing
        if shift_name in SHIFT_HOURS:
            if not t_start:
                t_start = parse_time_str(SHIFT_HOURS[shift_name]["start"])
            if not t_end:
                t_end = parse_time_str(SHIFT_HOURS[shift_name]["end"])
        else:
            if not t_start:
                t_start = time(9, 0)
            if not t_end:
                t_end = time(17, 0)
                
        records.append({
            'raw_date': raw_date,
            'agent': agent_name,
            'shift': shift_name,
            'task': task_name,
            'line_desc': line_desc,
            'start_time': t_start,
            'end_time': t_end,
            'is_all_lines': 'all lines' in line_desc or 'all line' in line_desc,
            'is_live_response': 'live' in task_name.lower() or 'response' in task_name.lower()
        })
        
    return pd.DataFrame(records)


def run_conversation_analysis(messages_df: pd.DataFrame, roster_df: pd.DataFrame = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Runs the full conversation & burst analysis:
    - Identifies conversation threads (whatsappAccId + phone)
    - Groups into Inbound & Outbound Bursts
    - Applies Dynamic Unanswered rule (If influencer is the last sender in a chat, it is Unanswered)
    - Computes reply times in minutes
    """
    df = messages_df.copy().sort_values(['whatsappAccId', 'phone', 'createdAt'])
    
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
                    responder = m['userName'] if m['userName'] and m['userName'] != 'nan' else 'original whatsapp'
                    
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
