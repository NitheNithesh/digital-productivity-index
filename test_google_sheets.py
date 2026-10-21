
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Google Sheets Connection Test")

st.title("DPI - Google Sheets Connection Test")

try:
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
    ]

    credentials = Credentials.from_service_account_info(
        {
            **dict(st.secrets["gcp_service_account"]),
        },
        scopes=scopes,
    )

    client = gspread.authorize(credentials)

    spreadsheet = client.open_by_key(
        st.secrets["spreadsheet_id"]
    )

    worksheet = spreadsheet.worksheet("Responses")

    st.success("Google Sheets connection successful!")
    st.write("Spreadsheet:", spreadsheet.title)
    st.write("Worksheet:", worksheet.title)
    st.write("Current number of rows:", worksheet.row_count)

except Exception as e:
    st.error("Google Sheets connection failed.")
    st.code(f"{type(e).__name__}: {e}")
