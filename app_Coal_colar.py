import io
import pandas as pd
import streamlit as st

# 1. Pengaturan Dasar Halaman Streamlit
st.set_page_config(
    page_title="Mining Data Condenser", page_icon="⛏️", layout="centered"
)

st.title("⛏️ Mining Data Condenser App")
st.write(
    "Upload file Excel (Sumber Data) untuk mengonversi formatnya berdasarkan LITO = CO."
)

# 2. Komponen File Uploader
uploaded_file = st.file_uploader(
    "Pilih file Excel kamu:", type=["xlsx", "xls"]
)

if uploaded_file is not None:
    try:
        # 3. Load data dan skip 2 baris awal (Header utama ada di baris ke-3)
        df_source = pd.read_excel(uploaded_file, skiprows=2)

        # Bersihkan nama kolom dari spasi liar di awal/akhir teks
        df_source.columns = df_source.columns.str.strip()

        # Validasi kecocokan kolom standar wajib (sekarang ditambah kolom LITO)
        required_cols = ["ID", "X", "Y", "Z", "TO", "LITO"]
        if not all(col in df_source.columns for col in required_cols):
            st.error(
                f"Format kolom tidak sesuai! Pastikan file memiliki kolom: {required_cols}"
            )
        else:
            # 4. Proses Transformasi Data
            df_filtered = df_source[
                ["ID", "X", "Y", "Z", "TO", "LITO"]
            ].copy()

            # Mengatasi merged cells pada kolom ID
            df_filtered["ID"] = df_filtered["ID"].ffill()

            # Bersihkan nilai pada kolom LITO dari spasi liar dan ubah ke uppercase
            df_filtered["LITO"] = (
                df_filtered["LITO"].astype(str).str.strip().str.upper()
            )

            # --- PERBAIKAN LOGIKA: FILTER HANYA LITO == CO ---
            df_filtered = df_filtered[df_filtered["LITO"] == "CO"]
            # -------------------------------------------------

            # Mengubah TO menjadi numerik (jika ada karakter non-angka seperti '-' diubah jadi 0)
            df_filtered["TO"] = (
                pd.to_numeric(df_filtered["TO"], errors="coerce")
                .fillna(0)
                .round(3)
            )

            # Agregasi Groupby berdasarkan ID unik setelah difilter CO
            df_output = (
                df_filtered.groupby("ID")
                .agg(
                    X=("X", "first"),
                    Y=("Y", "first"),
                    Z=("Z", "first"),
                    Max_TO=("TO", "max"),  # Sekarang otomatis TO terbesar milik CO
                )
                .reset_index()
            )

            # Tambahkan konstanta 0.05 ke nilai TO maksimum CO dan bulatkan desimalnya
            df_output["E"] = (df_output["Max_TO"] + 0.05).round(3)

            # --- LOGIKA SORTING ID SECARA NUMERIK ---
            df_output["id_num"] = (
                df_output["ID"].str.extract(r"(\d+)").astype(int)
            )
            df_output = df_output.sort_values(by="id_num").reset_index(
                drop=True
            )
            # ----------------------------------------

            # Pilih kolom akhir sesuai format output
            df_output = df_output[["ID", "X", "Y", "Z", "E"]]

            # 5. Menampilkan Preview Hasil di Aplikasi Web
            st.success(
                "Data berhasil diproses! TO diambil dari nilai terbesar yang memiliki LITO = CO."
            )
            st.subheader("📋 Preview Data Output (10 Baris Pertama)")
            st.dataframe(df_output.head(10))

            # 6. Mekanisme Export ke Excel Tanpa Header Teks
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                df_output.to_excel(writer, index=False, header=False)

            # 7. Tombol Download Hasil
            st.download_button(
                label="📥 Download Hasil (.xlsx)",
                data=buffer.getvalue(),
                file_name="output_kondensasi_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses file: {e}")