Run order: prep.py -> analysis.py -> tables.py -> tables2.py -> build.py
Paths are hard-coded (/home/claude, /mnt/user-data). Change them before running locally.
tables2.py re-reads tables.py via exec(); intermediate state is stored as .pkl files.
See PROJECT_HANDOFF.md section 4 for what each script does and section 4.6 for known issues.
