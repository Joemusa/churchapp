import pandas as pd
import gspread
import qrcode
import os
from google.oauth2.service_account import Credentials

# ----------------------------
# CONFIG
# ----------------------------
APP_URL = "https://your-app-name.streamlit.app"
OUTPUT_FOLDER = "member_qrcodes"

# ----------------------------
# GOOGLE SHEETS CONNECTION
# ----------------------------
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_file("service_account.json", scopes=scope)
client = gspread.authorize(creds)

spreadsheet = client.open("ChurchApp")
members_sheet = spreadsheet.worksheet("Members")

members = pd.DataFrame(members_sheet.get_all_records())
members.columns = members.columns.str.strip()

members = members.rename(columns={
    "First Name?": "First Name",
    "Surname?": "Surname"
})

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

for _, row in members.iterrows():
    member_id = str(row["MemberID"]).strip()
    first_name = str(row.get("First Name", "")).strip()
    surname = str(row.get("Surname", "")).strip()

    qr_link = f"{APP_URL}/?member={member_id}"

    img = qrcode.make(qr_link)

    filename = f"{first_name}_{surname}_{member_id}.png".replace(" ", "_")
    img.save(os.path.join(OUTPUT_FOLDER, filename))

print("QR codes generated successfully.")
