# File: app_streamlit.py
# Aplikasi Kalibrasi Anak Timbang menggunakan Streamlit

import streamlit as st
import math
import statistics

# =====================================================================
# BAGIAN LOGIKA PERHITUNGAN
# =====================================================================

def hitung_kalibrasi_revisi(data):
    """
    Melakukan perhitungan kalibrasi dengan fokus pada analisis ketidakpastian.
    """
    try:
        # --- Ambil Data Input ---
        m_s_konvensional_g = data['massa_s_konvensional']
        u_s_sertifikat_mg = data['ketidakpastian_s']
        faktor_cakupan = data['faktor_cakupan']
        
        m_t_nominal_kg = data['massa_t_nominal']
        resolusi_mg = data['resolusi']
        mpe_mg = data['mpe']

        # --- Data Pembacaan Berulang (dianggap dalam mg) ---
        pembacaan_s_mg = data['pembacaan_s_list']
        pembacaan_t_mg = data['pembacaan_t_list']

        if len(pembacaan_s_mg) != len(pembacaan_t_mg) or not pembacaan_s_mg:
            raise ValueError("Jumlah pembacaan Standar dan Uji harus sama dan tidak boleh kosong.")

        # --- Perhitungan Massa Konvensional UUT ---
        selisih_pembacaan_mg = [(t - s) for s, t in zip(pembacaan_t_mg, pembacaan_s_mg)]
        rata_rata_selisih_mg = statistics.mean(selisih_pembacaan_mg)
        
        rata_rata_selisih_g = rata_rata_selisih_mg / 1000.0
        
        massa_t_konvensional_g = m_s_konvensional_g + rata_rata_selisih_g

        # --- Perhitungan Koreksi (C) ---
        m_t_nominal_g = m_t_nominal_kg * 1000.0
        koreksi_g = massa_t_konvensional_g - m_t_nominal_g
        koreksi_mg = koreksi_g * 1000.0

        # --- Perhitungan Anggaran Ketidakpastian (semua dalam gram) ---
        u_s_g = (u_s_sertifikat_mg / 1000.0) / faktor_cakupan

        if len(selisih_pembacaan_mg) > 1:
            stdev_mg = statistics.stdev(selisih_pembacaan_mg)
        else:
            stdev_mg = 0
        u_rep_g = stdev_mg / 1000.0

        resolusi_g = resolusi_mg / 1000.0
        u_res_g = (resolusi_g / 2) / math.sqrt(3)

        u_c_kuadrat_g = u_s_g**2 + u_rep_g**2 + u_res_g**2
        u_c_g = math.sqrt(u_c_kuadrat_g)

        ketidakpastian_diperluas_g = u_c_g * faktor_cakupan
        ketidakpastian_diperluas_mg = ketidakpastian_diperluas_g * 1000.0

        # --- Pengecekan MPE (Maximum Permissible Error) ---
        if abs(koreksi_mg) + ketidakpastian_diperluas_mg <= mpe_mg:
            mpe_status = "LULUS"
        else:
            mpe_status = "TIDAK LULUS"

        return {
            "nominal_g": m_t_nominal_g,
            "massa_konvensional": massa_t_konvensional_g,
            "koreksi_mg": koreksi_mg,
            "ketidakpastian_diperluas": ketidakpastian_diperluas_g,
            "faktor_cakupan": faktor_cakupan,
            "mpe_status": mpe_status,
            "error": None
        }

    except Exception as e:
        return {"error": str(e)}

# =====================================================================
# BAGIAN TAMPILAN WEB STREAMLIT
# =====================================================================

st.set_page_config(page_title="Kalkulator Kalibrasi", layout="wide")

st.title("Kalkulator Kalibrasi Anak Timbang")
st.markdown("Aplikasi untuk analisis ketidakpastian pengukuran berdasarkan metode perbandingan.")

# Inisialisasi session state untuk menyimpan jumlah baris pengulangan
if 'num_readings' not in st.session_state:
    st.session_state.num_readings = 1

# --- Formulir Input ---
with st.form(key='kalibrasi_form'):
    
    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.subheader("1. Anak Timbang Standar (S)")
        massa_s_konvensional = st.number_input("Nilai Massa Konvensional (g)", format="%.5f", step=1.0)
        ketidakpastian_s = st.number_input("Ketidakpastian (mg)", format="%.5f", step=0.1)
        faktor_cakupan = st.number_input("Faktor Cakupan (k)", value=2.0, step=0.1, help="Default adalah 2")
        
        st.divider()

        st.subheader("2. Anak Timbang Uji (T)")
        massa_t_nominal = st.number_input("Massa Nominal (Kg)", format="%.5f", step=1.0)
        densitas_t = st.number_input("Densitas Anak Timbang Uji (kg/m³)", value=7950.0)
        mpe = st.number_input("Maximum Permissible Error (MPE) (mg)", format="%.5f", step=1.0)

    with col2:
        st.subheader("3. Data Neraca")
        kapasitas = st.number_input("Kapasitas (g)", format="%.2f", step=100.0)
        resolusi = st.number_input("Resolusi (mg)", format="%.5f", step=0.01)

        st.divider()

        st.subheader("4. Data Pengulangan Pembacaan (mg)")
        
        s_readings = []
        t_readings = []
        
        # Buat kolom untuk pembacaan S dan T
        read_col1, read_col2 = st.columns(2)
        
        for i in range(st.session_state.num_readings):
            with read_col1:
                s_readings.append(st.number_input(f"Standar S{i+1}", key=f"s_{i}", format="%.5f", step=0.1))
            with read_col2:
                t_readings.append(st.number_input(f"Uji T{i+1}", key=f"t_{i}", format="%.5f", step=0.1))

    # Tombol submit di dalam form
    submit_button = st.form_submit_button(label='Hitung Kalibrasi')

# Tombol untuk menambah/mengurangi baris di luar form agar tidak men-submit data
st.markdown("---")
form_col1, form_col2, form_col3 = st.columns([1,1,5])

with form_col1:
    if st.button("➕ Tambah Pengulangan"):
        st.session_state.num_readings += 1
        st.rerun()

with form_col2:
    if st.session_state.num_readings > 1:
        if st.button("➖ Hapus Pengulangan"):
            st.session_state.num_readings -= 1
            st.rerun()

# --- Logika Setelah Tombol Ditekan ---
if submit_button:
    data_input = {
        'massa_s_konvensional': massa_s_konvensional,
        'ketidakpastian_s': ketidakpastian_s,
        'faktor_cakupan': faktor_cakupan,
        'massa_t_nominal': massa_t_nominal,
        'densitas_t': densitas_t,
        'mpe': mpe,
        'kapasitas': kapasitas,
        'resolusi': resolusi,
        'pembacaan_s_list': s_readings,
        'pembacaan_t_list': t_readings,
    }

    hasil = hitung_kalibrasi_revisi(data_input)

    st.markdown("---")
    st.header("Hasil Perhitungan")

    if hasil.get("error"):
        st.error(f"Terjadi Kesalahan: {hasil['error']}")
    else:
        res_col1, res_col2, res_col3 = st.columns(3)
        with res_col1:
            st.metric(label="Massa Konvensional (g)", value=f"{hasil['massa_konvensional']:.5f}")
        with res_col2:
            st.metric(label="Koreksi (mg)", value=f"{hasil['koreksi_mg']:.3f}")
        with res_col3:
            st.metric(label="Ketidakpastian Diperluas (g)", value=f"{hasil['ketidakpastian_diperluas']:.5f}")

        st.markdown("<br>", unsafe_allow_html=True)

        if hasil['mpe_status'] == 'LULUS':
            st.success(f"**Status MPE: {hasil['mpe_status']}**", icon="✅")
        else:
            st.error(f"**Status MPE: {hasil['mpe_status']}**", icon="❌")
