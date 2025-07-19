# File: kalibrasi.py
# Aplikasi Kalibrasi Anak Timbang menggunakan Streamlit

import streamlit as st
import math
import statistics
from scipy.stats import t

# =====================================================================
# BAGIAN LOGIKA PERHITUNGAN
# =====================================================================

def hitung_kalibrasi_revisi(data):
    """
    Melakukan perhitungan kalibrasi dengan fokus pada analisis ketidakpastian.
    """
    try:
        # --- Ambil Data Input ---
        massa_konvensional_g = data['nilai_massa_konvensional']
        ketidakpastian_mg = data['ketidakpastian']
        faktor_cakupan = data['faktor_cakupan']
        
        massa_nominal_g = data['massa_nominal']
        densitas_anak_timbang = data['densitas_anak_timbang_uji']
        mpe_mg = data['mpe']
        
        kapasitas_g = data['kapasitas']
        resolusi_mg = data['resolusi']

        # --- Data Pembacaan Berulang (dianggap dalam g) ---
        pembacaan_s_g = data['pembacaan_s_list']
        pembacaan_t_g = data['pembacaan_t_list']

        if len(pembacaan_s_g) != len(pembacaan_t_g) or not pembacaan_s_g:
            raise ValueError("Jumlah pembacaan Standar dan Uji harus sama dan tidak boleh kosong.")

        # --- Perhitungan Massa Konvensional UUT ---
        selisih_pembacaan_g = [(t - s) for s, t in zip(pembacaan_t_g, pembacaan_s_g)]
        rata_rata_selisih_g = statistics.mean(selisih_pembacaan_g)
        
        massa_t_konvensional_g = massa_konvensional_g + rata_rata_selisih_g + 0

        # --- Perhitungan Ketidakpastian diperluas (semua dalam mg) ---
def derajat_kebebasan():
    try:
        v1 = 60
        c1 = 1
        v2 = len(selisih_pembacaan_g)-1
        c2 = 1
        v3 = 1*(10**10)
        c3 = 1
        v4 = 100
        c4 = ((1 / densitas_anak_timbang)-(1/8000))*(massa_nominal_g/1000)
        v5 = 4
        c5 = 1
        
        selisih_pembacaan_mg = selisih_pembacaan_g*1000
        u_standar_massa_U1 = ketidakpastian_mg / faktor_cakupan
        uc_U1 = u_standar_massa_U1*c1
        uc1_U1 = uc_U1**2
        uc2_U1 = uc_U1**4/v1
        
        if len(selisih_pembacaan_mg) > 1:
            stdev_mg = statistics.stdev(selisih_pembacaan_mg)
        else:
            stdev_mg = 0
        u_daya_ulang_pembacaan_U2 = stdev_mg / math.sqrt(len(selisih_pembacaan_mg))
        uc_U2 = u_daya_ulang_pembacaan_U2*c2
        uc1_U2 = uc_U2**2
        uc2_U2 = uc_U2**4/v2
        
        u_resolusi_timbangan_U3 = (resolusi_mg / 2) / math.sqrt(3)
        uc_U3 = u_resolusi_timbangan_U3*c3
        uc1_U3 = uc_U3**2
        uc2_U3 = uc_U3**4/v3
 
        u_bouyancy_U4 = 120000 / math.sqrt(3)
        uc_U4 = u_bouyancy_U4*c4
        uc1_U4 = uc_U4**2
        uc2_U4 = uc_U4**4/v4
        
        u_instability_U5 = ((8/100)*mpe_mg)/1
        uc_U5 = u_instability_U5*c5
        uc1_U5 = uc_U5**2
        uc2_U5 = uc_U5**4/v1
        
        uc1_kuadrat_mg = uc1_U1 + uc1_U2 + uc1_U3 + uc1_U4 + uc1_U5
        uc1_g = math.sqrt(uc_kuadrat_mg)

        uc2_kuadrat_mg = uc2_U1 + uc2_U2 + uc2_U3 + uc2_U4 + uc2_U5
        uc2_veff = (uc1_g**4) / uc2_kuadrat_mg

        k1 = 1,95996
        k2 = (2,37356 / uc2_veff)
        k3 = (2,818745 / (uc2_veff**2))
        k4 = (2,546662 / (uc2_veff**3))
        k5 = (1,761829 / (uc2_veff**4))
        k6 = (0,245458 / (uc2_veff**5))
        k7 = ("1,0o0764 / (uc2_veff**6)")
        faktor_cakupan_k = k1 + k2 + k3 + k4 + k5 + k6 + k7
        
        ketidakpastian_diperluas_mg = uc1_g * faktor_cakupan_k
        ketidakpastian_diperluas_g = ketidakpastian_diperluas_mg * 1000.0

# =====================================================================
# BAGIAN TAMPILAN WEB STREAMLIT
# =====================================================================

st.set_page_config(page_title="Kalkulator Kalibrasi", layout="wide")

st.title("Kalkulator Kalibrasi Anak Timbang")
st.markdown("Aplikasi untuk menghitung ketidakpastian dari kalibrasi anak timbang berdasarkan metode perbandingan.")

# Inisialisasi session state untuk menyimpan jumlah baris pengulangan
if 'num_readings' not in st.session_state:
    st.session_state.num_readings = 1

# --- Formulir Input ---
with st.form(key='kalibrasi_form'):
    
    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.subheader("1. Anak Timbang Standar (S)")
        nilai_massa_konvensional = st.number_input("Nilai Massa Konvensional (g)", format="%.5f", step=1.0)
        ketidakpastian = st.number_input("Ketidakpastian (mg)", format="%.5f", step=0.1)
        faktor_cakupan = st.number_input("Faktor Cakupan (k)", value=2.0, step=0.1, help="Default adalah 2")
        
        st.divider()

        st.subheader("2. Anak Timbang Uji (T)")
        massa_nominal = st.number_input("Massa Nominal (g)", format="%.5f", step=1.0)
        densitas_anak_timbang_uji = st.number_input("Densitas Anak Timbang Uji (kg/m³)", value=7950.0)
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
        'nilai_massa_konvensional': nilai_massa_konvensional,
        'ketidakpastian': ketidakpastian,
        'faktor_cakupan': faktor_cakupan,
        'massa_nominal': massa_nominal,
        'densitas_anak_timbang_uji': densitas_anak_timbang_uji,
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
            st.metric(label="Massa Nominal (g)", value=f"{['massa_nominal_g']:.5f}")
        with res_col2:
            st.metric(label="Massa Konvensional (g)", value=f"{hasil['massa_t_konvensional_g']:.3f}")
        with res_col3:
            st.metric(label="Ketidakpastian (g)", value=f"{hasil['ketidakpastian_diperluas_g']:.5f}")
        with res_col3:
            st.metric(label="Faktor cakupan (k)", value=f"{hasil['faktor_cakupan_k']:.5f}")

        st.markdown("<br>", unsafe_allow_html=True)
