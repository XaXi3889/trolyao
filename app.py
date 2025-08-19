import streamlit as st
import pandas as pd
from rapidfuzz import process

st.title("🤖 Trợ lý ảo QC C3")
st.write("Xin chào, tôi là trợ lý ảo của bạn!")

@st.cache_data
def load_data():
    # Bỏ 1 dòng đầu, lấy dòng thứ 2 làm header
    df = pd.read_excel("QCC3.xlsx", sheet_name=0, header=1)
    df = df.astype(str).apply(lambda x: x.str.lower().str.strip())
    return df

df = load_data()

question = st.text_input("Bạn muốn hỏi gì?")

if question:
    q = question.lower().strip()

    # Ghép các cột liên quan để so sánh
    df["combined"] = df[["Bộ phận", "THÔNG BÁO LỖI", "MÔ TẢ LỖI"]].agg(" ".join, axis=1)

    # Tìm dòng gần giống nhất
    best_match = process.extractOne(q, df["combined"], score_cutoff=40)  

    if best_match:
        matched_row = df.loc[df["combined"] == best_match[0]]

        st.success(f"🔑 Tôi tìm thấy kết quả gần nhất (độ giống {best_match[1]}%):")

        # Hiển thị gọn: chỉ thông tin lỗi + cách xử lý
        for idx, row in matched_row.iterrows():
            st.write(f"**📌 Lỗi:** {row['THÔNG BÁO LỖI']} — {row['MÔ TẢ LỖI']}")
            st.write(f"**🛠️ Cách xử lý:** {row['CÁCH XỬ LÍ']}")
            st.write("---")
    else:
        st.error("Xin lỗi, tôi không tìm thấy thông tin liên quan.")
