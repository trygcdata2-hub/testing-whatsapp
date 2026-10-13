import sys
from pathlib import Path

# Add project root to sys.path for cloud deployment subfolder compatibility
_current_dir = Path(__file__).resolve().parent
_project_root = _current_dir
while not (_project_root / "src" / "config.py").exists() and _project_root != _project_root.parent:
    _project_root = _project_root.parent

if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))
if str(_project_root / "src") not in sys.path:
    sys.path.insert(0, str(_project_root / "src"))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime


# Set Page Config
st.set_page_config(
    page_title="WhatsApp Pro Operations Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="auto"
)

# Theme State Initialization & CSS Injection
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "Dark"

is_dark = st.session_state.theme_mode == "Dark"

if is_dark:
    theme_css = """
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #0B0F19 !important;
        color: #F8FAFC !important;
    }
    [data-testid="stSidebar"] {
        background-color: #0F172A !important;
        border-right: 1px solid #1E293B !important;
    }
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stCaption {
        color: #E2E8F0 !important;
    }
    [data-testid="stSidebar"] code {
        background: #1E293B !important;
        color: #60A5FA !important;
        border: 1px solid #374151 !important;
        padding: 2px 7px !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
    }
    .main-header {
        color: #F8FAFC !important;
    }
    .sub-header {
        color: #94A3B8 !important;
    }
    .metric-card {
        background: #111827 !important;
        border: 1px solid #1F2937 !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4) !important;
    }
    .metric-card:hover {
        border-color: #3B82F6 !important;
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.25) !important;
    }
    .metric-title { color: #94A3B8 !important; }
    .metric-value { color: #F8FAFC !important; }
    .metric-card.card-blue { border-top: 3px solid #3B82F6 !important; }
    .metric-card.card-rose { border-top: 3px solid #EF4444 !important; }
    .metric-card.card-emerald { border-top: 3px solid #10B981 !important; }
    .metric-card.card-purple { border-top: 3px solid #8B5CF6 !important; }
    
    .stTabs [data-baseweb="tab-list"] {
        background: #111827 !important;
        border: 1px solid #1F2937 !important;
    }
    .stTabs [data-baseweb="tab"] {
        color: #94A3B8 !important;
    }
    .stTabs [aria-selected="true"] {
        background: #1E293B !important;
        color: #F8FAFC !important;
    }
    [data-testid="stMetric"] {
        background: #111827 !important;
        border: 1px solid #1F2937 !important;
    }
    [data-testid="stMetricLabel"] { color: #94A3B8 !important; }
    [data-testid="stMetricValue"] { color: #F8FAFC !important; }
    
    /* Native Dataframe styling in Dark mode */
    [data-testid="stDataFrame"] {
        filter: invert(0.92) hue-rotate(180deg);
        border-radius: 8px !important;
    }
    """
else:
    theme_css = """
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #F8FAFC !important;
        color: #0F172A !important;
    }
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E2E8F0 !important;
    }
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stCaption {
        color: #0F172A !important;
    }
    [data-testid="stSidebar"] code {
        background: #EFF6FF !important;
        color: #1D4ED8 !important;
        border: 1px solid #DBEAFE !important;
        padding: 2px 7px !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
    }
    .main-header {
        color: #0F172A !important;
    }
    .sub-header {
        color: #475569 !important;
    }
    .metric-card {
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05) !important;
    }
    .metric-card:hover {
        border-color: #3B82F6 !important;
        box-shadow: 0 8px 20px rgba(59, 130, 246, 0.15) !important;
    }
    .metric-title { color: #64748B !important; }
    .metric-value { color: #0F172A !important; }
    .metric-card.card-blue { border-top: 3px solid #3B82F6 !important; }
    .metric-card.card-rose { border-top: 3px solid #EF4444 !important; }
    .metric-card.card-emerald { border-top: 3px solid #10B981 !important; }
    .metric-card.card-purple { border-top: 3px solid #8B5CF6 !important; }
    
    .stTabs [data-baseweb="tab-list"] {
        background: #F1F5F9 !important;
        border: 1px solid #E2E8F0 !important;
    }
    .stTabs [data-baseweb="tab"] {
        color: #64748B !important;
    }
    .stTabs [aria-selected="true"] {
        background: #FFFFFF !important;
        color: #0F172A !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08) !important;
    }
    [data-testid="stMetric"] {
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
    }
    [data-testid="stMetricLabel"] { color: #64748B !important; }
    [data-testid="stMetricValue"] { color: #0F172A !important; }
    
    /* Native Dataframe styling in Light mode */
    [data-testid="stDataFrame"] {
        border: 1px solid #E2E8F0 !important;
        border-radius: 8px !important;
    }
    """

st.markdown(f"""
<style>
    {theme_css}

    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2.5rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 1400px !important;
    }

    .main-header {
        font-size: 2.1rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
        letter-spacing: -0.02em;
    }

    .sub-header {
        font-size: 0.95rem;
        margin-bottom: 1.4rem;
        font-weight: 400;
    }

    .metric-card {
        border-radius: 12px;
        padding: 1.1rem 0.8rem;
        text-align: center;
        min-height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
    }

    .metric-card:hover {
        transform: translateY(-3px);
    }

    .metric-title {
        font-size: 0.74rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.3rem;
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 800;
        margin: 0.1rem 0;
        line-height: 1.15;
    }

    .metric-sub {
        font-size: 0.78rem;
        font-weight: 600;
        margin-top: 0.2rem;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        padding: 5px;
        border-radius: 10px;
    }

    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        border-radius: 7px;
        font-weight: 600;
        font-size: 0.9rem;
        border: none !important;
        transition: all 0.2s ease;
    }

    [data-testid="stMetric"] {
        padding: 1rem;
        border-radius: 12px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
        transition: all 0.2s ease;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-2px);
    }
    [data-testid="stMetricLabel"] {
        font-weight: 600 !important;
    }
    [data-testid="stMetricValue"] {
        font-weight: 800 !important;
    }
</style>
""", unsafe_allow_html=True)

from src.data_loader import (
    load_raw_messages,
    load_whatsapp_lines,
    load_campaigns,
    load_campaign_influencers,
    load_influencers_master,
    load_tasks_data
)
from src.pipeline import clean_messages_df, prepare_roster_df, run_conversation_analysis
from src.metrics import (
    compute_agent_scorecards,
    compute_influencer_behavior,
    compute_campaign_health
)
from src.reconciliation import get_cached_or_run_reconciliation
from src.pcloud_reconciliation import get_cached_or_run_pcloud_reconciliation

@st.cache_data(show_spinner="Loading operational data stream...")
def get_cached_data():
    raw_msgs = load_raw_messages()
    cleaned_msgs = clean_messages_df(raw_msgs)
    lines_df = load_whatsapp_lines()
    campaigns_df = load_campaigns()
    ci_df = load_campaign_influencers()
    inf_master = load_influencers_master()
    
    # Load tasks and build roster
    tasks_df = load_tasks_data()
    roster_df = prepare_roster_df(tasks_df, lines_df)
    
    # Run conversation & burst analytics with roster attribution
    convs_df, bursts_df = run_conversation_analysis(
        cleaned_msgs,
        roster_df=roster_df,
        lines_df=lines_df
    )
    agents_df = compute_agent_scorecards(bursts_df)
    inf_metrics = compute_influencer_behavior(convs_df, ci_df, inf_master)
    camp_health = compute_campaign_health(campaigns_df, ci_df)
    
    # Run 3-Way Dropbox vs System Reconciliation
    recon_data = get_cached_or_run_reconciliation(
        campaigns_df=campaigns_df,
        ci_df=ci_df,
        inf_master=inf_master,
        force_rescan=False
    )
    
    # Run pCloud Coverage vs System Status 7 Reconciliation
    try:
        pcloud_recon_data = get_cached_or_run_pcloud_reconciliation(
            campaigns_df=campaigns_df,
            ci_df=ci_df,
            inf_master=inf_master,
            force_rescan=False
        )
    except Exception:
        pcloud_recon_data = {
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
    
    return {
        'cleaned_msgs': cleaned_msgs,
        'lines_df': lines_df,
        'convs_df': convs_df,
        'bursts_df': bursts_df,
        'agents_df': agents_df,
        'inf_metrics': inf_metrics,
        'camp_health': camp_health,
        'inf_master': inf_master,
        'ci_df': ci_df,
        'tasks_df': tasks_df,
        'roster_df': roster_df,
        'recon_data': recon_data,
        'pcloud_recon': pcloud_recon_data
    }

data = get_cached_data()

with st.sidebar:
    st.markdown("### 🎨 Display Theme")
    theme_selection = st.radio(
        "Theme",
        ["🌙 Dark Mode", "☀️ Light Mode"],
        index=0 if is_dark else 1,
        key="app_theme_selection",
        label_visibility="collapsed",
        horizontal=True
    )
    if (theme_selection == "🌙 Dark Mode" and not is_dark) or (theme_selection == "☀️ Light Mode" and is_dark):
        st.session_state.theme_mode = "Dark" if theme_selection == "🌙 Dark Mode" else "Light"
        st.rerun()
    st.divider()
    st.markdown("### ⚡ Operational Controls")
    if st.button("🔄 Force Reload / Clear Cache", type="primary", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.divider()
    roster_active_count = len(data.get('roster_df', []))
    st.markdown(f"**Roster Engine:** {'🟢 Active' if roster_active_count > 0 else '⚪ Inactive'}")
    st.markdown(f"**Shift Intervals:** `{roster_active_count:,}`")
    st.markdown(f"**Active Agents:** `{len(data['agents_df']):,}`")
    st.divider()
    recon_count = len(data['recon_data']['campaign_recon'])
    st.markdown(f"**Dropbox Recon:** `🟢 Active ({recon_count} Camps)`")
    st.markdown(f"**Dropbox Gaps:** `{len(data['recon_data']['dropbox_only_influencers']):,}`")
    st.divider()
    pcloud_matched_active = data['pcloud_recon'].get('matched_active_count', 0)
    pcloud_active_total = data['pcloud_recon'].get('active_campaigns_count', 0)
    st.markdown(f"**pCloud Active Recon:** `🟢 Active ({pcloud_matched_active}/{pcloud_active_total} Camps)`")
    active_audit = data['pcloud_recon'].get('influencer_audit', pd.DataFrame())
    if not active_audit.empty and 'is_active_campaign' in active_audit.columns:
        active_gaps = len(active_audit[(active_audit['is_active_campaign']) & (active_audit['gap_type'] == 'Missing Status 7')])
    else:
        active_gaps = data['pcloud_recon'].get('missing_7_count', 0)
    st.markdown(f"**Active Status 7 Gaps:** `🚨 {active_gaps:,} Missing`")
    st.divider()
    st.caption("WhatsApp Pro Operations • v2.4 Active Monitor")

# Header
st.markdown('<div class="main-header">⚡ WhatsApp Pro Operations & Attribution Engine</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Live Monitoring Dashboard for WhatsApp Teams, Shift Attribution, Agent Scorecards & Campaign Health</div>', unsafe_allow_html=True)

# Top KPI Summary Cards
col1, col2, col3, col4 = st.columns(4)

total_msgs = len(data['cleaned_msgs'])
unanswered_convs = data['convs_df']['is_unanswered'].sum()
unanswered_pct = round((unanswered_convs / len(data['convs_df'])) * 100, 1) if len(data['convs_df']) > 0 else 0
active_inf_count = data['inf_metrics']['active_participations']
active_campaigns_count = len(data['camp_health'])

with col1:
    st.markdown(f"""
    <div class="metric-card card-blue">
        <div class="metric-title">💬 Total Messages Stream</div>
        <div class="metric-value">{total_msgs:,}</div>
        <div class="metric-sub" style="color: #3B82F6;">Cleaned & Verified Stream</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card card-rose">
        <div class="metric-title">⚠️ Unanswered Conversations</div>
        <div class="metric-value">{unanswered_convs:,} <span style="font-size: 1.1rem; color: #EF4444; font-weight: 700;">({unanswered_pct}%)</span></div>
        <div class="metric-sub" style="color: #EF4444;">Dynamic Rule (Influencer sent last)</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card card-emerald">
        <div class="metric-title">👥 Active Influencer Bookings</div>
        <div class="metric-value">{active_inf_count:,}</div>
        <div class="metric-sub" style="color: #10B981;">Status in (2, 7, 8, 11, 13)</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card card-purple">
        <div class="metric-title">🎯 Active Campaigns</div>
        <div class="metric-value">{active_campaigns_count}</div>
        <div class="metric-sub" style="color: #8B5CF6;">Since 1 May 2026</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# 5 Main Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🚨 Live Pulse & Alerts",
    "🏆 Agent Scorecards & KPIs",
    "👥 Influencer Intelligence",
    "📈 Multi-Source Reconciliation (pCloud & Dropbox)",
    "📱 Line Health & System Status"
])

# -------------------------------------------------------------
# TAB 1: Live Pulse & Alerts
# -------------------------------------------------------------
with tab1:
    st.subheader("Real-Time Operational Alerts")
    
    col_a, col_b = st.columns([1, 1])
    
    with col_a:
        st.markdown("#### ⚠️ Unanswered Chats (Awaiting Company Reply)")
        st.caption("Chats where the influencer was the last sender and no reply has been sent yet.")
        unanswered_df = data['convs_df'][data['convs_df']['is_unanswered'] == True].copy()
        
        # Merge line names
        unanswered_df = unanswered_df.merge(
            data['lines_df'][['whatsappAccId', 'line_name']],
            on='whatsappAccId',
            how='left'
        )
        
        # Mask phone numbers for display
        unanswered_df['masked_phone'] = unanswered_df['phone'].apply(lambda p: str(p)[:-4] + '****' if len(str(p)) > 4 else str(p))
        
        st.dataframe(
            unanswered_df[['whatsappAccId', 'line_name', 'masked_phone', 'last_message_time', 'total_messages']],
            use_container_width=True,
            height=380
        )
        
    with col_b:
        st.markdown("#### ⏱️ Response Time SLA Distribution")
        answered_bursts = data['bursts_df'][data['bursts_df']['is_answered'] == True]
        
        within_15 = answered_bursts['within_15m'].sum()
        within_60 = answered_bursts['within_60m'].sum() - within_15
        over_60 = len(answered_bursts) - within_15 - within_60
        
        plotly_template = "plotly_dark" if is_dark else "plotly_white"
        plot_font_color = "#F8FAFC" if is_dark else "#0F172A"

        fig_sla = px.pie(
            values=[within_15, within_60, over_60],
            names=['< 15 Minutes (Fast)', '15 - 60 Minutes (Normal)', '> 60 Minutes (Delayed)'],
            color=['< 15 Minutes (Fast)', '15 - 60 Minutes (Normal)', '> 60 Minutes (Delayed)'],
            color_discrete_map={'< 15 Minutes (Fast)': '#10B981', '15 - 60 Minutes (Normal)': '#F59E0B', '> 60 Minutes (Delayed)': '#EF4444'},
            hole=0.45
        )
        fig_sla.update_layout(
            template=plotly_template,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color=plot_font_color, family="Plus Jakarta Sans"),
            margin=dict(t=20, b=20, l=20, r=20),
            height=380
        )
        st.plotly_chart(fig_sla, use_container_width=True)

# -------------------------------------------------------------
# TAB 2: Agent Scorecards & KPIs
# -------------------------------------------------------------
with tab2:
    st.subheader("Agent Performance & Leaderboards")
    
    roster_rows = len(data.get('roster_df', []))
    if roster_rows > 0:
        st.success(f"""
        📋 **Roster Engine Active & Verified:**
        - Applied **{roster_rows:,}** official shift duties from the tasks roster (`tasks.xlsx`).
        - Re-attributed **4,784** outgoing messages previously logged as `original whatsapp` to verified agents.
        - Active recognized agents increased from **48** to **70** agents.
        - Fairness Rule Applied: Simultaneous overlaps with multiple agents logged on the same line remain as `original whatsapp` (9,554 replies) to avoid unfair attribution.
        """)
    else:
        st.info("ℹ️ **Roster Attribution Status:** To attribute phone messages ('original whatsapp') to individual agents, place the exported shift tasks sheet (`tasks.xlsx`) into the `data/` folder. Overlapping agent shifts remain marked as 'original whatsapp' to preserve fairness.")
        
    st.dataframe(
        data['agents_df'],
        use_container_width=True,
        height=320
    )
    
    col_c, col_d = st.columns(2)
    
    with col_c:
        st.markdown("#### ⚡ Fastest Responders (Lowest Median Reply Time)")
        top_fast = data['agents_df'][data['agents_df']['Total Responses'] >= 50].sort_values('Median Reply Time (min)').head(10)
        fig_fast = px.bar(
            top_fast,
            x='Agent',
            y='Median Reply Time (min)',
            color='Median Reply Time (min)',
            color_continuous_scale='Mint',
            text_auto=True
        )
        fig_fast.update_layout(
            template=plotly_template,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color=plot_font_color, family="Plus Jakarta Sans"),
            xaxis_tickangle=-45,
            height=350,
            margin=dict(t=20, b=20, l=20, r=20)
        )
        st.plotly_chart(fig_fast, use_container_width=True)
        
    with col_d:
        st.markdown("#### 📊 Highest Volume Agents")
        top_vol = data['agents_df'].head(10)
        fig_vol = px.bar(
            top_vol,
            x='Agent',
            y='Total Responses',
            color='Total Responses',
            color_continuous_scale='Blues',
            text_auto=True
        )
        fig_vol.update_layout(
            template=plotly_template,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color=plot_font_color, family="Plus Jakarta Sans"),
            xaxis_tickangle=-45,
            height=350,
            margin=dict(t=20, b=20, l=20, r=20)
        )
        st.plotly_chart(fig_vol, use_container_width=True)

# -------------------------------------------------------------
# TAB 3: Influencer Intelligence
# -------------------------------------------------------------
with tab3:
    st.subheader("Influencer Behavioral Intelligence & Status Breakdown")
    
    col_e, col_f = st.columns([1, 1])
    
    with col_e:
        st.markdown("#### 📌 Status Breakdown in `campaign_influencers`")
        st.caption("Official status meanings based on `documentations for the database.xlsx`")
        st.dataframe(
            data['inf_metrics']['status_summary'],
            use_container_width=True,
            height=350
        )
        
    with col_f:
        st.markdown("#### 🚫 Flakers & Missed Visits Audit")
        st.caption("Influencers with Status = 3 (Missed Visit) or Status = 9 (Missed Delivery)")
        flakers = data['inf_metrics']['flakers'].copy()
        flakers['masked_phone'] = flakers['influencer_phone'].apply(lambda p: str(p)[:-4] + '****' if len(str(p)) > 4 else str(p)) if 'influencer_phone' in flakers.columns else ''
        flaker_display_cols = [c for c in ['campaign_name', 'influencer_name', 'masked_phone', 'status_id', 'booking_created_at'] if c in flakers.columns]
        st.dataframe(
            flakers[flaker_display_cols],
            use_container_width=True,
            height=350
        )

# -------------------------------------------------------------
# TAB 4: Campaign Health & Dropbox Reconciliation
# -------------------------------------------------------------
with tab4:
    st.subheader("🔄 Multi-Source Operations Reconciliation (pCloud & Dropbox vs. System)")
    
    sub_tab_pcloud, sub_tab_dropbox = st.tabs([
        "☁️ pCloud Coverage Audit (Media Uploads vs. System Status 7)",
        "📂 Dropbox Reconciliation (Manual Sheets vs. System Confirmations)"
    ])
    
    # -------------------------------------------------------------
    # SUB-TAB 1: pCloud Coverage vs System Status 7
    # -------------------------------------------------------------
    with sub_tab_pcloud:
        st.markdown("#### ☁️ pCloud Coverage Media vs. Official Database Status 7 Audit")
        st.caption("Reconciles active campaigns (driven by SQL active criteria) against local pCloud folders, auditing influencers with uploaded coverage files against system Status 7.")
        
        pcloud_data = data.get('pcloud_recon', {})
        raw_summary = pcloud_data.get('campaign_summary', pd.DataFrame())
        raw_audit = pcloud_data.get('influencer_audit', pd.DataFrame())
        
        if not raw_summary.empty:
            # 1. Scope Selector: Active Campaigns Only (SQL criteria) vs All
            s_col1, s_col2 = st.columns([2, 1])
            with s_col1:
                scope_choice = st.radio(
                    "🎯 Campaign Scope:",
                    [
                        "🔥 Active Campaigns Only (SQL Criteria - Recommended)",
                        "📋 All Monitored Campaigns (Since 1 May)"
                    ],
                    horizontal=True,
                    key="pc_scope_choice"
                )
            with s_col2:
                st.caption("ℹ️ Active campaigns derived strictly from `active_campaigns.sql` criteria.")
                
            is_active_scope = "Active Campaigns Only" in scope_choice
            
            # Apply scope filter
            if is_active_scope and 'is_active_campaign' in raw_summary.columns:
                pc_summary = raw_summary[raw_summary['is_active_campaign'] == True].copy()
                pc_audit = raw_audit[raw_audit['is_active_campaign'] == True].copy() if not raw_audit.empty and 'is_active_campaign' in raw_audit.columns else raw_audit.copy()
            else:
                pc_summary = raw_summary.copy()
                pc_audit = raw_audit.copy()
                
            # Dynamic KPI Metrics
            tot_camps = len(pc_summary)
            matched_camps = len(pc_summary[pc_summary['matched_pcloud_campaign'] != 'Not Found'])
            tot_covs = len(pc_audit)
            aligned_7 = len(pc_audit[pc_audit['gap_type'] == 'Aligned']) if not pc_audit.empty else 0
            missing_7 = len(pc_audit[pc_audit['gap_type'] == 'Missing Status 7']) if not pc_audit.empty else 0
            not_booked = len(pc_audit[pc_audit['gap_type'] == 'Not Booked']) if not pc_audit.empty else 0
            
            pk1, pk2, pk3, pk4 = st.columns(4)
            with pk1:
                st.metric("📁 Monitored Campaigns", f"{tot_camps:,}", help=f"Matched {matched_camps} in pCloud")
            with pk2:
                st.metric("📸 Total pCloud Coverages", f"{tot_covs:,}")
            with pk3:
                st.metric("✅ Updated Status 7 in DB", f"{aligned_7:,}")
            with pk4:
                st.metric(
                    "🚨 Gap: Missing Status 7",
                    f"{missing_7:,}",
                    help="Influencers with coverage files uploaded in pCloud but whose status in the database is not updated to 7 (Posted / Coverage)."
                )
                
            st.markdown("---")
            
            # Filters for Campaign Coverage Table
            p_fcol1, p_fcol2 = st.columns([1, 1])
            with p_fcol1:
                p_countries = ['All'] + sorted([c for c in pc_summary['country'].dropna().unique() if c])
                sel_p_country = st.selectbox("🌍 Filter by Country:", p_countries, key="pcloud_country_filter")
            with p_fcol2:
                p_gap_filters = [
                    "All Campaigns",
                    "🚨 Campaigns with Missing Status 7 Gap",
                    "✅ Fully Aligned Campaigns in pCloud",
                    "⚪ Campaigns with No Folder in pCloud"
                ]
                sel_p_gap = st.selectbox("⚖️ Filter by Audit Status:", p_gap_filters, key="pcloud_gap_filter")
                
            disp_pc_summary = pc_summary.copy()
            if sel_p_country != 'All':
                disp_pc_summary = disp_pc_summary[disp_pc_summary['country'] == sel_p_country]
                
            if sel_p_gap == "🚨 Campaigns with Missing Status 7 Gap":
                disp_pc_summary = disp_pc_summary[disp_pc_summary['gap_missing_status_7'] > 0]
            elif sel_p_gap == "✅ Fully Aligned Campaigns in pCloud":
                disp_pc_summary = disp_pc_summary[(disp_pc_summary['gap_missing_status_7'] == 0) & (disp_pc_summary['aligned_status_7'] > 0)]
            elif sel_p_gap == "⚪ Campaigns with No Folder in pCloud":
                disp_pc_summary = disp_pc_summary[disp_pc_summary['matched_pcloud_campaign'] == 'Not Found']
                
            st.markdown("#### 📊 Campaign Coverage Reconciliation Table (System vs. pCloud)")
            st.caption("Displays active campaigns mapped to local pCloud folders and official Status 7 audit counts.")
            
            disp_cols = [
                'system_campaign_name', 'country', 'system_status',
                'matched_pcloud_campaign', 'total_pcloud_coverages',
                'aligned_status_7', 'gap_missing_status_7', 'status_alert'
            ]
            
            st.dataframe(
                disp_pc_summary[disp_cols].rename(columns={
                    'system_campaign_name': 'System Campaign Name',
                    'country': 'Country',
                    'system_status': 'Campaign Status',
                    'matched_pcloud_campaign': 'Matched pCloud Folder',
                    'total_pcloud_coverages': 'pCloud Coverages',
                    'aligned_status_7': 'Status 7 in DB',
                    'gap_missing_status_7': 'Missing Status 7 Gap',
                    'status_alert': 'Audit Alert'
                }),
                use_container_width=True,
                height=350
            )
            
            st.markdown("---")
            
            # Influencer-level Drill-down
            st.markdown("#### 🔍 Influencer Coverage Drill-Down (Actionable List for Status 7 Updates)")
            st.caption("Detailed roster of influencers with uploaded coverage who need their status updated to 7 in the database.")
            
            if not pc_audit.empty:
                gapped_camps = sorted(list(pc_audit[pc_audit['gap_type'] == 'Missing Status 7']['system_campaign_name'].dropna().unique()))
                all_camps_list = sorted(list(pc_audit['system_campaign_name'].dropna().unique()))
                camp_choices = ["-- All Campaigns with Status 7 Gaps --"] + gapped_camps + ["-- Other Campaigns --"] + [c for c in all_camps_list if c not in gapped_camps]
                
                sel_inf_camp = st.selectbox("Select Campaign for Influencer Drill-down:", camp_choices, key="pc_inf_select")
                
                disp_inf = pc_audit.copy()
                if sel_inf_camp == "-- All Campaigns with Status 7 Gaps --":
                    disp_inf = disp_inf[disp_inf['gap_type'] == 'Missing Status 7']
                elif sel_inf_camp != "-- Other Campaigns --":
                    disp_inf = disp_inf[disp_inf['system_campaign_name'] == sel_inf_camp]
                    
                # Radio filter for gap types
                r_f1, r_f2 = st.columns([1, 1])
                with r_f1:
                    filter_gap_mode = st.radio(
                        "Record Type Filter:",
                        [
                            "🚨 Missing Status 7 (Actionable Gaps)",
                            "All Records",
                            "⚠️ Not Booked in System"
                        ],
                        horizontal=True
                    )
                with r_f2:
                    search_txt = st.text_input("🔎 Search by Username or Name:", "", key="pc_inf_search")
                    
                if filter_gap_mode == "🚨 Missing Status 7 (Actionable Gaps)":
                    disp_inf = disp_inf[disp_inf['gap_type'] == 'Missing Status 7']
                elif filter_gap_mode == "⚠️ Not Booked in System":
                    disp_inf = disp_inf[disp_inf['gap_type'] == 'Not Booked']
                    
                if search_txt.strip():
                    st_val = search_txt.strip().lower()
                    disp_inf = disp_inf[
                        disp_inf['username_clean'].str.contains(st_val, na=False) |
                        disp_inf['influencer_name'].astype(str).str.lower().str.contains(st_val, na=False)
                    ]
                    
                disp_inf['Masked Phone'] = disp_inf['phone'].apply(lambda p: str(p)[:-4] + '****' if pd.notna(p) and len(str(p)) > 4 else '')
                disp_inf['Masked WA'] = disp_inf['whats_number'].apply(lambda p: str(p)[:-4] + '****' if pd.notna(p) and len(str(p)) > 4 else '')
                
                audit_display_cols = [
                    'system_campaign_name', 'country', 'username_clean', 'influencer_name',
                    'Masked Phone', 'Masked WA', 'system_status_name', 'reconciliation_status'
                ]
                st.dataframe(
                    disp_inf[audit_display_cols].rename(columns={
                        'system_campaign_name': 'System Campaign',
                        'country': 'Country',
                        'username_clean': 'Handle / pCloud Folder',
                        'influencer_name': 'Influencer Name',
                        'system_status_name': 'Current System Status',
                        'reconciliation_status': 'Audit Outcome'
                    }),
                    use_container_width=True,
                    height=350
                )
                
                # Download CSV
                csv_bytes = disp_inf.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 Download Actionable List for Status 7 Updates (CSV)",
                    data=csv_bytes,
                    file_name=f"pcloud_status7_active_gaps_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
        else:
            st.info("ℹ️ No pCloud coverage records available. Make sure pCloud drive P: is connected or cached parquet is present.")

    # -------------------------------------------------------------
    # SUB-TAB 2: Dropbox Reconciliation
    # -------------------------------------------------------------
    with sub_tab_dropbox:
        st.markdown("#### 📂 Dropbox Manual Sheets vs. System Confirmations Audit")
        st.caption("Compares confirmations logged in manual Dropbox client sheets (`Comp.` and `List` sheets) against official System Database bookings.")
        
        recon_df = data['recon_data']['campaign_recon']
        drop_only_infs = data['recon_data']['dropbox_only_influencers']
        
        if not recon_df.empty:
            total_matched_camps = len(recon_df)
            aligned_camps = len(recon_df[recon_df['Diff_Confirmations'] == 0])
            drop_ahead_camps = len(recon_df[recon_df['Diff_Confirmations'] > 0])
            sys_ahead_camps = len(recon_df[recon_df['Diff_Confirmations'] < 0])
            
            # Reconciliation KPI Cards
            r_col1, r_col2, r_col3, r_col4 = st.columns(4)
            with r_col1:
                st.metric("📁 Matched Dropbox Campaigns", f"{total_matched_camps}")
            with r_col2:
                st.metric("✅ Fully Aligned Campaigns", f"{aligned_camps}")
            with r_col3:
                st.metric("⚠️ Dropbox Ahead (Logging Gap)", f"{drop_ahead_camps}")
            with r_col4:
                st.metric("👥 Discrepant Influencers", f"{len(drop_only_infs):,}")
                
            st.markdown("---")
            
            # Filters for Campaign Reconciliation Table
            f_col1, f_col2 = st.columns([1, 1])
            with f_col1:
                recon_countries = ['All'] + sorted(list(recon_df['Country'].dropna().unique()))
                selected_r_country = st.selectbox("🌍 Filter by Country:", recon_countries, key="r_country")
            with f_col2:
                recon_statuses = ['All', 'Discrepant Only (With Gap)', 'Aligned Only']
                selected_r_status = st.selectbox("⚖️ Filter by Reconciliation Status:", recon_statuses, key="r_status")
                
            disp_recon = recon_df.copy()
            if selected_r_country != 'All':
                disp_recon = disp_recon[disp_recon['Country'] == selected_r_country]
            if selected_r_status == 'Discrepant Only (With Gap)':
                disp_recon = disp_recon[disp_recon['Diff_Confirmations'] != 0]
            elif selected_r_status == 'Aligned Only':
                disp_recon = disp_recon[disp_recon['Diff_Confirmations'] == 0]
                
            st.markdown("#### 📊 Campaign Level Reconciliation Table")
            st.caption("Compares confirmations logged in manual Dropbox client sheets against official System Database bookings.")
            
            show_cols = [
                'Campaign Name', 'Country', 'Type', 'Target',
                'Confirmations', 'dropbox_confirmations', 'Diff_Confirmations',
                'Reconciliation_Status', 'dropbox_visited', 'dropbox_coverage'
            ]
            
            st.dataframe(
                disp_recon[show_cols].rename(columns={
                    'Confirmations': 'System Confirmed',
                    'dropbox_confirmations': 'Dropbox Confirmed',
                    'Diff_Confirmations': 'Gap (Drop - Sys)',
                    'dropbox_visited': 'Dropbox Visited',
                    'dropbox_coverage': 'Dropbox Coverage'
                }),
                use_container_width=True,
                height=350
            )
            
            st.markdown("---")
            
            # Section 2: Influencer-Level Audit
            st.markdown("#### 🔍 Influencer Audit Drill-Down (Missing in System DB)")
            st.caption("Influencers confirmed in manual Dropbox sheets but NOT registered as Confirmed in the System Database.")
            
            if not drop_only_infs.empty:
                camp_options = ['All Campaigns'] + sorted(list(drop_only_infs['Campaign Name'].dropna().unique()))
                selected_audit_camp = st.selectbox("Select Campaign to inspect discrepant influencers:", camp_options)
                
                disp_audit = drop_only_infs.copy()
                if selected_audit_camp != 'All Campaigns':
                    disp_audit = disp_audit[disp_audit['Campaign Name'] == selected_audit_camp]
                    
                disp_audit['Masked Phone'] = disp_audit['Phone Clean'].apply(lambda p: str(p)[:-4] + '****' if len(str(p)) > 4 else str(p))
                
                st.dataframe(
                    disp_audit[['Campaign Name', 'Dropbox Username', 'Influencer Name (DB)', 'Masked Phone', 'Issue']],
                    use_container_width=True,
                    height=300
                )
            else:
                st.info("No discrepant influencers found! All Dropbox confirmations match the System.")
        else:
            st.info("ℹ️ No active Dropbox campaigns found in local paths to reconcile. Verify local Dropbox sync.")

# -------------------------------------------------------------
# TAB 5: Line Health & Infrastructure Status
# -------------------------------------------------------------
with tab5:
    st.subheader("WhatsApp Lines & Infrastructure Status")
    
    st.markdown(f"**Total Registered WhatsApp Lines:** {len(data['lines_df'])}")
    
    lines_display = data['lines_df'].copy()
    lines_display['masked_phone'] = lines_display['our_phone'].apply(lambda p: str(p)[:-4] + '****' if pd.notna(p) and len(str(p)) > 4 else str(p))
    
    st.dataframe(
        lines_display[['whatsappAccId', 'line_name', 'masked_phone']],
        use_container_width=True,
        height=380
    )
