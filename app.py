import streamlit as st
import gspread
import pandas as pd
import plotly.express as px
from google.oauth2 import service_account
from io import BytesIO
import json

st.set_page_config(page_title="Dashboard IT Asset", layout="wide")
st.title("Dashboard IT Asset Umara Group")

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

SHEET_ID = "1msf4IK1ZJReQl5f_6VRbVCsGiJXcHUHENto1DqrQwkY"
JSON_FILE = "dashboard-laptop-it-92f648a3958c.json"

@st.cache_resource
def get_client():
    try:
        info = json.loads(st.secrets["gcp_json"])
    except:
        with open(JSON_FILE, 'r') as f:
            info = json.load(f)
    creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    return gspread.authorize(creds)

@st.cache_data(ttl=30)
def load_data():
    client = get_client()
    sheet = client.open_by_key(SHEET_ID).sheet1
    df = pd.DataFrame(sheet.get_all_records())
    df = df.loc[:, ~df.columns.str.contains('auto_unique_id')]
    return df

def save_data(df):
    client = get_client()
    sheet = client.open_by_key(SHEET_ID).sheet1
    sheet.clear()
    sheet.update(range_name='A1', values=[df.columns.tolist()] + df.fillna("").values.tolist())
    st.cache_data.clear()

try:
    df = load_data()

    tab1, tab2, tab3 = st.tabs(["📋 Data", "📊 Chart", "➕ Tambah / Edit / Hapus"])

    # ── TAB 1 : DATA ──
    with tab1:
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_model = st.multiselect("Model", options=sorted(df["Model"].dropna().unique()))
        with col2:
            filter_status = st.multiselect("Status", options=sorted(df["Status"].dropna().unique()))
        with col3:
            filter_bu = st.multiselect("Bu Owner", options=sorted(df["Bu Owner"].dropna().unique()))

        search = st.text_input("🔍 Cari")

        filtered = df.copy()
        if filter_model:
            filtered = filtered[filtered["Model"].isin(filter_model)]
        if filter_status:
            filtered = filtered[filtered["Status"].isin(filter_status)]
        if filter_bu:
            filtered = filtered[filtered["Bu Owner"].isin(filter_bu)]
        if search:
            filtered = filtered[filtered.apply(
                lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1
            )]

        st.dataframe(filtered, use_container_width=True)
        st.caption(f"Total: {len(filtered)} data")

        col_exp1, col_exp2 = st.columns(2)
        with col_exp1:
            buffe