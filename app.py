import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime

st.title("Church Check-In")

# Google API scope
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Authenticate using Streamlit secrets
creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)

client = gspread.authorize(creds)

# Open spreadsheet
spreadsheet = client.open_by_key("1k2mBMHROvmht5aaQjPQenHtwWVl9Y_h-gey5EIIAwLQ")

members_sheet = spreadsheet.worksheet("Members")
attendance_sheet = spreadsheet.worksheet("Attendance")

# Load members database
members_data = members_sheet.get_all_records()
members_df = pd.DataFrame(members_data)

# convert Last4 column to string
members_df["Last4"] = members_df["Last4"].astype(str)

# Load attendance history
attendance_data = attendance_sheet.get_all_records()
attendance_df = pd.DataFrame(attendance_data)

# Member enters digits
digits = st.text_input("Enter the last 4 digits of your cellphone number")

if digits and len(digits) == 4:

    matches = members_df[members_df["Last4"] == digits]

    if len(matches) == 0:

        st.warning("Member not found. Please register using the visitor form.")

    else:

        st.write("Please confirm your name")

        selected_name = st.selectbox("Select your name", matches["Name"])

        if st.button("Confirm Check-In"):

            member = matches[matches["Name"] == selected_name].iloc[0]

            # Count previous visits
            member_history = attendance_df[
                attendance_df["MemberID"] == member["MemberID"]
            ]

            visit_count = len(member_history) + 1

            if visit_count == 1:
                status = "First Visit"
            elif visit_count == 2:
                status = "Second Visit"
            else:
                status = "Regular Member"

            # Record attendance
            row = [
                    datetime.now().strftime("%Y-%m-%d"),
                    datetime.now().strftime("%H:%M"),
                    str(member["MemberID"]),
                    member["Name"],
                    status
                ]

attendance_sheet.append_row(row)

st.success(f"Attendance recorded. Status: {status}")
else:
    st.error("Please enter exactly 4 digits.")
