import pandas as pd

d = pd.read_csv('data/last_month_s_data.csv', dtype=str, encoding='utf-8-sig').drop_duplicates()
d = d[(d.isSystem != '1') & (d.phone.notna()) & (d.isFromMe == '1')]

def mask_phone(p):
    p = str(p)
    if len(p) > 4:
        return p[:-4] + '****'
    return p

d['masked_phone'] = d['phone'].apply(mask_phone)

anydesk = d[d.userName == 'original whatsapp'].sample(10, random_state=42)[['createdAt', 'masked_phone', 'whatsappAccId', 'userName', 'content']]
platform = d[d.userName != 'original whatsapp'].sample(10, random_state=42)[['createdAt', 'masked_phone', 'whatsappAccId', 'userName', 'content']]

with open('scratch_samples.txt', 'w', encoding='utf-8') as f:
    f.write('--- ANYDESK SAMPLES ---\n')
    for _, row in anydesk.iterrows():
        c = str(row['content']).replace('\n', ' ')
        f.write(f"- **Line {row['whatsappAccId']}** ({row['createdAt']}): `{c[:150]}`\n")

    f.write('\n--- PLATFORM SAMPLES ---\n')
    for _, row in platform.iterrows():
        c = str(row['content']).replace('\n', ' ')
        f.write(f"- **Line {row['whatsappAccId']} ({row['userName']})** ({row['createdAt']}): `{c[:150]}`\n")
