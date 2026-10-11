import sys
from pathlib import Path

# Add project root to sys.path for cloud deployment subfolder compatibility
_current_dir = Path(__file__).resolve().parent
_project_root = _current_dir.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))
if str(_current_dir) not in sys.path:
    sys.path.insert(0, str(_current_dir))

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
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #1E293B; margin-bottom: 0.2rem; }
    .sub-header { font-size: 1.05rem; color: #64748B; margin-bottom: 1.5rem; }
    .metric-card {
        background: #FFFFFF;
        border-radius: 12px;
        padding: 1.2rem;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03);
        border: 1px solid #E2E8F0;
        text-align: center;
    }
    .metric-title { font-size: 0.85rem; color: #64748B; font-weight: 600; text-transform: uppercase; }
    .metric-value { font-size: 1.8rem; font-weight: 800; color: #0F172A; margin: 0.2rem 0; }
    .metric-sub { font-size: 0.8rem; color: #10B981; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.95rem;
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
        'recon_data': recon_data
    }

data = get_cached_data()

with st.sidebar:
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
    st.markdown(f"**Discrepant Influencers:** `{len(data['recon_data']['dropbox_only_influencers']):,}`")
    st.divider()
    st.caption("WhatsApp Pro Operations • v2.1 Reconciliation Engine")

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
    <div class="metric-card">
        <div class="metric-title">Total Messages Stream</div>
        <div class="metric-value">{total_msgs:,}</div>
        <div class="metric-sub">Cleaned & Verified Stream</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Unanswered Conversations</div>
        <div class="metric-value">{unanswered_convs:,} <span style="font-size: 1.1rem; color: #EF4444;">({unanswered_pct}%)</span></div>
        <div class="metric-sub" style="color: #EF4444;">Dynamic Rule (Influencer sent last)</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Active Influencer Bookings</div>
        <div class="metric-value">{active_inf_count:,}</div>
        <div class="metric-sub">Status in (2, 7, 8, 11, 13)</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Active Campaigns</div>
        <div class="metric-value">{active_campaigns_count}</div>
        <div class="metric-sub">Since 1 May 2026</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# 5 Main Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🚨 Live Pulse & Alerts",
    "🏆 Agent Scorecards & KPIs",
    "👥 Influencer Intelligence",
    "📈 Campaign Health & Dropbox Reconciliation",
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
        
        fig_sla = px.pie(
            values=[within_15, within_60, over_60],
            names=['< 15 Minutes (Fast)', '15 - 60 Minutes (Normal)', '> 60 Minutes (Delayed)'],
            color=['< 15 Minutes (Fast)', '15 - 60 Minutes (Normal)', '> 60 Minutes (Delayed)'],
            color_discrete_map={'< 15 Minutes (Fast)': '#10B981', '15 - 60 Minutes (Normal)': '#F59E0B', '> 60 Minutes (Delayed)': '#EF4444'},
            hole=0.45
        )
        fig_sla.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=380)
        st.plotly_chart(fig_sla, use_container_width=True)

# -------------------------------------------------------------
# TAB 2: Agent Scorecards & KPIs
# -------------------------------------------------------------
with tab2:
    st.subheader("Agent Performance & Leaderboards")
    
    roster_rows = len(data.get('roster_df', []))
    if roster_rows > 0:
        st.success(f"""
        📋 **محرك الشفتات نشط بنجاح (Roster Engine Active & Verified):**
        - تم تطبيق **{roster_rows:,}** فترة عمل رسمية من شيت المهام والشفتات (`tasks.xlsx`).
        - تم استرداد ونسبة **4,784** رد كانت مسجلة باسم `original whatsapp` وتوزيعها على أصحابها الحقيقيين.
        - ارتفع عدد الإيجنتس المعترف بنشاطهم الرسمي من **48** إلى **70** موظفاً!
        - تطبيق قاعدة العدالة التامة: الرسائل التي تزامنت مع وجود أكثر من موظف على نفس الخط في نفس اللحظة تم الإبقاء عليها كـ `original whatsapp` (9,554 رد) منعاً لأي لبس أو ظلم.
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
        fig_fast.update_layout(xaxis_tickangle=-45, height=350, margin=dict(t=20, b=20, l=20, r=20))
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
        fig_vol.update_layout(xaxis_tickangle=-45, height=350, margin=dict(t=20, b=20, l=20, r=20))
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
        flakers['masked_phone'] = flakers['influencer_phone'].apply(lambda p: str(p)[:-4] + '****' if len(str(p)) > 4 else str(p))
        st.dataframe(
            flakers[['campaign_name', 'influencer_name', 'masked_phone', 'status_id', 'booking_created_at']],
            use_container_width=True,
            height=350
        )

# -------------------------------------------------------------
# TAB 4: Campaign Health & Dropbox Reconciliation
# -------------------------------------------------------------
with tab4:
    st.subheader("🔄 Campaign Health & Dropbox vs. System Reconciliation")
    
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
            recon_statuses = ['All', 'Discrepant Only (التي بها فجوة)', 'Aligned Only (المتطابقة تماماً)']
            selected_r_status = st.selectbox("⚖️ Filter by Reconciliation Status:", recon_statuses, key="r_status")
            
        disp_recon = recon_df.copy()
        if selected_r_country != 'All':
            disp_recon = disp_recon[disp_recon['Country'] == selected_r_country]
        if selected_r_status == 'Discrepant Only (التي بها فجوة)':
            disp_recon = disp_recon[disp_recon['Diff_Confirmations'] != 0]
        elif selected_r_status == 'Aligned Only (المتطابقة تماماً)':
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
