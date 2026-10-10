import requests

url_csv = "https://docs.google.com/spreadsheets/d/1cmG2xWjcbF-76YOcvPKyn1x_BciElT3F3gyFemE_Kq0/export?format=csv&gid=1975448556"
url_gviz = "https://docs.google.com/spreadsheets/d/1cmG2xWjcbF-76YOcvPKyn1x_BciElT3F3gyFemE_Kq0/gviz/tq?tqx=out:csv&gid=1975448556"

print("Trying public CSV export...")
r = requests.get(url_csv)
print(f"Status Code: {r.status_code}")
if r.status_code == 200 and "text/html" not in r.headers.get("Content-Type", ""):
    print("Successfully fetched CSV! First 500 chars:")
    print(r.text[:500])
else:
    print("Content-Type:", r.headers.get("Content-Type"))
    print("First 200 chars of response:", r.text[:200])
