import pandas as pd

d = pd.read_csv('data/last_month_s_data.csv', dtype=str, encoding='utf-8-sig').drop_duplicates()

null_phone = d[d['phone'].isna()].head(3)[['createdAt', 'userName', 'whatsappAccId', 'phone', 'content']]
null_line = d[d['whatsappAccId'].isna()].head(3)[['createdAt', 'userName', 'whatsappAccId', 'phone', 'content']]

with open('scratch_nulls.txt', 'w', encoding='utf-8') as f:
    f.write('--- PHONE (Contact) IS NULL ---\n')
    for _, row in null_phone.iterrows():
        c = str(row['content']).replace('\n', ' ')
        f.write(f"Time: {row['createdAt']} | Line: {row['whatsappAccId']} | User: {row['userName']} | Phone: {row['phone']}\nMsg: {c[:150]}\n-\n")

    f.write('\n--- WHATSAPPACCID (Our Line) IS NULL ---\n')
    for _, row in null_line.iterrows():
        c = str(row['content']).replace('\n', ' ')
        f.write(f"Time: {row['createdAt']} | Line: {row['whatsappAccId']} | User: {row['userName']} | Phone: {row['phone']}\nMsg: {c[:150]}\n-\n")
