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
    return pd.DataFrame(sheet.get_all_records())

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
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                filtered.to_excel(writer, index=False)
            st.download_button("📥 Export Excel", buffer.getvalue(), file_name="it_asset.xlsx")
        with col_exp2:
            st.download_button("📥 Export CSV", filtered.to_csv(index=False).encode('utf-8'), file_name="it_asset.csv")

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
            edited = st.data_editor(df, num_rows="fixed", use_container_width=True)
            if st.button("💾 Simpan Perubahan"):
                save_data(edited)
                st.success("Data berhasil disimpan!")
                st.rerun()

        elif action == "➕ Tambah Data":
            new_row = {}
            cols = st.columns(3)
            for i, col in enumerate(df.columns):
                with cols[i % 3]:
                    new_row[col] = st.text_input(col)
            if st.button("➕ Tambah"):
                save_data(pd.concat([df, pd.DataFrame([new_row])], ignore_index=True))
                st.success("Data berhasil ditambahkan!")
                st.rerun()

        elif action == "🗑️ Hapus Data":
            st.dataframe(df, use_container_width=True)
            row_idx = st.number_input("Nomor baris yang dihapus (mulai dari 0)",
                                      min_value=0, max_value=len(df)-1, step=1)
            st.warning(f"Akan menghapus: {df.iloc[int(row_idx)].to_dict()}")
            if st.button("🗑️ Hapus"):
                save_data(df.drop(index=int(row_idx)).reset_index(drop=True))
                st.success("Data berhasil dihapus!")
                st.rerun()

except Exception as e:
    import traceback
    st.error(f"Error: {e}")
    st.code(traceback.format_exc())