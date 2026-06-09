import streamlit as st
import gspread
import pandas as pd
import plotly.express as px
from google.oauth2 import service_account
from io import BytesIO
import json
import hashlib
import segno
import datetime

st.set_page_config(page_title="Dashboard IT Asset", layout="wide")

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

SHEET_ID = "1msf4IK1ZJReQl5f_6VRbVCsGiJXcHUHENto1DqrQwkY"
JSON_FILE = "dashboard-laptop-it-92f648a3958c.json"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@st.cache_resource
def get_client():
    try:
        info = json.loads(st.secrets["gcp_json"])
    except:
        with open(JSON_FILE, 'r') as f:
            info = json.load(f)
    creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    return gspread.authorize(creds)

def get_users_sheet():
    client = get_client()
    spreadsheet = client.open_by_key(SHEET_ID)
    try:
        return spreadsheet.worksheet("users")
    except:
        sheet = spreadsheet.add_worksheet(title="users", rows=100, cols=3)
        sheet.append_row(["username", "password", "role"])
        sheet.append_row(["admin", hash_password("admin123"), "admin"])
        sheet.append_row(["it", hash_password("itumara2024"), "user"])
        return sheet

def get_riwayat_sheet():
    client = get_client()
    spreadsheet = client.open_by_key(SHEET_ID)
    try:
        return spreadsheet.worksheet("riwayat")
    except:
        sheet = spreadsheet.add_worksheet(title="riwayat", rows=1000, cols=5)
        sheet.append_row(["Waktu", "User", "Aksi", "Detail", "No Aset"])
        return sheet

def catat_riwayat(aksi, detail, no_aset="-"):
    try:
        sheet = get_riwayat_sheet()
        waktu = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user = st.session_state.get("username", "-")
        sheet.append_row([waktu, user, aksi, detail, no_aset])
    except:
        pass

@st.cache_data(ttl=10)
def load_users():
    sheet = get_users_sheet()
    data = sheet.get_all_records()
    return pd.DataFrame(data) if data else pd.DataFrame(columns=["username", "password", "role"])

def save_user(username, password, role="user"):
    sheet = get_users_sheet()
    users_df = load_users()
    if username in users_df["username"].values:
        cell = sheet.find(username)
        sheet.update_cell(cell.row, 2, hash_password(password))
    else:
        sheet.append_row([username, hash_password(password), role])
    load_users.clear()

def delete_user(username):
    sheet = get_users_sheet()
    cell = sheet.find(username)
    if cell:
        sheet.delete_rows(cell.row)
    load_users.clear()

def verify_user(username, password):
    users_df = load_users()
    if users_df.empty:
        return False
    user_row = users_df[users_df["username"] == username]
    if user_row.empty:
        return False
    return user_row.iloc[0]["password"] == hash_password(password)

def get_user_role(username):
    users_df = load_users()
    user_row = users_df[users_df["username"] == username]
    if user_row.empty:
        return "user"
    return user_row.iloc[0]["role"]

def login():
    st.title("🔐 Login Dashboard IT Asset")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            if verify_user(username, password):
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.session_state["role"] = get_user_role(username)
                catat_riwayat("Login", f"User {username} login")
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
    "Lenovo V14 G2-ITL": "LNV-V14G2ITL",
    "Lenovo Ideapad 330": "LNV-IP330",
    "Lenovo G40 G9": "LNV-G40G9",
    "Lenovo G40 G6": "LNV-G40G6",
    "Lenovo G40-30": "LNV-G40-30",
    "Lenovo Yoga 730": "LNV-YG730",
    "Lenovo Thinkpad E490": "LNV-TPE490",
    "Lenovo K14 Gen 1": "LNV-K14G1",
    "Lenovo Legion 5": "LNV-LEG5",
    "HP 240 G6": "HP-240G6",
    "HP 240 G8": "HP-240G8",
    "HP 240 G9": "HP-240G9",
    "HP 240 G4 G3-IAP": "HP-240G4",
    "HP 14-bw515AU": "HP-14BW",
    "HP Aspire ES 11": "HP-ASPES11",
    "Aspire ES 11": "ACR-ASPES11",
    "HP ProBook 640 G4": "HP-PB640G4",
    "HP Latitude 5300": "HP-LAT5300",
    "HP 14-am503TU": "HP-14AM",
    "HP 14-bs006T": "HP-14BS",
    "Asus X540L": "ASUS-X540L",
    "Apple MacBook Air M2 (2022)": "APL-MBA-M2",
    "Acer Aspire 3": "ACR-ASP3",
    "Dell Latitude 3490": "DELL-LAT3490",
    "Dell Latitude 3400": "DELL-LAT3400",
    "Dell Latitude 5300": "DELL-LAT5300",
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

def hitung_umur(buy_date_str):
    try:
        if not buy_date_str or str(buy_date_str).strip() in ["-", "", "nan"]:
            return "-"
        buy_date = pd.to_datetime(buy_date_str)
        umur = (datetime.datetime.now() - buy_date).days // 365
        return f"{umur} tahun"
    except:
        return "-"

def generate_qr(data_text):
    qr = segno.make(data_text)
    buffer = BytesIO()
    qr.save(buffer, kind='png', scale=6)
    buffer.seek(0)
    return buffer

@st.cache_data(ttl=30)
def load_data():
    client = get_client()
    sheet = client.open_by_key(SHEET_ID).sheet1
    df = pd.DataFrame(sheet.get_all_records())
    df = df.loc[:, ~df.columns.str.contains('auto_unique_id')]
    return df

@st.cache_data(ttl=30)
def load_riwayat():
    sheet = get_riwayat_sheet()
    data = sheet.get_all_records()
    return pd.DataFrame(data) if data else pd.DataFrame(columns=["Waktu", "User", "Aksi", "Detail", "No Aset"])

def save_data(df, aksi="Edit", detail="", no_aset="-"):
    client = get_client()
    sheet = client.open_by_key(SHEET_ID).sheet1
    sheet.clear()
    sheet.update(range_name='A1', values=[df.columns.tolist()] + df.fillna("").values.tolist())
    catat_riwayat(aksi, detail, no_aset)
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
    "Umur": st.column_config.TextColumn("Umur", width="small"),
}

# ── HEADER ──
col_title, col_logout = st.columns([6, 1])
with col_title:
    st.title("Dashboard IT Asset Umara Group")
with col_logout:
    st.write(f"👤 {st.session_state['username']}")
    if st.button("Logout"):
        catat_riwayat("Logout", f"User {st.session_state['username']} logout")
        st.session_state["logged_in"] = False
        st.rerun()

try:
    df = load_data()

    if "Buy date" in df.columns:
        df["Umur"] = df["Buy date"].apply(hitung_umur)

    total = len(df)
    dipakai = len(df[df["Status"].str.lower().str.contains("pakai", na=False)])
    rusak = len(df[df["Status"].str.lower().str.contains("rusak", na=False)])
    servis = len(df[df["Status"].str.lower().str.contains("perbaikan", na=False)])
    tersedia = len(df[df["Status"].str.lower().str.contains("tersedia", na=False)])
    tua = len(df[df["Umur"].str.contains(r"^[5-9]|^[1-9][0-9]", na=False, regex=True)])

    s1, s2, s3, s4, s5, s6 = st.columns(6)
    s1.metric("💻 Total Asset", total)
    s2.metric("✅ Di Pakai", dipakai)
    s3.metric("🔧 Perlu Perbaikan", servis)
    s4.metric("❌ Rusak", rusak)
    s5.metric("📦 Tersedia", tersedia)
    s6.metric("⏰ Laptop Tua (>5th)", tua)

    st.divider()

    perlu_servis = df[df["Status"].str.lower().str.contains("perbaikan|rusak", na=False)]
    laptop_tua = df[df["Umur"].str.contains(r"^[5-9]|^[1-9][0-9]", na=False, regex=True)]

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📋 Data",
        "📊 Chart",
        "➕ Tambah / Edit / Hapus",
        f"⚠️ Perlu Perhatian ({len(perlu_servis)})",
        "📜 Riwayat",
        "⚙️ Settings",
        "🔧 Tools"
    ])

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
            save_data(df, "Generate No Aset", "Generate ulang semua No Aset")
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
                save_data(edited, "Edit Data", "Edit data laptop")
                st.success("Data berhasil disimpan!")
                st.rerun()

        elif action == "➕ Tambah Data":
            new_row = {}
            cols = st.columns(3)
            for i, col in enumerate(df.columns):
                with cols[i % 3]:
                    if col in ["No Aset", "Umur"]:
                        new_row[col] = ""
                    else:
                        new_row[col] = st.text_input(col)
            if st.button("➕ Tambah"):
                new_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                new_df["No Aset"] = generate_asset_numbers(new_df)
                save_data(new_df, "Tambah Data",
                         f"Tambah laptop {new_row.get('Model','-')} SN:{new_row.get('Serial Number','-')}",
                         new_df.iloc[-1]["No Aset"])
                st.success("Data berhasil ditambahkan!")
                st.rerun()

        elif action == "🗑️ Hapus Data":
            st.dataframe(df, use_container_width=True, column_config=COLUMN_CONFIG)
            row_idx = st.number_input("Nomor baris yang dihapus (mulai dari 0)",
                                      min_value=0, max_value=len(df)-1, step=1)
            hapus_row = df.iloc[int(row_idx)]
            st.warning(f"Akan menghapus: {hapus_row.to_dict()}")
            if st.button("🗑️ Hapus"):
                new_df = df.drop(index=int(row_idx)).reset_index(drop=True)
                new_df["No Aset"] = generate_asset_numbers(new_df)
                save_data(new_df, "Hapus Data",
                         f"Hapus laptop {hapus_row.get('Model','-')} SN:{hapus_row.get('Serial Number','-')}",
                         hapus_row.get("No Aset", "-"))
                st.success("Data berhasil dihapus!")
                st.rerun()

    # ── TAB 4 : PERLU PERHATIAN ──
    with tab4:
        st.subheader(f"⚠️ {len(perlu_servis)} Laptop Perlu Perhatian")
        if perlu_servis.empty:
            st.success("Semua laptop dalam kondisi baik!")
        else:
            st.dataframe(
                perlu_servis[["No Aset", "Model", "Serial Number", "User", "Bu Owner", "Status", "Notes"]],
                use_container_width=True
            )

        st.divider()
        st.subheader(f"⏰ {len(laptop_tua)} Laptop Tua (>5 Tahun)")
        if laptop_tua.empty:
            st.success("Tidak ada laptop tua!")
        else:
            st.dataframe(
                laptop_tua[["No Aset", "Model", "Serial Number", "User", "Bu Owner", "Buy date", "Umur", "Status"]],
                use_container_width=True
            )

    # ── TAB 5 : RIWAYAT ──
    with tab5:
        st.subheader("📜 Riwayat Aktivitas")

        riwayat_df = load_riwayat()

        if riwayat_df.empty:
            st.info("Belum ada riwayat aktivitas.")
        else:
            # Filter riwayat
            col1, col2 = st.columns(2)
            with col1:
                filter_user_r = st.multiselect("Filter User", options=sorted(riwayat_df["User"].dropna().unique()))
            with col2:
                filter_aksi_r = st.multiselect("Filter Aksi", options=sorted(riwayat_df["Aksi"].dropna().unique()))

            filtered_r = riwayat_df.copy()
            if filter_user_r:
                filtered_r = filtered_r[filtered_r["User"].isin(filter_user_r)]
            if filter_aksi_r:
                filtered_r = filtered_r[filtered_r["Aksi"].isin(filter_aksi_r)]

            # Tampilkan terbaru di atas
            st.dataframe(
                filtered_r.iloc[::-1].reset_index(drop=True),
                use_container_width=True
            )
            st.caption(f"Total: {len(filtered_r)} aktivitas")

            # Export riwayat
            buffer_r = BytesIO()
            with pd.ExcelWriter(buffer_r, engine='openpyxl') as writer:
                filtered_r.to_excel(writer, index=False)
            st.download_button("📥 Export Riwayat Excel", buffer_r.getvalue(), file_name="riwayat_aktivitas.xlsx")

            if st.session_state.get("role") == "admin":
                if st.button("🗑️ Hapus Semua Riwayat"):
                    sheet = get_riwayat_sheet()
                    sheet.clear()
                    sheet.append_row(["Waktu", "User", "Aksi", "Detail", "No Aset"])
                    st.cache_data.clear()
                    st.success("Riwayat berhasil dihapus!")
                    st.rerun()

    # ── TAB 6 : SETTINGS ──
    with tab6:
        st.subheader("⚙️ Pengaturan Akun")
        current_user = st.session_state["username"]
        is_admin = st.session_state.get("role") == "admin"

        st.markdown("### 🔑 Ganti Password")
        col1, col2 = st.columns(2)
        with col1:
            old_pass = st.text_input("Password Lama", type="password", key="old_pass")
            new_pass = st.text_input("Password Baru", type="password", key="new_pass")
            confirm_pass = st.text_input("Konfirmasi Password Baru", type="password", key="confirm_pass")
            if st.button("Simpan Password"):
                if not verify_user(current_user, old_pass):
                    st.error("Password lama salah!")
                elif new_pass != confirm_pass:
                    st.error("Password baru tidak cocok!")
                elif len(new_pass) < 6:
                    st.error("Password minimal 6 karakter!")
                else:
                    save_user(current_user, new_pass, st.session_state.get("role", "user"))
                    catat_riwayat("Ganti Password", f"User {current_user} ganti password")
                    st.success("Password berhasil diubah!")

        if is_admin:
            st.divider()
            st.markdown("### 👥 Kelola User (Admin Only)")
            col3, col4 = st.columns(2)
            with col3:
                st.markdown("**Tambah User Baru**")
                new_username = st.text_input("Username Baru", key="new_username")
                new_user_pass = st.text_input("Password", type="password", key="new_user_pass")
                new_user_role = st.selectbox("Role", ["user", "admin"], key="new_user_role")
                if st.button("➕ Tambah User"):
                    users_df = load_users()
                    if new_username in users_df["username"].values:
                        st.error("Username sudah ada!")
                    elif len(new_username) < 3:
                        st.error("Username minimal 3 karakter!")
                    elif len(new_user_pass) < 6:
                        st.error("Password minimal 6 karakter!")
                    else:
                        save_user(new_username, new_user_pass, new_user_role)
                        catat_riwayat("Tambah User", f"Tambah user {new_username} role {new_user_role}")
                        st.success(f"User '{new_username}' berhasil ditambahkan!")
                        st.rerun()

            with col4:
                st.markdown("**Hapus User**")
                users_df = load_users()
                user_list = [u for u in users_df["username"].tolist() if u != "admin"]
                if user_list:
                    del_user = st.selectbox("Pilih User", options=user_list)
                    if st.button("🗑️ Hapus User"):
                        delete_user(del_user)
                        catat_riwayat("Hapus User", f"Hapus user {del_user}")
                        st.success(f"User '{del_user}' berhasil dihapus!")
                        st.rerun()
                else:
                    st.info("Tidak ada user lain selain admin.")

            st.divider()
            st.markdown("**Daftar User Aktif**")
            users_df = load_users()
            st.dataframe(users_df[["username", "role"]], use_container_width=True, hide_index=True)

    # ── TAB 7 : TOOLS ──
    with tab7:
        tool = st.radio("Pilih Tool", ["📲 QR Code", "📤 Import Excel/CSV"], horizontal=True)

        if tool == "📲 QR Code":
            st.subheader("📲 Generate QR Code Laptop")
            no_aset_list = df["No Aset"].dropna().unique().tolist()
            no_aset_list = [x for x in no_aset_list if x not in ["-", ""]]
            selected = st.selectbox("Pilih No Aset", options=sorted(no_aset_list))

            if selected:
                row = df[df["No Aset"] == selected].iloc[0]
                info_text = (
                    f"No Aset: {row.get('No Aset', '-')}\n"
                    f"Model: {row.get('Model', '-')}\n"
                    f"Serial: {row.get('Serial Number', '-')}\n"
                    f"User: {row.get('User', '-')}\n"
                    f"Bu: {row.get('Bu Owner', '-')}\n"
                    f"Status: {row.get('Status', '-')}"
                )

                col_qr, col_info = st.columns(2)
                with col_qr:
                    qr_buffer = generate_qr(info_text)
                    st.image(qr_buffer, caption=f"QR Code - {selected}", width=250)
                    st.download_button(
                        "📥 Download QR Code",
                        data=generate_qr(info_text),
                        file_name=f"qr_{selected}.png",
                        mime="image/png"
                    )
                with col_info:
                    st.markdown("**Detail Laptop:**")
                    st.markdown(f"**No Aset:** {row.get('No Aset', '-')}")
                    st.markdown(f"**Model:** {row.get('Model', '-')}")
                    st.markdown(f"**Serial Number:** {row.get('Serial Number', '-')}")
                    st.markdown(f"**User:** {row.get('User', '-')}")
                    st.markdown(f"**Bu Owner:** {row.get('Bu Owner', '-')}")
                    st.markdown(f"**Status:** {row.get('Status', '-')}")
                    st.markdown(f"**Umur:** {row.get('Umur', '-')}")

        elif tool == "📤 Import Excel/CSV":
            st.subheader("📤 Import Data dari Excel/CSV")
            st.info("Upload file Excel/CSV dengan format kolom yang sama seperti data yang ada.")

            uploaded_file = st.file_uploader("Upload File", type=["xlsx", "csv"])
            if uploaded_file:
                try:
                    if uploaded_file.name.endswith(".csv"):
                        import_df = pd.read_csv(uploaded_file)
                    else:
                        import_df = pd.read_excel(uploaded_file)

                    st.write(f"Preview data ({len(import_df)} baris):")
                    st.dataframe(import_df.head(10), use_container_width=True)

                    mode = st.radio("Mode Import", ["Tambah ke data yang ada", "Ganti semua data"], horizontal=True)

                    if st.button("📤 Import Sekarang"):
                        if mode == "Tambah ke data yang ada":
                            new_df = pd.concat([df, import_df], ignore_index=True)
                        else:
                            new_df = import_df.copy()

                        new_df["No Aset"] = generate_asset_numbers(new_df)
                        save_data(new_df, "Import Data", f"Import {len(import_df)} data dari {uploaded_file.name}")
                        st.success(f"Berhasil import {len(import_df)} data!")
                        st.rerun()

                except Exception as ex:
                    st.error(f"Error membaca file: {ex}")

except Exception as e:
    import traceback
    st.error(f"Error: {e}")
    st.code(traceback.format_exc())