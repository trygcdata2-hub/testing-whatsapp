import pandas as pd
import numpy as np

# 1. Load data
print("Loading data...")
d = pd.read_csv('data/last_month_s_data.csv', dtype=str, encoding='utf-8-sig').drop_duplicates()
d['createdAt'] = pd.to_datetime(d['createdAt'])
d = d.sort_values(['whatsappAccId', 'phone', 'createdAt'])

# 2. Basic keywords
yes_keywords = ['تم', 'موافق', 'اكيد', 'طبعا', 'اوك', 'بإذن الله', 'باذن الله', 'ان شاء الله', 'تمام', 'yes', 'ok']
logistics_keywords = ['موقع', 'لوكيشن', 'location', 'maps.app.goo.gl', 'بريف', 'brief', 'التفاصيل', 'موعد', 'تأكيد']

# 3. Identify conversations
# Group by conversation (line + phone)
conversations = []
grouped = d.groupby(['whatsappAccId', 'phone'])

for name, group in grouped:
    if str(name[1]) == 'nan':
        continue
        
    msgs = group.to_dict('records')
    
    # Look for the last "Yes" from the influencer
    last_yes_idx = -1
    for i in range(len(msgs)-1, -1, -1):
        msg = msgs[i]
        if msg['isFromMe'] == '0' and str(msg['content']) != 'nan':
            content = str(msg['content']).lower()
            if any(k in content for k in yes_keywords):
                last_yes_idx = i
                break
                
    if last_yes_idx == -1:
        continue # No yes found
        
    # Analyze what agent did after the Yes
    yes_msg = msgs[last_yes_idx]
    agent_replies_after = [m for m in msgs[last_yes_idx+1:] if m['isFromMe'] == '1']
    
    bucket = None
    if len(agent_replies_after) == 0:
        # Check if 24h passed
        # Simplification for sample: if no reply at all in the dataset after Yes
        bucket = 'Yes + No Reply'
    else:
        # Check if logistics were sent
        sent_logistics = False
        for m in agent_replies_after:
            content = str(m['content']).lower()
            if any(k in content for k in logistics_keywords):
                sent_logistics = True
                break
                
        if sent_logistics:
            bucket = 'Yes + Logistics Sent'
        else:
            bucket = 'Yes + Replied but No Logistics'
            
    # Format the conversation snippet (2 messages before yes, yes, and all after)
    start_idx = max(0, last_yes_idx - 2)
    snippet = []
    for m in msgs[start_idx:last_yes_idx+1 + 3]: # up to 3 messages after
        sender = "Influencer" if m['isFromMe'] == '0' else f"Agent ({m['userName']})"
        snippet.append(f"[{m['createdAt']}] {sender}: {m['content']}")
        
    conversations.append({
        'Line': name[0],
        'Phone': name[1],
        'Bucket': bucket,
        'Yes Time': yes_msg['createdAt'],
        'Conversation Snippet': '\n\n'.join(snippet)
    })

df_results = pd.DataFrame(conversations)

# 4. Sample 30 from each bucket
final_samples = pd.DataFrame()
for bucket in df_results['Bucket'].unique():
    subset = df_results[df_results['Bucket'] == bucket]
    n_samples = min(30, len(subset))
    sampled = subset.sample(n_samples, random_state=42)
    final_samples = pd.concat([final_samples, sampled])

# 5. Export to Excel
output_file = 'Funnel_Verification_Samples.xlsx'
final_samples.to_excel(output_file, index=False)
print(f"Exported {len(final_samples)} samples to {output_file}")
