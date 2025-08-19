import streamlit as st
import pandas as pd
from rapidfuzz import process, fuzz
from pathlib import Path

EXCEL_FILE = "QCC3.xlsx"  # nếu bạn đã đổi tên theo Cách A

st.title("🤖 Trợ lý ảo QC C3")
st.write("Xin chào, tôi là trợ lý ảo của bạn!")

@st.cache_data(show_spinner=False)
def load_data():
    # Nếu EXCEL_FILE không tồn tại, thử tự tìm 1 file .xlsx trong thư mục
    file_to_read = EXCEL_FILE
    if not Path(file_to_read).exists():
        xlsx_files = list(Path(".").glob("*.xlsx"))
        if not xlsx_files:
            raise FileNotFoundError("Không tìm thấy file .xlsx trong repo.")
        file_to_read = xlsx_files[0].name  # dùng file .xlsx đầu tiên

    df = pd.read_excel(file_to_read, engine="openpyxl")
    df = df.fillna("")
    df.columns = df.columns.map(str)
    return df, file_to_read

df, using_file = load_data()
st.caption(f"Đang dùng dữ liệu: **{using_file}**")

# Gộp toàn bộ cột thành 1 chuỗi để tìm gần đúng
df["_combined_"] = df.astype(str).agg(" ".join, axis=1).str.lower()

q = st.text_input("Bạn muốn hỏi gì?")

if q:
    q_norm = q.lower().strip()
    match, score, idx = process.extractOne(
        q_norm, df["_combined_"], scorer=fuzz.token_set_ratio
    )

    if score >= 55:  # có thể chỉnh 60–70 tùy dữ liệu
        st.success(f"✅ Kết quả gần nhất (độ giống {score:.1f}%).")
        row = df.drop(columns=["_combined_"]).iloc[[idx]]
        # Hiển thị an toàn trên mobile
        st.write(row)
    else:
        st.error("❌ Không tìm thấy kết quả phù hợp. Hãy thử từ khóa khác.")
