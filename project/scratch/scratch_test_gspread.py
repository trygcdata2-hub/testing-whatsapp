import sys
import json

try:
    import gspread
    from google.oauth2.service_account import Credentials
    print("gspread and google.oauth2 are available.")
except ImportError as e:
    print(f"ImportError: {e}")
