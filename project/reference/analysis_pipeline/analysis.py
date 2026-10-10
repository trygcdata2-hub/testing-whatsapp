import pandas as pd, numpy as np, re, unicodedata, pickle
d=pd.read_pickle('/home/claude/clean.pkl')
END=d.t.max(); START=d.t.min()

def norm(s):
    s=unicodedata.normalize('NFKC',str(s)).lower()
    s=re.sub('[\u064b-\u0652\u0640]','',s)
    s=re.sub('[أإآ]','ا',s).replace('ى','ي').replace('ة','ه')
    return s
d['n']=d.content.map(norm)

# ---------- country ----------
def country(p):
    if p.startswith('966'): return 'KSA'
    if p.startswith('965'): return 'Kuwait'
    if p.startswith('971'): return 'UAE'
    if p.startswith('974'): return 'Qatar'
    if p.startswith('20') and len(p)==12: return 'Egypt'
    if p.startswith('201'): return 'Egypt'
    return 'Other'
d['country']=d.phone.map(country)

# ---------- runs ----------
d['newrun']=(d.phone!=d.phone.shift())|(d.out!=d.out.shift())
d['run']=d.newrun.cumsum()
CLOSE=re.compile(r'^(?:[\s\W_]|شكرا|شكراا*|شكرن|تسلم\w*|يعطيك العافيه|الله يعافيك|الله يسلمك|تمام|اوكي|اوك|ok|okay|thanks?|thank you|مشكور\w*|يسلمو|بارك الله فيك|الله يخليك|عفوا|حاضر|يارب|امين|تم|اكيد|بالتوفيق|ما قصرت\w*|[\U0001F300-\U0001FAFF\u2600-\u27BF])+$')
d['closer']=((d.n.str.len()<=30)&d.n.map(lambda x: bool(CLOSE.match(x)) if x.strip() else False))|(d.type=='stickerMessage')
runs=d.groupby('run').agg(phone=('phone','first'),out=('out','first'),t0=('t','first'),t1=('t','last'),nmsg=('t','size'),
    first_text=('content','first'),closer_all=('closer','all'),country=('country','first'),
    first_agent=('agent',lambda s: next((x for x in s if x),None)),
    text=('content',lambda s:'\n'.join(s)),invflag=('inv','any'),media=('media','sum')).reset_index()
runs['agent']=runs.first_agent
runs['next_t']=runs.t0.shift(-1); runs['next_phone']=runs.phone.shift(-1); runs['next_out']=runs.out.shift(-1)
runs['next_agent']=runs.first_agent.shift(-1)

# last agent that wrote before each run (within phone)
runs['last_agent']=runs.groupby('phone').agent.ffill()
runs['prev_agent']=runs.groupby('phone').last_agent.shift(1)
runs.loc[runs.phone!=runs.phone.shift(1),'prev_agent']=None
# ---------- Response events ----------
inb=runs[~runs.out].copy()
ok=(inb.next_phone==inb.phone)&(inb.next_out==True)
inb['replied']=ok.astype(int)
inb['replied_at']=inb.next_t.where(ok)
inb['rt_min']=(inb.replied_at-inb.t0).dt.total_seconds()/60
inb['responder']=np.where(ok,inb.next_agent.fillna('Phone (unattributed)'),None)
inb['late']=inb.rt_min>1440
inb['pending']=(~ok)&(inb.t0>END-pd.Timedelta(hours=3))
inb['unanswered']=((~ok)|inb.late)&(~inb.pending)&(~inb.closer_all)
RE=inb[['phone','t0','nmsg','first_text','closer_all','prev_agent','replied','replied_at','rt_min','responder','late','pending','unanswered','country']].rename(columns={'t0':'inbound_at','nmsg':'inbound_msgs','closer_all':'closer_only'})
RE['hour']=RE.inbound_at.dt.hour; RE['date']=RE.inbound_at.dt.date
print('inbound bursts',len(RE),'replied',RE.replied.sum(),'unanswered',RE.unanswered.sum(),'pending',RE.pending.sum(),'closer only',RE.closer_only.sum())

# ---------- Turns ----------
o=d[d.out].copy()
o['ag_ff']=o.groupby('run').agent.ffill()
prevag=o.groupby('run').ag_ff.shift(1)
gap=(o.t-o.groupby('run').t.shift(1)).dt.total_seconds()/60
chg=o.agent.notna()&prevag.notna()&(o.agent!=prevag)
o['newturn']=o.newrun|chg|(gap>30)
o['turn']=o.newturn.cumsum()
out=o.groupby('turn').agg(run=('run','first'),phone=('phone','first'),t0=('t','first'),t1=('t','last'),nmsg=('t','size'),
    first_text=('content','first'),country=('country','first'),
    first_agent=('agent',lambda s: next((x for x in s if isinstance(x,str)),None)),
    text=('content',lambda s:'\n'.join(s)),invflag=('inv','any'),media=('media','sum')).reset_index()
out['last_in_run']=out.run!=out.run.shift(-1)
inb_i=runs[~runs.out].set_index('run')
out['in_run']=out.run+1
out=out.join(inb_i[['t0','text','nmsg']].rename(columns={'t0':'in_t','text':'in_text','nmsg':'in_n'}),on='in_run')
out['has_next']=out.last_in_run&out.in_t.notna()&(out.phone==out.phone)
out.loc[~out.has_next,['in_t','in_text','in_n']]=[pd.NaT,None,np.nan]
out['reply_delay_min']=(out.in_t-out.t1).dt.total_seconds()/60
out['replied']=(out.has_next&(out.reply_delay_min<=1440)).astype(int)

def rx(p): return re.compile(p)
ACC=rx(r'(?:^|\s)(?:تم|تمام|اوكي|اوكيه|اوك|ok|okay|okey|ابشر|ابشري|مناسب|مناسبه|ايوه|ايوا|اكيد|yes|yep|موافق|موافقه|يناسبني)(?:\s|$|[!.،,])|👍|✅')
NEG=rx(r'(?:^|\s)(?:لا|ما|مو|مب|مش|no)(?:\s|$)')
DEC=rx(r'اعتذر|ما اقدر|مااقدر|ما اقدر|مشغول|مو متاح|غير متاح|مب متاح|لا شكرا|مو مهتم|غير مهتم|ما ابغي|ما ابي|sorry|not available|not interested|لا استطيع|ظروف|مسافر|سفر')
PAY=rx(r'مدفوع|دفع|ادفع|المبلغ|تكلفه|تكلفة|سعر|paid|payment|fee|rate card|ريت|اعلان\w* ب|مقابل مادي|عمولة|عموله|كم تدفع|التسعير|بكم')
def accepted(t):
    if not isinstance(t,str): return 0
    msgs=[norm(x) for x in t.split('\n')]
    for m in msgs[:3]:
        if len(m)<=40 and ACC.search(' '+m+' ') and not NEG.search(m): return 1
    return 0
out['accepted']=out.in_text.map(accepted)*out.replied
out['declined']=out.in_text.map(lambda t: int(isinstance(t,str) and bool(DEC.search(norm(t))))) * out.replied
out['payment_q']=out.in_text.map(lambda t: int(isinstance(t,str) and bool(PAY.search(norm(t))))) * out.replied
out.loc[out.declined==1,'accepted']=0

LOG=rx(r'العنوان|رقم الطلب|رقم الشحنه|تتبع|التوصيل|ملاحظات مهمه|يرجي الالتزام|لا يقبل النشر|مواعيد الزياره|رابط الموقع|maps\.|goo\.gl|share\.google|بريف|تفاصيل الزياره|يرجي ابلاغنا|تفاصيل العنوان|كود الخصم|الكود|اسم الحساب|امثله للتغطيات|الجو العام للمكان|يرجي ارسال')
POST=rx(r'تقييم|ريبوست|اعاده نشر|ستوري|سناب|ريل|تغطيه|اسكرين|اليوم زيارتك|شكرا لزيارتك|بعد الزياره|يرجي النشر|رابط النشر|انشر|نشرت')
CONF=rx(r'تم تاكيد|تاكيد حجزك|تاكيد موعد|تم حجز|تم تسجيلك|تم اضافتك|تم اضافه اسمك|موعد زيارتك|حجزك')
PIT=rx(r'تفوت|متحمسين|جديد|عرض|تجربه|زياره|حمله|دعوه|ندعوك|ندعوكم|يسعدنا|نتشرف|اكدلي|بتناسب|نضيفك|حياك|تناسبك|يناسبك|exclusive|invite|ضيوفنا|حابين تكون|ارسل.{0,12}تم|ابعت.{0,12}تم|تحب تجرب|حبيت اسالك|نبي نتعاون|تعاون|حمله|حملة')
REM=rx(r'بانتظار|طمنا|تذكير|ننتظر|هل ما زلت|لسه|عساك|اخبارك|طمني|ردك|تاكيدك|بتشرفنا|ما وصلنا|متواجد')
def kind(r):
    t=norm(r.text); L=len(t)
    if r.invflag: return 'PITCH'
    if L>=600 or LOG.search(t): 
        return 'LOGISTICS' if not PIT.search(t[:200]) or L>=600 else 'PITCH'
    if CONF.search(t): return 'CONFIRM'
    if POST.search(t): return 'POST_VISIT'
    if PIT.search(t) and L>=40: return 'PITCH'
    if REM.search(t): return 'REMINDER'
    return 'CHAT'
out['kind']=out.apply(kind,axis=1)
print(out.kind.value_counts())

BR=[('Dopamine','دوبامين|dopamine'),('Creation Burger','creation burger|كرييشن|كريشن'),('Bloomore / BMORE','bloomore|bmore|بلومور'),('Shrimp Zone','شرمب زون|shrimp zone'),('Jones the Grocer','jones'),('Jade Room','jade room'),('Pilatta','pilatta'),('Triowalite','triowalite'),('Society by Sofleur','sofleur|سوفلور|سوسايتي'),('Dr. Scent','dr scent|dr\\. scent|دكتور سنت|dr.scent'),('Black Tap','black tap'),('Tashas','tasha'),('Pizzarati','pizzarati'),('SO by Sora','sora'),('Brands For Less','brands for less'),('FNP','fnp'),('Table to','table to'),('Riyadh book launch','كتاب الرياض'),('Saudi National Day','اليوم الوطني'),('Brunch & Cake','brunch & cake|brunch and cake')]
BRC=[(b,re.compile(p)) for b,p in BR]
def brand_of(t):
    t=norm(t)
    for b,p in BRC:
        if p.search(t): return b
    return None
out['brand']=out.text.map(brand_of)
tb=out.dropna(subset=['brand']).groupby('phone').brand.agg(lambda s:s.value_counts().index[0])
out['brand']=out.brand.fillna(out.phone.map(tb)).fillna('Unknown')

# features
EMO=rx(r'^[\s]*[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B50\u2728\u2764]')
GREET=rx(r'^[\W_]*(?:هلا|مرحبا|اهلين|اهلا|السلام|حياك|مساء|صباح)')
GULF=rx(r'(?:^|\s)(?:شو|وش|ايش|حياك|ابغي|ابي|ابغا|تبي|تبغي|زين|وايد|شلونك|شخبارك|عساك|شرايك|رايك|نبي|نبغي|بنحب|مب|حبيت|ودك|ودي|يبغي|هلا|اهلين|يالله|ابشر)(?:\s|$)')
URG=rx(r'محدود|لفتره|الان فقط|اخر فرصه|لا تفوت|ما تفوت|تفوتك|ينتهي|مقاعد|المقاعد|قبل ان')
BEN=rx(r'ضيف|ضيوف|مشروب|قهوه|كاترينق|مجان|علينا|هديه|منتجات|وجبه|فطور|عشاء|غداء|خصم|كود')
TIM=rx(r'اليوم|بكره|بكرا|غدا|السبت|الاحد|الاثنين|الثلاثاء|الاربعاء|الخميس|الجمعه|صباح|مساء|الساعه|\d{1,2}[:.]\d{2}|\d\s*(?:ص|م|pm|am)|موعد')
TAM=rx(r'(?:ارسل|ابعت|رد|ارسلي|ابعتلنا|ارسلنا|send).{0,14}تم')
def feats(r):
    t=norm(r.text); first=norm(r.first_text); last=norm(r.text.split('\n')[-1])
    L=len(r.text)
    return pd.Series(dict(chars=L,starts_emoji=int(bool(EMO.match(r.first_text))),starts_greeting=int(bool(GREET.match(first))),
      cta_tam=int(bool(TAM.search(t))),cta_question=int(last.strip().endswith(('؟','?'))),urgency=int(bool(URG.search(t))),benefit=int(bool(BEN.search(t))),
      gulf=int(bool(GULF.search(t))),has_q=int('؟' in t or '?' in t),proposes_time=int(bool(TIM.search(t))),
      closed_q=int(('؟' in t or '?' in t) and L<=80)))
F=out.apply(feats,axis=1)
out=pd.concat([out.reset_index(drop=True),F.drop(columns=[]).reset_index(drop=True)],axis=1)
out['len_bucket']=pd.cut(out.chars,[-1,20,45,90,200,10**6],labels=['≤20','21-45','46-90','91-200','200+']).astype(str)
out['hour']=out.t0.dt.hour
out['ask_turn']=out.kind.isin(['PITCH','REMINDER','CHAT']).astype(int)
out['agent']=out.first_agent
out['sent_at']=out.t0
out['date']=out.t0.dt.date
tk=out.first_text.map(lambda s: re.sub(r'[^\w\s]','',norm(s))[:45].strip())
vc=tk.value_counts()
out['template_key']=tk.where(tk.map(vc)>=15)
out.loc[out.first_text.str.len()<=25,'template_key']=None
out.to_pickle('/home/claude/turns.pkl'); RE.to_pickle('/home/claude/re.pkl'); runs.to_pickle('/home/claude/runs.pkl'); d.to_pickle('/home/claude/d2.pkl')
base=out[out.ask_turn==1].groupby('kind').agg(turns=('replied','size'),rep=('replied','mean'),acc=('accepted','mean'))
print(base)
print(out.brand.value_counts().head(15))
