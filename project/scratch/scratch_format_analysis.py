import json

with open('google_sheets_structure.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Spreadsheet Title: {data['title']}")
print(f"Total Worksheets: {data['total_worksheets']}\n")

with open('sheets_analysis.txt', 'w', encoding='utf-8') as out:
    out.write(f"Spreadsheet: {data['title']}\n")
    out.write(f"Total Sheets: {data['total_worksheets']}\n\n")
    
    for s in data['sheets']:
        out.write(f"==================================================\n")
        out.write(f"SHEET: '{s['title']}' (id: {s['id']})\n")
        out.write(f"Rows: {s['rows']}, Columns: {s['cols']}\n")
        out.write(f"Headers: {s['header']}\n")
        out.write("Sample Rows:\n")
        for idx, r in enumerate(s['sample_rows']):
            out.write(f"  Row {idx+1}: {r}\n")
        out.write("\n")

print("Generated sheets_analysis.txt")
