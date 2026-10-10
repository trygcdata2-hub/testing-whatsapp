import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.data_loader import (
    load_whatsapp_lines,
    load_google_sheet_tasks,
    load_campaigns,
    load_campaign_influencers,
    load_influencers_master
)

lines = load_whatsapp_lines()
print("Lines count:", len(lines))

campaigns = load_campaigns()
print("Campaigns count:", len(campaigns))
print("Campaign columns:", list(campaigns.columns[:6]))

ci = load_campaign_influencers()
print("Campaign influencers count:", len(ci))
print("Active influencers rows count:", ci['is_active_influencer'].sum())

inf = load_influencers_master()
print("Influencers master count:", len(inf))
