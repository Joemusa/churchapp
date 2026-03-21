import streamlit as st
import pandas as pd
import gspread
from datetime import datetime
from zoneinfo import ZoneInfo
import time

st.set_page_config(page_title="Church Check-In", layout="centered")

st.markdown("""
    <style>
        [data-testid="stToolbar"] {display: none;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        .block-container {padding-top: 1.5rem; padding-bottom: 1.5rem;}
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
# HELPERS
# ----------------------------
def safe_string(value):
    if pd.isna(value):
        return ""
    return str(value).strip()

def digits_only(value):
    return "".join(ch for ch in safe_string(value) if ch.isdigit())

def format_sa_cellphone(cell):
    digits = digits_only(cell)

    if not digits:
        return ""

    if digits.startswith("27") and len(digits) >= 11:
        return digits
    if digits.startswith("0") and len(digits) == 10:
        return "27" + digits[1:]
    if len(digits) == 9:
        return "27" + digits

    return digits

def get_sa_datetime():
    sa_now = datetime.now(ZoneInfo("Africa/Johannesburg"))
    return sa_now.strftime("%Y-%m-%d"), sa_now.strftime("%H:%M")

def get_visit_status(history_count):
    visits = history_count + 1
    if visits == 1:
        return "First Visit"
    elif visits == 2:
        return "Second Visit"
    return "Regular Member"

def load_members():
    df = pd.DataFrame(members_sheet.get_all_records())

    if df.empty:
        return pd.DataFrame(columns=[
            "MemberID", "First Name", "Surname", "Cellphone",
            "Province", "Branch", "Gender", "Region", "Employment Status"
        ])

    df.columns = df.columns.str.strip()

    df = df.rename(columns={
        "First Name?": "First Name",
        "Surname?": "Surname",
        "Cellphone?": "Cellphone",
        "Employment Status?": "Employment Status"
    })

    if "MemberID" in df.columns:
        df["MemberID"] = df["MemberID"].astype(str).str.strip()
    else:
        df["MemberID"] = ""

    if "First Name" not in df.columns:
        df["First Name"] = ""
    if "Surname" not in df.columns:
        df["Surname"] = ""
    if "Cellphone" not in df.columns:
        df["Cellphone"] = ""
    if "Province" not in df.columns:
        df["Province"] = ""
    if "Branch" not in df.columns:
        df["Branch"] = ""
    if "Gender" not in df.columns:
        df["Gender"] = ""
    if "Region" not in df.columns:
        df["Region"] = ""
    if "Employment Status" not in df.columns:
        df["Employment Status"] = ""

    df["Cellphone"] = df["Cellphone"].apply(format_sa_cellphone)
    df["FullName"] = (
        df["First Name"].astype(str).str.strip() + " " +
        df["Surname"].astype(str).str.strip()
    ).str.strip()

    return df

def load_attendance():
    df = pd.DataFrame(attendance_sheet.get_all_records())

    if df.empty:
        return pd.DataFrame(columns=[
            "Date", "Time", "Service", "MemberID", "Name", "Status",
            "Province", "Branch", "Gender", "Region", "Employment Status", "Contact"
        ])

    df.columns = df.columns.str.strip()

    if "MemberID" in df.columns:
        df["MemberID"] = df["MemberID"].astype(str).str.strip()
    else:
        df["MemberID"] = ""

    if "Date" in df.columns:
        df["Date"] = df["Date"].astype(str).str.strip()
    else:
        df["Date"] = ""

    if "Service" in df.columns:
        df["Service"] = df["Service"].astype(str).str.strip()
    else:
        df["Service"] = ""

    return df

def find_member_by_phone(members_df, phone_input):
    formatted_input = format_sa_cellphone(phone_input)

    if not formatted_input:
        return pd.DataFrame()

    exact_matches = members_df[members_df["Cellphone"] == formatted_input].copy()
    if not exact_matches.empty:
        return exact_matches

    raw_digits = digits_only(phone_input)
    if raw_digits:
        fallback_matches = members_df[
            members_df["Cellphone"].astype(str).str.endswith(raw_digits[-9:])
        ].copy()
        return fallback_matches

    return pd.DataFrame()

def append_attendance(member_row, selected_service):
    attendance_df = load_attendance()
    today, current_time = get_sa_datetime()
    member_id = safe_string(member_row.get("MemberID", ""))

    duplicate = attendance_df[
        (attendance_df["MemberID"] == member_id) &
        (attendance_df["Date"] == today) &
        (attendance_df["Service"] == selected_service)
    ]

    if not duplicate.empty:
        return False, "Already checked in today"

    history = attendance_df[attendance_df["MemberID"] == member_id]
    status = get_visit_status(len(history))

    full_name = safe_string(member_row.get("FullName", ""))
    if not full_name:
        full_name = (
            safe_string(member_row.get("First Name", "")) + " " +
            safe_string(member_row.get("Surname", ""))
        ).strip()

    attendance_sheet.append_row([
        safe_string(today),
        safe_string(current_time),
        safe_string(selected_service),
        member_id,
        full_name,
        status,
        safe_string(member_row.get("Province", "")),
        safe_string(member_row.get("Branch", "")),
        safe_string(member_row.get("Gender", "")),
        safe_string(member_row.get("Region", "")),
        safe_string(member_row.get("Employment Status", "")),
        format_sa_cellphone(member_row.get("Cellphone", ""))
    ], value_input_option="USER_ENTERED")

    return True, status

# ----------------------------
# LOAD DATA
# ----------------------------
members = load_members()

# ----------------------------
# SELECT SERVICE
# ----------------------------
service = st.selectbox(
    "Select Service",
    ["Sunday Service", "Youth Service", "Prayer Meeting", "Special Event"]
)

st.write("Scan the church QR code, enter your cellphone number, then tap Present.")

phone_input = st.text_input(
    "Enter your cellphone number",
    placeholder="Example: 0834123456 or 27834123456"
)

if phone_input:
    matches = find_member_by_phone(members, phone_input)

    if matches.empty:
        st.error("Member not found")
    else:
        if len(matches) == 1:
            member = matches.iloc[0]

            st.success(f"Welcome {safe_string(member.get('FullName', 'Member'))}")

            if st.button("Present", use_container_width=True):
                success, result = append_attendance(member, service)

                if success:
                    st.success(f"Check-in successful ({result})")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.warning(result)

        else:
            st.warning("More than one member matched this number. Please select your name.")
            selected = st.selectbox("Select your name", matches["FullName"].tolist())

            if st.button("Present", use_container_width=True):
                member = matches[matches["FullName"] == selected].iloc[0]
                success, result = append_attendance(member, service)

                if success:
                    st.success(f"Check-in successful ({result})")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.warning(result)
