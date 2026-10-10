import pandas as pd, numpy as np, re, math, pickle, unicodedata
exec(open('tables.py').read().split("# ---------- baselines")[0])  # helpers + loads
P=pickle.load(open('tabs1.pkl','rb')); t=P['t']; SC=P['SC']; PERS=P['PERS']
def norm(s):
    s=unicodedata.normalize('NFKC',str(s)).lower(); s=re.sub('[\u064b-\u0652\u0640]','',s)
    return re.sub('[أإآ]','ا',s).replace('ى','ي').replace('ة','ه')
# --- revise persuasion verdict on kind x brand z ---
def vd(r):
    z=r['z (kind×brand)']; n=r['Ask-turns']
    if n<100: return 'Too few turns (<100)'
    return 'Clearly above expected' if z>=3 else 'Clearly below expected' if z<=-3 else 'Leaning above' if z>=1.5 else 'Leaning below' if z<=-1.5 else 'In line'
PERS['Verdict']=PERS.apply(vd,axis=1)
PERS=PERS.sort_values('z (kind×brand)',ascending=False).reset_index(drop=True)
# --- shift-adjusted reply time ---
am=d[d.agent.notna()].copy(); am['h']=am.t.dt.hour
prof=am.groupby(['agent','h']).size().unstack(fill_value=0); prof=prof.div(prof.sum(axis=1),axis=0)
R['arr_h']=R.inbound_at.dt.hour
RR=R[(R.replied==1)&(~R.late)&R.responder.notna()].copy()
RR['onshift']=[ (a in prof.index) and prof.loc[a,h]>=0.04 for a,h in zip(RR.responder,RR.arr_h)]
sh=RR[RR.onshift].groupby('responder').rt_min.agg(['median','count'])
SC['med_shift']=SC.Agent.map(sh['median']); SC['n_shift']=SC.Agent.map(sh['count'])
# --- brand map & country ---
tb=t[t.brand!='Unknown'].groupby('phone').brand.agg(lambda s:s.value_counts().index[0])
d['brand']=d.phone.map(tb).fillna('Unknown')
# --- Features ---
FEATS={'PITCH':[('starts_emoji','Starts with an emoji (broadcast look)'),('starts_greeting','Opens with a greeting (هلا / مرحبا / اهلين)'),('cta_question','Ends with a question'),('cta_tam','Asks to send «تم» to join'),('urgency','Urgency / "limited time" wording'),('benefit','Mentions the perk (guest, drink, catering…)'),('gulf','Written in Gulf dialect'),('is_tmpl','Sent as a shared template (15+ identical openings)')],
 'CHAT':[('closed_q','Closed question (short, ends with ؟)'),('proposes_time','Proposes a day / time'),('has_q','Contains a question')],
 'REMINDER':[('has_q','Contains a question'),('proposes_time','Proposes a day / time'),('closed_q','Closed question (short, ends with ؟)')]}
t['is_tmpl']=t.template_key.notna().astype(int)
def adjlift(g1,g0,col):
    r0=g0.groupby('brand')[col].agg(['mean','size']); allr=g0[col].mean()
    exp=0
    for b,gg in g1.groupby('brand'):
        rate=r0.loc[b,'mean'] if b in r0.index and r0.loc[b,'size']>=20 else allr
        exp+=rate*len(gg)
    return g1[col].sum()/exp if exp>0 else np.nan
FT=[]
for kind,fl in FEATS.items():
    k=t[t.kind==kind]
    for col,label in fl:
        g1=k[k[col]==1]; g0=k[k[col]==0]
        if len(g1)<10 or len(g0)<10: continue
        r1,r0=g1.replied.mean(),g0.replied.mean(); a1,a0=g1.accepted.mean(),g0.accepted.mean()
        p=min(ptest(g1.replied.sum(),len(g1),g0.replied.sum(),len(g0)),ptest(g1.accepted.sum(),len(g1),g0.accepted.sum(),len(g0)))
        al_r=adjlift(g1,g0,'replied'); al_a=adjlift(g1,g0,'accepted')
        rob='Yes' if (min(len(g1),len(g0))>=100 and p<0.01 and (al_r-1)*(r1/r0-1)>0 and (al_a-1)*(a1/a0-1)>0) else 'No'
        FT.append([kind,label,len(g1),r1,a1,len(g0),r0,a0,r1/r0 if r0 else np.nan,a1/a0 if a0 else np.nan,al_r,al_a,p,rob])
FT=pd.DataFrame(FT,columns=['Message kind','Feature','n (with)','Reply rate (with)','Accept rate (with)','n (without)','Reply rate (without)','Accept rate (without)','Reply lift','Accept lift','Reply lift (brand-adjusted)','Accept lift (brand-adjusted)','p-value','Robust?'])
print(FT.round(3).to_string())
LEN=[]
for kind in ['CHAT','PITCH','REMINDER']:
    for b,g in t[t.kind==kind].groupby('len_bucket'):
        LEN.append([kind,b,len(g),g.replied.mean(),g.accepted.mean()])
LEN=pd.DataFrame(LEN,columns=['Message kind','Length (chars)','Turns','Reply rate','Accept rate'])
LEN['o']=LEN['Length (chars)'].map({'≤20':0,'21-45':1,'46-90':2,'91-200':3,'200+':4}); LEN=LEN.sort_values(['Message kind','o']).drop(columns='o')
pit=t[t.kind=='PITCH'].copy(); pit['hb']=pd.cut(pit.hour,[-1,5,9,13,17,21,23],labels=['00–05','06–09','10–13','14–17','18–21','22–23']).astype(str)
HR=pit.groupby('hb').agg(n=('replied','size'),rep=('replied','mean'),acc=('accepted','mean')).reset_index()
print(LEN.round(3).to_string()); print(HR.round(3))
# brand / country / dow of all ask turns
ask=t[t.ask_turn==1]
def seg(col,minn=100):
    x=ask.groupby(col).agg(turns=('replied','size'),rep=('replied','mean'),acc=('accepted','mean'),phones=('phone','nunique')).reset_index()
    return x[x.turns>=minn].sort_values('turns',ascending=False)
BRD=seg('brand'); CTY=seg('country'); 
ask=ask.assign(dow=ask.t0.dt.day_name()); DOW=ask.groupby('dow').agg(turns=('replied','size'),rep=('replied','mean'),acc=('accepted','mean')).reset_index()
# brand × kind: pitch conversions
BRD_P=t[t.kind=='PITCH'].groupby('brand').agg(pitches=('replied','size'),rep=('replied','mean'),acc=('accepted','mean'),agents=('first_agent','nunique')).reset_index().query('pitches>=100').sort_values('pitches',ascending=False)
print(BRD.round(3)); print(CTY.round(3)); print(BRD_P.round(3))
# --- Templates ---
tt=t[t.template_key.notna()&(t.kind!='LOGISTICS')]
TP=tt.groupby('template_key').agg(brand=('brand',lambda s:s.value_counts().index[0]),kind=('kind',lambda s:s.value_counts().index[0]),n=('replied','size'),agents=('first_agent','nunique'),rep=('replied','sum'),acc=('accepted','sum'),length=('chars','mean'),ex=('first_text','first')).reset_index()
TP=TP[TP.n>=40].copy(); TP['rr']=TP.rep/TP.n; TP['ar']=TP.acc/TP.n
TP['lift']=TP.ar/TP.kind.map(ask.groupby('kind').accepted.mean())
TP=TP.sort_values('n',ascending=False).head(60)
TP['ex']=TP.ex.str.replace('\n',' ').str[:220]
# --- After yes ---
ts=t.sort_values(['phone','t0']).reset_index(drop=True)
ts['next_t0']=ts.groupby('phone').t0.shift(-1); ts['next_agent']=ts.groupby('phone').first_agent.shift(-1); ts['next_kind']=ts.groupby('phone').kind.shift(-1)
y=ts[ts.accepted==1].copy()
y['follow_min']=(y.next_t0-y.in_t).dt.total_seconds()/60
y['followed']=(y.follow_min<=1440).astype(int)
y['censored']=y.in_t>END-pd.Timedelta(hours=3)
y['real_yes']=y.ask_turn
y['yes_hour']=y.in_t.dt.hour
Y=y[(y.real_yes==1)&(~y.censored)&y.first_agent.notna()]
AY=Y.groupby('first_agent').agg(yes=('followed','size'),fu=('followed','sum'),med=('follow_min',lambda s:s[s<=1440].median())).reset_index()
AY['nofu']=AY.yes-AY.fu; AY['rate']=AY.nofu/AY.yes; AY=AY[AY.yes>=15].sort_values('yes',ascending=False)
Yh=Y.groupby(pd.cut(Y.yes_hour,[-1,5,9,13,17,21,23],labels=['00–05','06–09','10–13','14–17','18–21','22–23'])).agg(yes=('followed','size'),nofu=('followed',lambda s:(1-s).sum()),med=('follow_min',lambda s:s[s<=1440].median())).reset_index()
Yh['rate']=Yh.nofu/Yh.yes
bins=[-1,15,60,240,1440]; Yb=Y.assign(b=pd.cut(Y.follow_min.where(Y.followed==1),bins,labels=['≤15 min','15–60 min','1–4 h','4–24 h'])).b.value_counts().reindex(['≤15 min','15–60 min','1–4 h','4–24 h']).fillna(0)
nofu_n=int((1-Y.followed).sum())
print(AY.round(2)); print(Yh.round(2)); print(Yb, nofu_n, len(Y), Y.follow_min[Y.followed==1].median())
# does fast follow-up matter? logistics sent within 24h by speed
Y2=Y.copy(); Y2['logi']=((Y2.next_kind=='LOGISTICS')&(Y2.followed==1)).astype(int)
# --- Objections ---
inbm=d[~d.out&(d.type=='message')&(d.content.str.len()>2)].copy(); inbm['n']=inbm.content.map(norm)
TOP=[('Date / time','موعد|وقت|متي|الساعه|اي يوم|بكره|تاريخ|الاسبوع|الاحد|الاثنين|الثلاثاء|الاربعاء|الخميس|الجمعه|السبت'),
('Branch / location','فرع|وين|موقع|لوكيشن|location|عنوان|اي منطقه|مدينه|حي '),
('Content requirements','ستوري|ريل|فيديو|تصوير|محتوي|بوست|تغطيه|سناب|تيك توك|انستقرام|انستغرام'),
('Menu / product','منيو|قائمه|وجبه|طبق|منتج|مكونات|menu|ايش فيه'),
('Wants payment / paid ad','مدفوع|دفع|مقابل|سعر|تكلفه|فلوس|paid|fee|ريت|بكم|اعلان'),
('Declines / unavailable','اعتذر|ما اقدر|مشغول|غير متاح|مو متاح|لا شكرا|مسافر|ظروف|not available|sorry|غير مهتم'),
('Delivery / order status','توصيل|طلب|اوردر|شحنه|لم يصل|ما وصل|دليفري|order|لسه ما وصل'),
('Code / discount','كود|خصم|discount|code|promo'),
('Guests / companions','ضيف|ضيوف|اصحاب|مرافق|شخصين|اشخاص|companion|معي'),
('Reschedule / cancel','تاجيل|تغيير الموعد|اغير الموعد|الغاء|الغي|cancel|reschedule|اعيد الجدوله')]
bt=inbm.brand.value_counts(); topb=[b for b in bt.index if b!='Unknown'][:6]
rows=[]
for name,pat in TOP:
    m=inbm.n.str.contains(pat,regex=True); inbm[name]=m
    q=m&(inbm.n.str.contains('؟|\\?',regex=True)|(name in('Declines / unavailable','Wants payment / paid ad')))
    rows.append([name,int(m.sum()),int(q.sum())]+[int((m&(inbm.brand==b)).sum()) for b in topb]+[int((m&(inbm.country==c)).sum()) for c in ['KSA','Kuwait','UAE']])
OBJ=pd.DataFrame(rows,columns=['Topic','All messages','Questions / declines / payment']+topb+['KSA','Kuwait','UAE'])
PREP={'Date / time':'Offer 2 concrete slots in the first reply instead of "when suits you?"','Branch / location':'Ready branch list + map links per city','Content requirements':'One-screen brief (what to film / what not to) sent before they ask','Menu / product':'Short menu / product card with photos per campaign','Wants payment / paid ad':'State barter-only vs paid in the first pitch so paid-only creators self-select out','Declines / unavailable':'Always reply with a re-invite offer and tag for the next campaign','Delivery / order status':'Auto-send tracking / delivery window once address is received','Code / discount':'Send the code in the same message as the brief','Guests / companions':'State guest count in the pitch text','Reschedule / cancel':'Fixed reschedule rule + one-tap new slot options'}
OBJ['What to prepare']=OBJ.Topic.map(PREP); print(OBJ)
# inbound tagged evidence
INB=inbm[inbm[[x[0] for x in TOP]].any(axis=1)].copy()
INB['topics']=INB.apply(lambda r:', '.join([x[0] for x in TOP if r[x[0]]]),axis=1)
INB=INB[['phone','t','topics','brand','country','content']].rename(columns={'t':'at','content':'text'}).head(15000)
# --- time series ---
d['date']=d.t.dt.date; R['date']=R.inbound_at.dt.date
RRf=R[(R.replied==1)&(~R.late)]
DAY=pd.DataFrame({'agent_msgs':d[d.agent.notna()].groupby('date').size(),'active_agents':d[d.agent.notna()].groupby('date').agent.nunique(),
 'inbound_bursts':R.groupby('date').size(),'median_rt':RRf.groupby('date').rt_min.median(),'pct15':RRf.groupby('date').rt_min.apply(lambda s:(s<=15).mean()),
 'unanswered':R[R.unanswered].groupby('date').size()}).fillna(0)
DAY['unans_rate']=DAY.unanswered/(DAY.inbound_bursts-R[R.closer_only].groupby('date').size().reindex(DAY.index).fillna(0))
DAY['pitches']=t[t.kind=='PITCH'].groupby(t.t0.dt.date).size(); DAY['pitch_reply']=t[t.kind=='PITCH'].groupby(t.t0.dt.date).replied.mean()
DAY['yes']=t[(t.accepted==1)&(t.ask_turn==1)].groupby(t.in_t.dt.date).size()
DAY=DAY.fillna(0).reset_index().rename(columns={'index':'date'})
DAY['dow']=pd.to_datetime(DAY.date).dt.day_name()
# hourly coverage
nd=d.date.nunique()
H=pd.DataFrame(index=range(24))
H['inbound_per_day']=R.groupby('arr_h').size().reindex(range(24)).fillna(0)/nd
ah=d[d.agent.notna()].assign(h=lambda x:x.t.dt.hour,date=lambda x:x.t.dt.date).groupby(['date','h']).agent.nunique().groupby('h').mean()
H['agents_active']=ah.reindex(range(24)).fillna(0)
H['median_rt']=RRf.groupby('arr_h').rt_min.median()
H['pct15']=RRf.groupby('arr_h').rt_min.apply(lambda s:(s<=15).mean())
base=R[~R.closer_only].groupby('arr_h').size(); H['unans_rate']=R[R.unanswered].groupby('arr_h').size().div(base)
H['pitches_per_day']=t[t.kind=='PITCH'].groupby('hour').size().reindex(range(24)).fillna(0)/nd
H['pitch_reply']=t[t.kind=='PITCH'].groupby('hour').replied.mean()
H['inbound_per_agent']=H.inbound_per_day/H.agents_active.replace(0,np.nan)
H=H.fillna(0).reset_index().rename(columns={'index':'hour'})
print(H.round(2).to_string()); print(DAY.round(2).to_string())
# weekly agent
d['wk']=((pd.to_datetime(d.date)-pd.Timestamp('2026-09-04')).dt.days//7).clip(upper=3)
RRf=RRf.assign(wk=((pd.to_datetime(RRf.date)-pd.Timestamp('2026-09-04')).dt.days//7).clip(upper=3))
t['wk']=((t.t0.dt.normalize()-pd.Timestamp('2026-09-04')).dt.days//7).clip(upper=3)
topag=SC[(SC.role=='Inbox responder')&(SC.msgs>=1000)].Agent.tolist()
WK=[]
for ag in topag:
    for w in range(4):
        m=d[(d.agent==ag)&(d.wk==w)]; r=RRf[(RRf.responder==ag)&(RRf.wk==w)]; a=t[(t.first_agent==ag)&(t.wk==w)&(t.ask_turn==1)]
        WK.append([ag,f'W{w+1}',len(m),len(r),r.rt_min.median() if len(r) else np.nan,a.accepted.mean() if len(a) else np.nan,len(a)])
WK=pd.DataFrame(WK,columns=['Agent','Week','Messages','Replies','Median reply (min)','Accept rate (ask-turns)','Ask-turns'])
# team KPIs & funnel
ph=t.groupby('phone')
pitched=set(t[t.kind=='PITCH'].phone)
rep_after=set(t[(t.kind=='PITCH')&(t.replied==1)].phone); yes_p=set(t[(t.accepted==1)&(t.ask_turn==1)].phone)
fy=t[(t.accepted==1)&(t.ask_turn==1)].groupby('phone').t0.min()
lg=t[t.kind=='LOGISTICS'].groupby('phone').t0.min(); pv=t[t.kind=='POST_VISIT'].groupby('phone').t0.min()
lg_after=set(p for p in yes_p if p in lg.index and lg[p]>fy[p]); pv_after=set(p for p in yes_p if p in pv.index and pv[p]>fy[p])
FUN=[('Conversations with any message',d.phone.nunique()),('Conversations pitched (invitation sent)',len(pitched)),('…influencer replied to a pitch',len(rep_after&pitched)),('Conversations with a real yes',len(yes_p)),('…then address / brief / logistics sent',len(lg_after)),('…then post-visit follow-up (review / post)',len(pv_after))]
print(FUN)
FB=[]
for b in BRD_P.brand.head(12):
    pb=set(t[(t.kind=='PITCH')&(t.brand==b)].phone); yb=set(t[(t.accepted==1)&(t.ask_turn==1)&(t.brand==b)].phone)
    FB.append([b,len(pb),len(set(t[(t.kind=='PITCH')&(t.brand==b)&(t.replied==1)].phone)),len(yb),len([p for p in yb if p in lg_after]),len([p for p in yb if p in pv_after])])
FB=pd.DataFrame(FB,columns=['Brand','Pitched convs','Replied','Real yes','Logistics sent','Post-visit follow-up'])
# never answered
inbound_ph=set(d[~d.out].phone); out_ph=set(d[d.out].phone)
never=len(inbound_ph-out_ph)
# agent-level kind mix / hour profile
pickle.dump(dict(t=t,SC=SC,PERS=PERS,BL=BL if 'BL' in dir() else None,FT=FT,LEN=LEN,HR=HR,BRD=BRD,CTY=CTY,DOW=DOW,BRD_P=BRD_P,TP=TP,AY=AY,Yh=Yh,Yb=Yb,Y=Y,OBJ=OBJ,INB=INB,DAY=DAY,H=H,WK=WK,FUN=FUN,FB=FB,never=never,R=R,topb=topb,nofu_n=nofu_n,y=y),open('tabs2.pkl','wb'))
print('never answered convs',never)
print(SC[['Agent','med','med_shift','n_shift']].head(25).round(1).to_string())
