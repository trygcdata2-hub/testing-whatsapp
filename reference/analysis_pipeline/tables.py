import pandas as pd, numpy as np, re, math, pickle
t=pd.read_pickle('turns.pkl'); R=pd.read_pickle('re.pkl'); d=pd.read_pickle('d2.pkl'); runs=pd.read_pickle('runs.pkl')
END=d.t.max(); START=d.t.min()
TEST={'Developers Team','IT Team','trainee01'}
t['agent']=t.first_agent
ta=t[t.agent.notna()].copy()
def wilson(k,n,z=1.96):
    if n==0: return (np.nan,np.nan)
    p=k/n; den=1+z*z/n; c=(p+z*z/(2*n))/den; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return (max(0,c-h),min(1,c+h))
def ptest(k1,n1,k0,n0):
    if min(n1,n0)==0: return np.nan
    p=(k1+k0)/(n1+n0)
    se=math.sqrt(p*(1-p)*(1/n1+1/n0)) if 0<p<1 else 0
    if se==0: return np.nan
    z=(k1/n1-k0/n0)/se
    return math.erfc(abs(z)/math.sqrt(2))
# ---------- baselines ----------
ask=t[t.ask_turn==1]
BL=t.groupby('kind').agg(turns=('replied','size'),rep=('replied','mean'),acc=('accepted','mean')).reset_index()
bk=ask.groupby('kind').agg(r=('replied','mean'),a=('accepted','mean'))
bb=ask.groupby(['kind','brand']).agg(n=('replied','size'),r=('replied','mean'),a=('accepted','mean'))
t['exp_rep']=t.kind.map(bk.r); t['exp_acc']=t.kind.map(bk.a)
def adj(r):
    k=(r.kind,r.brand)
    if k in bb.index and bb.loc[k,'n']>=50: return pd.Series([bb.loc[k,'r'],bb.loc[k,'a']])
    return pd.Series([r.exp_rep,r.exp_acc])
# vectorised kind x brand baseline
bbm=bb.reset_index(); bbm=bbm[bbm.n>=50][['kind','brand','r','a']].rename(columns={'r':'rb','a':'ab'})
t=t.merge(bbm,on=['kind','brand'],how='left'); t['exp_rep_b']=t.rb.fillna(t.exp_rep); t['exp_acc_b']=t.ab.fillna(t.exp_acc)
ta=t[t.first_agent.notna()].copy(); ta['agent']=ta.first_agent; ask=t[t.ask_turn==1]; aska=ta[ta.ask_turn==1]
# ---------- persuasion ----------
rows=[]
for ag,g in aska.groupby('agent'):
    n=len(g)
    if n<30: continue
    k=int(g.accepted.sum()); er=g.exp_rep.sum(); ea=g.exp_acc.sum(); eab=g.exp_acc_b.sum()
    lo,hi=wilson(k,n); z=(k-ea)/math.sqrt(ea) if ea>0 else np.nan
    zb=(k-eab)/math.sqrt(eab) if eab>0 else np.nan
    if n<100: verdict='Too few turns (<100)' if abs(z)<2 else ('Promising (<100 turns)' if z>0 else 'Concerning (<100 turns)')
    else: verdict='Clearly above expected' if z>=2 else 'Clearly below expected' if z<=-2 else 'Leaning above' if z>=1 else 'Leaning below' if z<=-1 else 'In line'
    p=g[g.kind=='PITCH']; c=g[g.kind=='CHAT']
    rows.append([ag,n,int(g.replied.sum()),g.replied.mean(),er,g.replied.sum()/er,k,k/n,ea,k/ea if ea else np.nan,lo,hi,z,verdict,len(p),p.accepted.mean() if len(p) else np.nan,len(c),c.accepted.mean() if len(c) else np.nan,int(g.declined.sum()),int(g.payment_q.sum()),eab,k/eab if eab else np.nan,zb])
PERS=pd.DataFrame(rows,columns=['Agent','Ask-turns','Influencer replied','Reply rate','Expected replies','Reply lift','Accepted','Accept rate','Expected accepts','Accept lift','Accept rate – low (95%)','Accept rate – high (95%)','z-score','Verdict','Pitch turns','Pitch accept rate','Chat turns','Chat accept rate','Declined','Wanted payment','Expected accepts (kind×brand)','Accept lift (kind×brand)','z (kind×brand)']).sort_values('Accept lift',ascending=False)
print(PERS[['Agent','Ask-turns','Accept rate','Accept lift','z-score','Accept lift (kind×brand)','z (kind×brand)','Verdict']].round(2).to_string())
# ---------- response metrics ----------
RR=R[R.replied==1]
resp=RR[~RR.late]
# per agent
d['date']=d.t.dt.date
am=d[d.agent.notna()]
first_msg=d.groupby('phone').head(1)
opened=first_msg[first_msg.agent.notna()].groupby('agent').size()
infl_replied=[]  # per agent: convs where influencer wrote after agent's first msg
ag_first=am.groupby(['agent','phone']).t.min().reset_index()
inbt=d[~d.out][['phone','t']]
lastin=inbt.groupby('phone').t.max()
ag_first['last_in']=ag_first.phone.map(lastin)
ag_first['repl']=(ag_first.last_in>ag_first.t)
irr=ag_first.groupby('agent').repl.mean()
# positives
acc=t[(t.accepted==1)&t.first_agent.notna()].sort_values('t0').drop_duplicates('phone')
pos=acc.groupby('first_agent').size(); conf=acc[acc.kind=='PITCH'].groupby('first_agent').size()
inv=t[(t.kind=='PITCH')&t.first_agent.notna()].groupby('first_agent').phone.nunique()
# template share
vc=d[d.out&(d.content.str.len()>25)].content.value_counts(); tmpl=set(vc[vc>=3].index)
am=am.assign(tm=am.content.isin(tmpl)&(am.content.str.len()>25))
tshare=am.groupby('agent').tm.mean()
unans=R[R.unanswered].groupby('prev_agent').size()
rows=[]
for ag,g in am.groupby('agent'):
    r=resp[resp.responder==ag].rt_min
    nrep=len(r); un=int(unans.get(ag,0))
    cv=g.phone.nunique()
    rows.append(dict(Agent=ag,msgs=len(g),convs=cv,opened=int(opened.get(ag,0)),replies=nrep,
      med=r.median() if nrep else np.nan,avg=r.mean() if nrep else np.nan,p90=r.quantile(.9) if nrep else np.nan,
      p5=(r<=5).mean() if nrep else np.nan,p15=(r<=15).mean() if nrep else np.nan,p60=(r<=60).mean() if nrep else np.nan,
      unans=un,unrate=un/(nrep+un) if nrep+un else np.nan,irr=irr.get(ag,np.nan),pos=int(pos.get(ag,0)),posrate=pos.get(ag,0)/cv if cv else np.nan,
      inv=int(inv.get(ag,0)),conf=int(conf.get(ag,0)),confrate=conf.get(ag,0)/inv.get(ag,1) if inv.get(ag,0) else 0,
      tshare=tshare.get(ag,np.nan),media=int(g.media.sum()),days=g.date.nunique(),first=g.t.min(),last=g.t.max()))
SC=pd.DataFrame(rows).sort_values('msgs',ascending=False).reset_index(drop=True)
def role(r):
    if r.Agent in TEST: return 'Test / admin account'
    if r.replies>=100: return 'Inbox responder'
    if r.msgs>=300: return 'Outreach / templates'
    return 'Low volume'
SC['role']=SC.apply(role,axis=1)
SC['mpd']=SC.msgs/SC.days
print(SC[['Agent','role','msgs','days','replies','med','p15','unrate','irr','posrate','tshare']].round(2).to_string())
pickle.dump(dict(t=t,SC=SC,PERS=PERS,BL=BL,bb=bb),open('tabs1.pkl','wb'))
print(BL)
