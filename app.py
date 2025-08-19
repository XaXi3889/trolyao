import streamlit as st
import pandas as pd
from rapidfuzz import process, fuzz

# Tải dữ liệu từ Excel
@st.cache_data
def load_data():
    df = pd.read_excel("data.xlsx")   # đổi tên file nếu khác
    return df

df = load_data()

st.title("🤖 Trợ lý ảo QC C3")
st.write("Xin chào, tôi là trợ lý ảo của bạn!")

# Ô nhập câu hỏi
query = st.text_input("Bạn muốn hỏi gì?")

if query:
    # Lấy danh sách các lỗi từ file
    errors = df["THỐNG KÊ LỖI VÀ CÁCH XỬ LÝ"].astype(str).tolist()

    # Tìm kết quả gần giống nhất
    best_match, score, idx = process.extractOne(
        query, errors, scorer=fuzz.token_sort_ratio
    )

    if score > 50:  # Ngưỡng giống (có thể chỉnh lên 60-70)
        st.success(f"✅ Tôi tìm thấy kết quả gần nhất (độ giống {score:.2f}%):")

        # Lấy hàng dữ liệu tương ứng
        result_row = df.iloc[idx]

        # Hiển thị ra bảng (an toàn cho cả điện thoại)
        st.write(result_row.to_frame().T)
    else:
        st.error("❌ Xin lỗi, tôi không tìm thấy kết quả phù hợp.")
