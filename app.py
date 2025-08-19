import streamlit as st
import pandas as pd

st.title("🤖 Trợ lý ảo QC C3")
st.write("Xin chào, tôi là trợ lý ảo của bạn!")

# Đọc file Excel
@st.cache_data
def load_data():
    return pd.read_excel("QCC3.xlsx")

df = load_data()

# Cho phép người dùng nhập câu hỏi
question = st.text_input("Bạn muốn hỏi gì?")

if question:
    # Tìm kiếm trong dữ liệu
    ket_qua = df[df.apply(lambda row: row.astype(str).str.contains(question, case=False).any(), axis=1)]
    
    if not ket_qua.empty:
        st.success("Tôi tìm thấy thông tin sau:")
        st.dataframe(ket_qua)
    else:
        st.error("Xin lỗi, tôi không tìm thấy thông tin liên quan.")
