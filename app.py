import streamlit as st
import gspread
import pandas as pd
import plotly.express as px
from google.oauth2 import service_account
from io import BytesIO
import json

st.set_page_config(page_title="Dashboard IT Asset", layout="wide")

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

SHEET_ID = "1msf4IK1ZJReQl5f_6VRbVCsGiJXcHUHENto1DqrQwkY"
JSON_FILE = "dashboard-laptop-it-92f648a3958c.json"

# ── LOGIN ──
USERS = {
    "admin": "admin123",
    "it": "itumara2024",
}

def login():
    st.title("🔐 Login Dashboard IT Asset")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            if username in USERS and USERS[username] == password:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.rerun()
            else:
                st.error("Username atau password salah!")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login()
    st.stop()

MODEL_CODE = {
    "Lenovo Ideapad 5": "LNV-IP5",
    "Lenovo Ideapad 130-14AST": "LNV-IP130",
    "Lenovo LOQ 15IRX9": "LNV-LOQ15",
    "Lenovo Thinkpad T490": "LNV-TPT490",
    "Lenovo V14 G2-ALC": "LNV-V14G2",
    "Lenovo V14 G3-IAP": "LNV-V14G3",
    "Lenovo V14 G3 IAP": "LNV-V14G3",
    "Lenovo Ideapad 330": "LNV-IP330",
    "Lenovo G40 G9": "LNV-G40G9",
    "Lenovo Yoga 730": "LNV-YG730",
    "Lenovo Thinkpad E490": "LNV-TPE490",
    "Lenovo K14 Gen 1": "LNV-K14G1",
    "Lenovo G40 G6": "LNV-G40G6",
    "HP 240 G6": "HP-240G6",
    "HP 240 G4 G3-IAP": "HP-240G4",
    "HP 14-bw515AU": "HP-14BW",
    "HP Aspire ES 11": "HP-ASPES11",
    "HP ProBook 640 G4": "HP-PB640G4",
    "HP Latitude 5300": "HP-LAT5300",
    "HP 14-am503TU": "HP-14AM",
    "HP 14-bs006T": "HP-14BS",
    "Asus X540L": "ASUS-X540L",
    "Apple MacBook Air M2 (2022)": "APL-MBA-M2",
    "Acer Aspire 3": "ACR-ASP3",
    "Dell Latitude 3490": "DELL-LAT3490",
    "Dell Latitude 3400": "DELL-LAT3400",
}

def generate_asset_numbers(df):
    counters = {}
    new_no_aset = []
    for _, row in df.iterrows():
        model = str(row.get("Model", "")).strip()
        code = MODEL_CODE.get(model, "UNKN")
        counters[code] = counters.get(code, 0) + 1
        new_no_aset.append(f"{code}-{counters[code]:03d}")
    return new_no_aset

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

COLUMN_CONFIG = {
    "No Aset": st.column_config.TextColumn("No Aset", width="medium"),
    "Model": st.column_config.TextColumn("Model", width="large"),
    "Serial Number": st.column_config.TextColumn("Serial Number", width="medium"),
    "Job Title": st.column_config.TextColumn("Job Title", width="large"),
    "User": st.column_config.TextColumn("User", width="medium"),
    "Notes": st.column_config.TextColumn("Notes", width="large"),
    "Buy date": st.column_config.TextColumn("Buy date", width="medium"),
    "Handover Date": st.column_config.TextColumn("Handover Date", width="medium"),
    "Return Date": st.column_config.TextColumn("Return Date", width="medium"),
    "Bu Owner": st.column_config.TextColumn("Bu Owner", width="small"),
    "Bu User": st.column_config.TextColumn("Bu User", width="small"),
    "Status": st.column_config.TextColumn("Status", width="medium"),
}

# ── HEADER ──
col_title, col_logout = st.columns([6, 1])
with col_title:
    st.title("Dashboard IT Asset Umara Group")
with col_logout:
    st.write(f"👤 {st.session_state['username']}")
    if st.button("Logout"):
        st.session_state["logged_in"] = False
        st.rerun()

try:
    df = load_data()

    # ── SUMMARY ──
    total = len(df)
    dipakai = len(df[df["Status"].str.lower().str.contains("pakai", na=False)])
    rusak = len(df[df["Status"].str.lower().str.contains("rusak", na=False)])
    servis = len(df[df["Status"].str.lower().str.contains("perbaikan", na=False)])
    tersedia = len(df[df["Status"].str.lower().str.contains("tersedia", na=False)])

    s1, s2, s3, s4, s5 = st.columns(5)
    s1.metric("💻 Total Asset", total)
    s2.metric("✅ Di Pakai", dipakai)
    s3.metric("🔧 Perlu Perbaikan", servis)
    s4.metric("❌ Rusak", rusak)
    s5.metric("📦 Tersedia", tersedia)

    st.divider()

    # ── NOTIFIKASI ──
    perlu_servis = df[df["Status"].str.lower().str.contains("perbaikan|rusak", na=False)]
    if not perlu_servis.empty:
        with st.expander(f"⚠️ {len(perlu_servis)} Laptop Perlu Perhatian!", expanded=True):
            st.dataframe(
                perlu_servis[["No Aset", "Model", "Serial Number", "User", "Bu Owner", "Status", "Notes"]],
                use_container_width=True
            )

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

        st.dataframe(filtered, use_container_width=True, column_config=COLUMN_CONFIG)
        st.caption(f"Total: {len(filtered)} data")

        col_exp1, col_exp2 = st.columns(2)
        with col_exp1:
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                filtered.to_excel(writer, index=False)
            st.download_button("📥 Export Excel", buffer.getvalue(), file_name="it_asset.xlsx")
        with col_exp2:
            st.download_button("📥 Export CSV", filtered.to_csv(index=False).encode('utf-8'), file_name="it_asset.csv")

        st.divider()
        if st.button("🔄 Generate Ulang Semua No Aset"):
            df["No Aset"] = generate_asset_numbers(df)
            save_data(df)
            st.success("No Aset berhasil di-generate!")
            st.rerun()

    # ── TAB 2 : CHART ──
    with tab2:
        c1, c2 = st.columns(2)
        with c1:
            status_df = df["Status"].value_counts().reset_index()
            status_df.columns = ["Status", "Jumlah"]
            fig1 = px.pie(status_df, names="Status", values="Jumlah",
                          title="Distribusi Status Asset", hole=0.4)
            st.plotly_chart(fig1, use_container_width=True)
        with c2:
            model_df = df["Model"].value_counts().reset_index()
            model_df.columns = ["Model", "Jumlah"]
            fig2 = px.bar(model_df, x="Model", y="Jumlah",
                          title="Jumlah per Model", color="Jumlah")
            st.plotly_chart(fig2, use_container_width=True)

        bu_df = df["Bu Owner"].value_counts().reset_index()
        bu_df.columns = ["Bu Owner", "Jumlah"]
        fig3 = px.bar(bu_df, x="Bu Owner", y="Jumlah",
                      title="Asset per BU", color="Bu Owner")
        st.plotly_chart(fig3, use_container_width=True)

    # ── TAB 3 : TAMBAH / EDIT / HAPUS ──
    with tab3:
        action = st.radio("Pilih Aksi", ["✏️ Edit Data", "➕ Tambah Data", "🗑️ Hapus Data"], horizontal=True)

        if action == "✏️ Edit Data":
            edited = st.data_editor(df, num_rows="fixed", use_container_width=True, column_config=COLUMN_CONFIG)
            if st.button("💾 Simpan Perubahan"):
                save_data(edited)
                st.success("Data berhasil disimpan!")
                st.rerun()

        elif action == "➕ Tambah Data":
            new_row = {}
            cols = st.columns(3)
            for i, col in enumerate(df.columns):
                with cols[i % 3]:
                    if col == "No Aset":
                        new_row[col] = ""
                    else:
                        new_row[col] = st.text_input(col)
            if st.button("➕ Tambah"):
                new_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                new_df["No Aset"] = generate_asset_numbers(new_df)
                save_data(new_df)
                st.success("Data berhasil ditambahkan!")
                st.rerun()

        elif action == "🗑️ Hapus Data":
            st.dataframe(df, use_container_width=True, column_config=COLUMN_CONFIG)
            row_idx = st.number_input("Nomor baris yang dihapus (mulai dari 0)",
                                      min_value=0, max_value=len(df)-1, step=1)
            st.warning(f"Akan menghapus: {df.iloc[int(row_idx)].to_dict()}")
            if st.button("🗑️ Hapus"):
                new_df = df.drop(index=int(row_idx)).reset_index(drop=True)
                new_df["No Aset"] = generate_asset_numbers(new_df)
                save_data(new_df)
                st.success("Data berhasil dihapus!")
                st.rerun()

except Exception as e:
    import traceback
    st.error(f"Error: {e}")
    st.code(traceback.format_exc())