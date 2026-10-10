import pandas as pd

excel_path = 'data/documentations for the database.xlsx'
xl = pd.ExcelFile(excel_path)

with open('scratch/db_doc.txt', 'w', encoding='utf-8') as f:
    for sheet in xl.sheet_names:
        f.write(f"\n=========================================\n")
        f.write(f"SHEET: {sheet}\n")
        f.write(f"=========================================\n")
        df = pd.read_excel(excel_path, sheet_name=sheet)
        f.write(df.to_string() + "\n")

print("Dumped db documentation to scratch/db_doc.txt")
