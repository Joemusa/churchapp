import streamlit as st
import gspread
import pandas as pd
from datetime import datetime
import time

st.set_page_config(layout="centered")

st.markdown(
    "<h1 style='text-align:center;color:#2E86C1;'>Church Check-In</h1>",
    unsafe_allow_html=True
)

st.markdown(
    "<h3 style='text-align:center;'>Enter the last 4 digits OR scan your QR code</h3>",
    unsafe_allow_html=True
)

# Select church service
service = st.selectbox(
    "Select Service",
    ["Sunday Service", "Youth Service", "Prayer Meeting", "Special Event"]
)

# Authenticate with Google
client = gspread.service_account_from_dict(
    st.secrets["gcp_service_account"]
)

# Open spreadsheet
spreadsheet = client.open("ChurchApp")

members_sheet = spreadsheet.worksheet("Members")
attendance_sheet = spreadsheet.worksheet("Attendance")

# Load members
members_data = members_sheet.get_all_records()
members_df = pd.DataFrame(members_data)

members_df.columns = members_df.columns.str.strip()
members_df["Cellphone?"] = members_df["Cellphone?"].astype(str)

# Load attendance history
attendance_data = attendance_sheet.get_all_records()
attendance_df = pd.DataFrame(attendance_data)

today = datetime.now().strftime("%Y-%m-%d")

# -----------------------------
# QR CODE CHECK-IN
# -----------------------------
query_params = st.query_params
member_qr = query_params.get("member")

if member_qr:

    member = members_df[members_df["MemberID"] == member_qr]

    if not member.empty:

        member = member.iloc[0]

        # Duplicate check
        duplicate = attendance_df[
            (attendance_df["MemberID"] == member_qr) &
            (attendance_df["Date"] == today) &
            (attendance_df["Service"] == service)
        ]

        if not duplicate.empty:
            st.warning("You already checked in for this service.")
            time.sleep(2)
            st.rerun()

        # Visit count
        member_history = attendance_df[
            attendance_df["MemberID"] == member_qr
        ]

        visit_count = len(member_history) + 1

        if visit_count == 1:
            status = "First Visit"
        elif visit_count == 2:
            status = "Second Visit"
        else:
            status = "Regular Member"

        row = [
            today,
            datetime.now().strftime("%H:%M"),
            service,
            member_qr,
            member["First Name?"] + " " + member["Surname?"],
            status
        ]

        attendance_sheet.append_row(row)

        st.success("QR Check-in successful!")

        time.sleep(2)
        st.rerun()

# -----------------------------
# DIGITS CHECK-IN
# -----------------------------

digits = st.text_input(
    "",
    max_chars=4,
    placeholder="Enter 4 digits",
    key="digits_input"
)

if digits:

    if len(digits) == 4:

        matches = members_df[members_df["Cellphone"].str.endswith(digits)]

        if len(matches) == 0:

            st.warning("Member not found. Please register using the visitor form.")

        else:

            matches = matches.copy()
            matches["FullName"] = matches["First Name?"] + " " + matches["Surname?"]

            st.write("Please confirm your name")

            selected_name = st.selectbox(
                "Select your name",
                matches["FullName"]
            )

            if st.button("Confirm Check-In"):

                member = matches[matches["FullName"] == selected_name].iloc[0]

                duplicate = attendance_df[
                    (attendance_df["MemberID"] == member["MemberID"]) &
                    (attendance_df["Date"] == today) &
                    (attendance_df["Service"] == service)
                ]

                if not duplicate.empty:

                    st.warning("You have already checked in for this service.")
                    time.sleep(2)
                    st.rerun()

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

                row = [
                    today,
                    datetime.now().strftime("%H:%M"),
                    service,
                    str(member["MemberID"]),
                    member["First Name?"] + " " + member["Surname?"],
                    status
                ]

                attendance_sheet.append_row(row)

                st.success(f"Attendance recorded for {service}. Status: {status}")

                time.sleep(2)

                st.rerun()

    else:
        st.error("Please enter exactly 4 digits.")
