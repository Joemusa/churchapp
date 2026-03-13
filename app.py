import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime

st.set_page_config(layout="centered")

st.markdown(
    "<h1 style='text-align:center;color:#2E86C1;'>Church Check-In</h1>",
    unsafe_allow_html=True
)

st.markdown(
    "<h3 style='text-align:center;'>Enter the last 4 digits of your cellphone number</h3>",
    unsafe_allow_html=True
)

# Google API scope
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Authenticate
creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)

client = gspread.authorize(creds)

# Open spreadsheet
spreadsheet = client.open_by_key("1k2mBMHROvmht5aaQjPQenHtwWVl9Y_h-gey5EIIAwLQ")

members_sheet = spreadsheet.worksheet("Members")
attendance_sheet = spreadsheet.worksheet("Attendance")

# Load members
members_data = members_sheet.get_all_records()
members_df = pd.DataFrame(members_data)

# Clean column names
members_df.columns = members_df.columns.str.strip()

# Ensure phone numbers are strings
members_df["Cellphone?"] = members_df["Cellphone?"].astype(str)

# Load attendance history
attendance_data = attendance_sheet.get_all_records()
attendance_df = pd.DataFrame(attendance_data)

# User input
digits = st.text_input("", max_chars=4, placeholder="Enter 4 digits")

if digits:

    if len(digits) == 4:

        # Search by last 4 digits
        matches = members_df[members_df["Cellphone?"].str.endswith(digits)]

        if len(matches) == 0:

            st.warning("Member not found. Please register using the visitor form.")

        else:

            # Create full name
            matches["FullName"] = matches["First Name?"] + " " + matches["Surname?"]

            st.write("Please confirm your name")

            selected_name = st.selectbox("Select your name", matches["FullName"])

            if st.button("Confirm Check-In"):

                member = matches[matches["FullName"] == selected_name].iloc[0]

                # Count previous visits
                if not attendance_df.empty:

                    member_history = attendance_df[
                        attendance_df["MemberID"] == member["MemberID"]
                    ]

                    visit_count = len(member_history) + 1

                else:
                    visit_count = 1

                if visit_count == 1:
                    status = "First Visit"
                elif visit_count == 2:
                    status = "Second Visit"
                else:
                    status = "Regular Member"

                # Save attendance
                row = [
                    datetime.now().strftime("%Y-%m-%d"),
                    datetime.now().strftime("%H:%M"),
                    str(member["MemberID"]),
                    member["First Name?"] + " " + member["Surname?"],
                    status
                ]

                attendance_sheet.append_row(row)

                st.success(f"Attendance recorded. Status: {status}")

    else:
        st.error("Please enter exactly 4 digits.")
