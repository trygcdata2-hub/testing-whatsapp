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
    load_google_sheet_tasks
)
from src.pipeline import clean_messages_df, run_conversation_analysis
from src.metrics import (
    compute_agent_scorecards,
    compute_influencer_behavior,
    compute_campaign_health
)

@st.cache_data(show_spinner="Loading operational data stream...")
def get_cached_data():
    raw_msgs = load_raw_messages()
    cleaned_msgs = clean_messages_df(raw_msgs)
    lines_df = load_whatsapp_lines()
    campaigns_df = load_campaigns()
    ci_df = load_campaign_influencers()
    inf_master = load_influencers_master()
    
    # Run conversation & burst analytics
    convs_df, bursts_df = run_conversation_analysis(cleaned_msgs)
    agents_df = compute_agent_scorecards(bursts_df)
    inf_metrics = compute_influencer_behavior(convs_df, ci_df, inf_master)
    camp_health = compute_campaign_health(campaigns_df, ci_df)
    
    return {
        'cleaned_msgs': cleaned_msgs,
        'lines_df': lines_df,
        'convs_df': convs_df,
        'bursts_df': bursts_df,
        'agents_df': agents_df,
        'inf_metrics': inf_metrics,
        'camp_health': camp_health,
        'inf_master': inf_master,
        'ci_df': ci_df
    }

data = get_cached_data()

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
    "📈 Campaign Health & Outcomes",
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
# TAB 4: Campaign Health & Outcomes
# -------------------------------------------------------------
with tab4:
    st.subheader("Active Campaigns Health & Target Progress")
    
    countries_list = ['All'] + list(data['camp_health']['Country'].dropna().unique())
    selected_country = st.selectbox("Filter by Country:", countries_list)
    
    filtered_camps = data['camp_health']
    if selected_country != 'All':
        filtered_camps = filtered_camps[filtered_camps['Country'] == selected_country]
        
    st.dataframe(
        filtered_camps[['Campaign Name', 'status', 'Country', 'Type', 'Target', 'Confirmations', 'Confirmation_Progress_%', 'Visited', 'Coverage', 'Missing_coverage', 'missed_visit']],
        use_container_width=True,
        height=400
    )

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
