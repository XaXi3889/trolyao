import streamlit as st
import pandas as pd
from rapidfuzz import process, fuzz
from pathlib import Path

EXCEL_FILE = "QCC3.xlsx"  # đổi tên file Excel thành data.xlsx cho gọn

st.title("🤖 Trợ lý ảo QC C3")
st.write("Xin chào, tôi là trợ lý ảo của bạn!")

@st.cache_data(show_spinner=False)
def load_data():
    file_to_read = EXCEL_FILE
    if not Path(file_to_read).exists():
        xlsx_files = list(Path(".").glob("*.xlsx"))
        if not xlsx_files:
            raise FileNotFoundError("Không tìm thấy file .xlsx trong repo.")
        file_to_read = xlsx_files[0].name
    df = pd.read_excel(file_to_read, engine="openpyxl")
    df = df.fillna("")
    df.columns = df.columns.map(str)
    return df, file_to_read

df, using_file = load_data()
st.caption(f"Đang dùng dữ liệu: **{using_file}**")

# Gộp toàn bộ cột để tìm gần đúng
df["_combined_"] = df.astype(str).agg(" ".join, axis=1).str.lower()

q = st.text_input("Bạn muốn hỏi gì?")

if q:
    q_norm = q.lower().strip()
    match, score, idx = process.extractOne(
        q_norm, df["_combined_"], scorer=fuzz.token_set_ratio
    )

    if score >= 55:  # ngưỡng giống
        st.success(f"✅ Tìm thấy lỗi gần nhất (độ giống {score:.1f}%)")

        # Lấy cột "Cách xử lý" (bạn cần đúng tên cột trong file Excel)
        if "Cách xử lý" in df.columns:
            cach_xu_ly = df.iloc[idx]["Cách xử lý"]
            st.subheader("🛠️ Cách xử lý")
            st.write(cach_xu_ly if cach_xu_ly else "Chưa có hướng dẫn xử lý.")
        else:
            st.error("⚠️ Không tìm thấy cột 'Cách xử lý' trong file Excel.")
    else:
        st.error("❌ Không tìm thấy kết quả phù hợp. Hãy thử từ khóa khác.")
