import streamlit as st
import pandas as pd
from rapidfuzz import fuzz, process
import pyttsx3

st.set_page_config(page_title="Trợ lý ảo QCC3", layout="centered")

st.title("🤖 Trợ lý ảo QCC3")

uploaded_file = st.file_uploader("📂 Tải file Excel dữ liệu", type=["xlsx"])

if uploaded_file:
    # Bỏ dòng tiêu đề phụ, lấy dòng thứ 2 làm header
    df = pd.read_excel(uploaded_file, header=1)

    # Chỉ lấy các cột cần thiết
    df = df[["THÔNG BÁO LỖI", "MÔ TẢ LỖI", "CÁCH XỬ LÍ"]]

    # Nhập từ khóa tìm kiếm
    query = st.text_input("🔍 Nhập từ khóa cần tra cứu:")

    if query:
        # Tìm kiếm mờ trong cột "THÔNG BÁO LỖI"
        choices = df["THÔNG BÁO LỖI"].astype(str).tolist()
        result = process.extractOne(query, choices, scorer=fuzz.WRatio)

        if result:
            matched_value, score, idx = result
            row = df.iloc[idx]

            st.subheader("📌 Kết quả tìm kiếm:")
            st.write(f"**THÔNG BÁO LỖI:** {row['THÔNG BÁO LỖI']}")
            st.write(f"**MÔ TẢ LỖI:** {row['MÔ TẢ LỖI']}")
            st.write(f"**CÁCH XỬ LÍ:** {row['CÁCH XỬ LÍ']}")

            # Đọc kết quả bằng giọng nói (tự động)
            engine = pyttsx3.init()
            text_to_speak = f"Lỗi: {row['THÔNG BÁO LỖI']}. Mô tả: {row['MÔ TẢ LỖI']}. Cách xử lý: {row['CÁCH XỬ LÍ']}."
            engine.say(text_to_speak)
            engine.runAndWait()
