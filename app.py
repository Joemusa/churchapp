import streamlit as st
import pandas as pd
import gspread
from datetime import datetime
import time

st.set_page_config(layout="centered")

# 🔥 HIDE STREAMLIT TOOLBAR (ADDED)
st.markdown("""
    <style>
        [data-testid="stToolbar"] {display: none;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

st.title("⛪ Church Check-In")

# ----------------------------
# CONNECT TO GOOGLE SHEETS
# ----------------------------
client = gspread.service_account_from_dict(
    st.secrets["gcp_service_account"]
)

spreadsheet = client.open("ChurchApp")

members_sheet = spreadsheet.worksheet("Members")
attendance_sheet = spreadsheet.worksheet("Attendance")

# ----------------------------
# LOAD DATA
# ----------------------------
members = pd.DataFrame(members_sheet.get_all_records())
attendance = pd.DataFrame(attendance_sheet.get_all_records())

members.columns = members.columns.str.strip()
attendance.columns = attendance.columns.str.strip()

# Rename for consistency
members = members.rename(columns={
    "First Name?": "First Name",
    "Surname?": "Surname",
    "Cellphone?": "Cellphone",
    "Employment Status?": "Employment Status"
})

# ----------------------------
# CLEAN / STANDARDIZE DATA
# ----------------------------
def safe_string(value):
    if pd.isna(value):
        return ""
    return str(value).strip()

def format_sa_cellphone(cell):
    cell = safe_string(cell)
    digits = "".join(ch for ch in cell if ch.isdigit())

    if not digits:
        return ""

    if digits.startswith("27"):
        return digits
    elif digits.startswith("0"):
        return "27" + digits[1:]
    elif len(digits) == 9:
        return "27" + digits
    else:
        return digits

if "MemberID" in members.columns:
    members["MemberID"] = members["MemberID"].astype(str).str.strip()

if "MemberID" in attendance.columns:
    attendance["MemberID"] = attendance["MemberID"].astype(str).str.strip()

if "Date" in attendance.columns:
    attendance["Date"] = attendance["Date"].astype(str).str.strip()

if "Service" in attendance.columns:
    attendance["Service"] = attendance["Service"].astype(str).str.strip()

if "Cellphone" in members.columns:
    members["Cellphone"] = members["Cellphone"].apply(format_sa_cellphone)

# ----------------------------
# SELECT SERVICE
# ----------------------------
service = st.selectbox(
    "Select Service",
    ["Sunday Service", "Youth Service", "Prayer Meeting", "Special Event"]
)

today = datetime.now().strftime("%Y-%m-%d")
current_time = datetime.now().strftime("%H:%M")

# =========================================================
# 🔥 AUTO FIRST VISIT (GOOGLE FORM SUBMISSIONS)
# =========================================================
for _, member in members.iterrows():

    member_id = safe_string(member["MemberID"])

    existing = attendance[
        attendance["MemberID"] == member_id
    ]

    if existing.empty:

        attendance_sheet.append_row([
            safe_string(today),
            safe_string(current_time),
            "Auto Registration",
            member_id,
            safe_string(member.get("First Name", "")) + " " + safe_string(member.get("Surname", "")),
            "First Visit",
            safe_string(member.get("Province", "")),
            safe_string(member.get("Branch", "")),
            safe_string(member.get("Gender", "")),
            safe_string(member.get("Region", "")),
            safe_string(member.get("Employment Status", "")),
            format_sa_cellphone(member.get("Cellphone", ""))
        ], value_input_option="USER_ENTERED")

# =========================================================
# 🔥 QR CODE CHECK-IN
# =========================================================
query_params = st.query_params
member_qr = query_params.get("member")

if member_qr:

    member_qr = safe_string(member_qr)
    member = members[members["MemberID"] == member_qr]

    if not member.empty:

        member = member.iloc[0]

        # Prevent duplicate check-in for same service & day
        duplicate = attendance[
            (attendance["MemberID"] == member_qr) &
            (attendance["Date"] == today) &
            (attendance["Service"] == service)
        ]

        if not duplicate.empty:
            st.warning("Already checked in today")
            st.stop()

        # Visit count
        history = attendance[attendance["MemberID"] == member_qr]
        visits = len(history) + 1

        if visits == 1:
            status = "First Visit"
        elif visits == 2:
            status = "Second Visit"
        else:
            status = "Regular Member"

        attendance_sheet.append_row([
            safe_string(today),
            safe_string(current_time),
            safe_string(service),
            safe_string(member_qr),
            safe_string(member.get("First Name", "")) + " " + safe_string(member.get("Surname", "")),
            safe_string(status),
            safe_string(member.get("Province", "")),
            safe_string(member.get("Branch", "")),
            safe_string(member.get("Gender", "")),
            safe_string(member.get("Region", "")),
            safe_string(member.get("Employment Status", "")),
            format_sa_cellphone(member.get("Cellphone", ""))
        ], value_input_option="USER_ENTERED")

        st.success(f"Welcome {member['First Name']} ({status})")
        time.sleep(2)
        st.rerun()

# =========================================================
# 🔥 4-DIGIT CHECK-IN
# =========================================================
digits = st.text_input("Enter last 4 digits of your phone")

if digits and len(digits) == 4:

    matches = members[members["Cellphone"].astype(str).str.endswith(digits)].copy()

    if matches.empty:
        st.error("Member not found")
    else:
        matches["FullName"] = matches["First Name"].astype(str) + " " + matches["Surname"].astype(str)

        selected = st.selectbox("Select your name", matches["FullName"])

        if st.button("Confirm Check-In"):

            member = matches[matches["FullName"] == selected].iloc[0]
            member_id = safe_string(member["MemberID"])

            # Prevent duplicates
            duplicate = attendance[
                (attendance["MemberID"] == member_id) &
                (attendance["Date"] == today) &
                (attendance["Service"] == service)
            ]

            if not duplicate.empty:
                st.warning("Already checked in today")
                st.stop()

            # Visit count
            history = attendance[attendance["MemberID"] == member_id]
            visits = len(history) + 1

            if visits == 1:
                status = "First Visit"
            elif visits == 2:
                status = "Second Visit"
            else:
                status = "Regular Member"

            attendance_sheet.append_row([
                safe_string(today),
                safe_string(current_time),
                safe_string(service),
                safe_string(member_id),
                safe_string(member.get("First Name", "")) + " " + safe_string(member.get("Surname", "")),
                safe_string(status),
                safe_string(member.get("Province", "")),
                safe_string(member.get("Branch", "")),
                safe_string(member.get("Gender", "")),
                safe_string(member.get("Region", "")),
                safe_string(member.get("Employment Status", "")),
                format_sa_cellphone(member.get("Cellphone", ""))
            ], value_input_option="USER_ENTERED")

            st.success(f"Check-in successful ({status})")
            time.sleep(2)
            st.rerun()
