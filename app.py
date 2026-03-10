import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

st.title("Church Member Verification")

digits = st.text_input("Enter the last 4 digits of your cellphone number")

if st.button("Submit"):

    if len(digits) == 4 and digits.isdigit():

        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]

        creds = ServiceAccountCredentials.from_json_keyfile_name(
            "credentials.json", scope
        )

        client = gspread.authorize(creds)

        sheet = client.open_by_key("https://docs.google.com/spreadsheets/d/1k2mBMHROvmht5aaQjPQenHtwWVl9Y_h-gey5EIIAwLQ/edit?gid=0#gid=0").sheet1

        sheet.append_row([datetime.now().strftime("%Y-%m-%d %H:%M"), digits])

        st.success("Thank you. Your information was captured.")

    else:
        st.error("Please enter exactly 4 digits.")
