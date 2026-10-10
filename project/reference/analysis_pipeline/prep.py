import pandas as pd, numpy as np, re
d=pd.read_csv('/mnt/user-data/uploads/last_month_s_data.csv',dtype=str,encoding='utf-8-sig')
raw_n=len(d)
d=d.drop_duplicates()
d['t']=pd.to_datetime(d.createdAt)
d=d[(d.isSystem!='1')&d.phone.notna()].copy()
d['out']=(d.isFromMe=='1')
d['agent']=np.where(d.out&d.userName.notna()&(d.userName!='original whatsapp'),d.userName,None)
d['phone_sent']=d.out&(d.agent.isna())
d['content']=d.content.fillna('')
d=d.sort_values(['phone','t','out']).reset_index(drop=True)
d['inv']=d.isInvitation=='1'
d['media']=d.type!='message'
d.to_pickle('/home/claude/clean.pkl')
print(raw_n,len(d),d.out.sum(),d.agent.notna().sum(),d.phone_sent.sum())
print(d[d.agent.notna()].groupby('agent').size().sort_values(ascending=False))
# top frequent outgoing templates
o=d[d.out&(d.content.str.len()>25)]
k=o.content.str.replace(r'[^\w\s]','',regex=True).str[:45]
print(k.value_counts().head(40))
