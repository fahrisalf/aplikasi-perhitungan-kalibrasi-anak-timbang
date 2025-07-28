# File: kalibrasi_neraca.py
# Aplikasi Kalibrasi Anak Timbang menggunakan Streamlit

import streamlit as st
import math
import statistics
import base64

# =========================
# BAGIAN LOGIKA PERHITUNGAN
# =========================

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
        v1 = 60
        c1 = 1
        v2 = len(selisih_pembacaan_g)-1 if len(selisih_pembacaan_g) > 1 else 1 
        c2 = 1
        v3 = 1*(10**10)
        c3 = 1
        v4 = 100
        c4 = ((1 / densitas_anak_timbang)-(1/8000))*(massa_nominal_g/1000)
        v5 = 4
        c5 = 1
        
        selisih_pembacaan_mg = [x * 1000 for x in selisih_pembacaan_g] 
        u_standar_massa_U1 = ketidakpastian_mg / faktor_cakupan
        uc_U1 = u_standar_massa_U1*c1
        uc1_U1 = uc_U1**2
        uc2_U1 = uc_U1**4/v1
        
        if len(selisih_pembacaan_mg) > 1:
            stdev_mg = statistics.stdev(selisih_pembacaan_mg)
        else:
            stdev_mg = 0
        u_daya_ulang_pembacaan_U2 = stdev_mg / math.sqrt(len(selisih_pembacaan_mg)) if len(selisih_pembacaan_mg) > 0 else 0
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
        uc1_g = math.sqrt(uc1_kuadrat_mg) 

        uc2_kuadrat_mg = uc2_U1 + uc2_U2 + uc2_U3 + uc2_U4 + uc2_U5
        
        if uc2_kuadrat_mg == 0:
            uc2_veff = float('inf') 
        else:
            uc2_veff = (uc1_g**4) / uc2_kuadrat_mg

        if uc2_veff == 0:
            faktor_cakupan_k = faktor_cakupan 
        else:
            faktor_cakupan_k = 1.95996 + (2.37356 / uc2_veff) + (2.818745 / (uc2_veff**2)) + (2.546662 / (uc2_veff**3)) + (1.761829 / (uc2_veff**4)) + (0.245458 / (uc2_veff**5)) + (1.000764 / (uc2_veff**6))
        
        ketidakpastian_diperluas_mg = uc1_g * faktor_cakupan_k
        ketidakpastian_diperluas_g = ketidakpastian_diperluas_mg / 1000.0 

        return {
            'massa_t_konvensional_g': massa_t_konvensional_g,
            'ketidakpastian_diperluas_g': ketidakpastian_diperluas_g,
            'faktor_cakupan_k': faktor_cakupan_k,
            'massa_nominal_g': massa_nominal_g 
        }

    except Exception as e:
        return {"error": str(e)}

# =====================================================================
# BAGIAN TAMPILAN WEB STREAMLIT
# =====================================================================

st.set_page_config(page_title="Kalkulator Kalibrasi Anak Timbang", page_icon="⚖️", layout="wide")

@st.cache_data
def get_img_as_base64(file):
    """Fungsi untuk membaca file gambar dan mengonversinya ke base64."""
    with open(file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

try:
    img_base64 = get_img_as_base64("background.jpg")
    
    with open("style.css", "r") as f:
        css_content = f.read()
        
    css_with_image = css_content.replace("{KODE_BASE64}", img_base64)
    
    st.markdown(f"<style>{css_with_image}</style>", unsafe_allow_html=True)
    
except FileNotFoundError:
    st.error("Pastikan file 'background.jpg' dan 'style.css' berada di folder yang sama dengan skrip Python ini.")

if 'num_readings' not in st.session_state:
    st.session_state.num_readings = 3

with st.sidebar:
    st.title("⚖️ Kalkulator Kalibrasi Anak Timbang")
    st.markdown("Aplikasi untuk menghitung hasil kalibrasi anak timbang.")
    st.info("Selamat Datang! Silakan baca panduan dan isi parameter di halaman utama.")
    with st.expander("📖 Panduan Penggunaan", expanded=True):
        st.markdown("""
        1.  **Isi Parameter Input** di halaman utama.
        2.  **Gunakan tanda titik `.`** atau `,` sebagai pemisah desimal.
        3.  **Kelola Pengulangan** dengan tombol `➕ Tambah` atau `➖ Hapus`.
        4.  **Klik `🚀 Hitung Kalibrasi`**.
        5.  **Hasil perhitungan** dan **prosesnya** akan muncul di bawah.
        """)

    st.markdown("---") 
    st.markdown("### Kelompok 6")
    st.markdown("""
    - **Annisa Widiyastuti Putri** (2460330)
    - **Fahri Salman Alfarizi** (2460365)
    - **Maula Izzati** (2460415)
    - **Nayla Amanda Zalfa** (2460463)
    - **Surya Adi Syaputra** (2460522)
    """)
    
    st.markdown("---")
    st.markdown("#### Contact Person")
    st.markdown("📞 +62 895-3348-98422 (Fahri)")


st.title("Kalkulator Kalibrasi Anak Timbang")

st.header("⚙️ Parameter Input")
with st.form(key='kalibrasi_form'):
    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.subheader("1. Anak Timbang Standar (S)")
        nilai_massa_konvensional = st.number_input("Massa Konvensional (g)", format="%.5f", step=1.0)
        ketidakpastian = st.number_input("Ketidakpastian (mg)", format="%.5f", step=0.001)
        faktor_cakupan = st.number_input("Faktor Cakupan (k)", value=2.0, step=0.1)
        st.divider()
        st.subheader("2. Anak Timbang Uji (T)")
        massa_nominal = st.number_input("Massa Nominal (g)", format="%.5f", step=1.0)
        densitas_anak_timbang_uji = st.number_input("Densitas (kg/m³)", value=7950.0)
        mpe = st.number_input("MPE (mg)", format="%.5f", step=0.1)
    with col2:
        st.subheader("3. Data Neraca")
        kapasitas = st.number_input("Kapasitas (g)", format="%.2f", step=100.0)
        resolusi = st.number_input("Resolusi (mg)", format="%.5f", step=0.001)
        st.divider()
        st.subheader(f"4. Data Pengulangan Pembacaan (mg) Berulang ({st.session_state.num_readings}x)")
        s_readings = []
        t_readings = []
        read_col1, read_col2 = st.columns(2)
        for i in range(st.session_state.num_readings):
            with read_col1:
                s_readings.append(st.number_input(f"Std. S{i+1} (mg)", key=f"s_{i}", format="%.5f", step=0.01))
            with read_col2:
                t_readings.append(st.number_input(f"Uji T{i+1} (mg)", key=f"t_{i}", format="%.5f", step=0.01))
    submit_button = st.form_submit_button(label='🚀 Hitung Kalibrasi', use_container_width=True)

with st.container(border=True):
    st.write("**Kontrol Pengulangan**")
    btn_col1, btn_col2, _ = st.columns([1, 1, 10])
    if btn_col1.button("➕ Tambah"):
        st.session_state.num_readings += 1
        st.rerun()
    if st.session_state.num_readings > 1:
        if btn_col2.button("➖ Hapus", type="secondary"):
            st.session_state.num_readings -= 1
            st.rerun()

if submit_button:
    data_input = {
        'nilai_massa_konvensional': nilai_massa_konvensional, 'ketidakpastian': ketidakpastian,
        'faktor_cakupan': faktor_cakupan, 'massa_nominal': massa_nominal,
        'densitas_anak_timbang_uji': densitas_anak_timbang_uji, 'mpe': mpe,
        'kapasitas': kapasitas, 'resolusi': resolusi,
        'pembacaan_s_list': s_readings, 'pembacaan_t_list': t_readings,
    }
    output = hitung_kalibrasi_revisi(data_input)
    
    st.markdown("---")
    
    with st.container(border=True):
        st.header("📈 Hasil Perhitungan")

        if output.get("error"):
            st.error(f"Terjadi Kesalahan: {output['error']}", icon="🚨")
        else:
            hasil = output
            
            res_col1, res_col2, res_col3, res_col4 = st.columns(4)
            res_col1.metric("Massa Nominal Uji (g)", f"{hasil['massa_nominal_g']:.4f}")
            res_col2.metric("Massa Konvensional Hasil (g)", f"{hasil['massa_t_konvensional_g']:.5f}")
            res_col3.metric("Ketidakpastian Diperluas (g)", f"± {hasil['ketidakpastian_diperluas_g']:.5f}")
            res_col4.metric("Faktor Cakupan (k)", f"{hasil['faktor_cakupan_k']:.3f}")
