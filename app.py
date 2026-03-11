import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

st.title("Church Member Verification")

digits = st.text_input("Enter the last 4 digits of your cellphone number")

# Create credentials once
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)

client = gspread.authorize(creds)

sheet = client.open_by_key(
    "1k2mBMHROvmht5aaQjPQenHtwWVl9Y_h-gey5EIIAwLQ"
).worksheet("Sheet1")

if st.button("Submit"):

    if len(digits) == 4 and digits.isdigit():

        sheet.append_row([
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            digits
        ])

        st.success("Thank you. Your information was captured.")

    else:
        st.error("Please enter exactly 4 digits.")
