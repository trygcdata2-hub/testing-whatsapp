import pandas as pd
import numpy as np
from typing import Dict, Any
try:
    from .config import ACTIVE_INFLUENCER_STATUSES, STATUS_MAP
except (ImportError, ValueError):
    try:
        from src.config import ACTIVE_INFLUENCER_STATUSES, STATUS_MAP
    except (ImportError, ValueError):
        from config import ACTIVE_INFLUENCER_STATUSES, STATUS_MAP

def compute_agent_scorecards(df_bursts: pd.DataFrame, df_tasks: pd.DataFrame = None) -> pd.DataFrame:
    """
    Computes individual KPIs per agent:
    - Total Responses Handled
    - Median Reply Time (minutes)
    - % Answered < 15 min
    - % Answered < 60 min
    - Dynamic Unanswered Chats Assigned
    """
    answered = df_bursts[df_bursts['is_answered'] == True].copy()
    
    agent_stats = []
    for agent, group in answered.groupby('responder'):
        if not agent or agent == 'nan':
            continue
            
        total_replies = len(group)
        median_time = group['reply_duration_min'].median()
        p15 = (group['within_15m'].sum() / total_replies) * 100.0
        p60 = (group['within_60m'].sum() / total_replies) * 100.0
        
        agent_stats.append({
            'Agent': agent,
            'Total Responses': total_replies,
            'Median Reply Time (min)': round(median_time, 1),
            'Answered < 15m (%)': round(p15, 1),
            'Answered < 60m (%)': round(p60, 1)
        })
        
    df_agents = pd.DataFrame(agent_stats)
    if not df_agents.empty:
        df_agents = df_agents.sort_values('Total Responses', ascending=False)
    return df_agents


def compute_influencer_behavior(
    df_convs: pd.DataFrame,
    df_ci: pd.DataFrame,
    df_master: pd.DataFrame = None
) -> Dict[str, Any]:
    """
    Computes influencer behavior intelligence:
    - Active influencers count (status in 2, 7, 8, 11, 13)
    - Ghosting / Flakers (Confirmed status=1 or missed_visit status=3)
    - Status breakdown across campaigns
    """
    active_count = df_ci['is_active_influencer'].sum() if 'is_active_influencer' in df_ci.columns else 0
    total_bookings = len(df_ci)
    
    status_counts = df_ci['status_id'].value_counts().to_dict()
    status_summary = []
    for s_id, count in status_counts.items():
        try:
            name = STATUS_MAP.get(int(float(s_id)), f"Status {s_id}")
        except (ValueError, TypeError):
            name = f"Status {s_id}"
        status_summary.append({
            'Status ID': s_id,
            'Status Meaning': name,
            'Count': count,
            'Share (%)': round((count / total_bookings) * 100.0, 1)
        })
        
    df_status_summary = pd.DataFrame(status_summary).sort_values('Count', ascending=False)
    
    # Flakers: status = 3 (Missed Visit) or status = 9 (Not Delivery / Missed)
    flaker_cols = ['campaign_name', 'influencer_name', 'influencer_phone', 'status_id', 'booking_created_at']
    flaker_cols = [c for c in flaker_cols if c in df_ci.columns]
    flakers_df = df_ci[df_ci['status_id'].isin([3, 9, 4])][flaker_cols]
    
    return {
        'total_bookings': total_bookings,
        'active_participations': active_count,
        'status_summary': df_status_summary,
        'flakers': flakers_df
    }


def compute_campaign_health(df_campaigns: pd.DataFrame, df_ci: pd.DataFrame = None) -> pd.DataFrame:
    """
    Computes active campaign health:
    - Confirmations vs Targets
    - Visited vs Missing Coverage
    - Progress percentages
    """
    df = df_campaigns.copy()
    
    # Numeric conversions
    num_cols = ['Total List', 'Confirmations', 'Target', 'Visited', 'Coverage', 'Missing_coverage', 'missed_visit', 'Approved', 'Reject']
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
            
    if 'Target' in df.columns and 'Confirmations' in df.columns:
        df['Confirmation_Progress_%'] = np.where(
            df['Target'] > 0,
            round((df['Confirmations'] / df['Target']) * 100.0, 1),
            0.0
        )
        
    return df
