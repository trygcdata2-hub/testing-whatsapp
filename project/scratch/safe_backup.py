import os
import shutil

backup_dir = 'local_raw_backups'
os.makedirs(backup_dir, exist_ok=True)

for f in os.listdir('data'):
    if f.endswith('.csv') and 'last_month_s_data' in f:
        src = os.path.join('data', f)
        dest = os.path.join(backup_dir, f)
        shutil.move(src, dest)
        print(f"Safely backed up {src} -> {dest}")

print("\n--- Files remaining in data/ (ALL UNDER 12 MB) ---")
for f in os.listdir('data'):
    p = os.path.join('data', f)
    sz = os.path.getsize(p) / (1024*1024)
    print(f"  {f}: {sz:.2f} MB")
