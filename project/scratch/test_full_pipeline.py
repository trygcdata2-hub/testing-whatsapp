import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.data_loader import (
    load_raw_messages,
    load_whatsapp_lines,
    load_campaigns,
    load_campaign_influencers,
    load_influencers_master
)
from src.pipeline import clean_messages_df, run_conversation_analysis
from src.metrics import (
    compute_agent_scorecards,
    compute_influencer_behavior,
    compute_campaign_health
)

print("1. Loading messages...")
raw = load_raw_messages()
clean = clean_messages_df(raw)
print(f"Clean messages: {len(clean):,}")

print("2. Running conversation analysis...")
convs, bursts = run_conversation_analysis(clean)
unanswered_count = convs['is_unanswered'].sum()
print(f"Total conversations: {len(convs):,}, Unanswered: {unanswered_count:,}")
print(f"Total bursts: {len(bursts):,}")

print("3. Computing agent scorecards...")
agents = compute_agent_scorecards(bursts)
print("Top 5 agents by volume:")
print(agents.head(5).to_string())

print("4. Testing Influencer and Campaign metrics...")
ci = load_campaign_influencers()
inf = load_influencers_master()
camps = load_campaigns()

inf_res = compute_influencer_behavior(convs, ci, inf)
print(f"Active influencer bookings (status in 2,7,8,11,13): {inf_res['active_participations']:,}")

camp_health = compute_campaign_health(camps, ci)
print(f"Campaigns processed: {len(camp_health):,}")

print("\n--- ALL PIPELINE CHECKS PASSED PERFECTLY! ---")
