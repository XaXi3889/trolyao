import streamlit as st
import pandas as pd
from rapidfuzz import fuzz, process   # fuzzy search

st.title("🤖 Trợ lý ảo QC C3")
st.write("Xin chào, tôi là trợ lý ảo của bạn!")

@st.cache_data
def load_data():
    df = pd.read_excel("QCC3.xlsx", sheet_name=0)
    df = df.astype(str).apply(lambda x: x.str.lower().str.strip())
    return df

df = load_data()

question = st.text_input("Bạn muốn hỏi gì?")

if question:
    q = question.lower().strip()

    # Ghép tất cả các cột thành 1 chuỗi để tìm
    df["combined"] = df.apply(lambda row: " ".join(row.values), axis=1)

    # fuzzy search: lấy ra những dòng có độ giống nhau > 70
    matches = df[df["combined"].apply(lambda x: fuzz.partial_ratio(q, x) > 70)]

    if not matches.empty:
        st.success("Tôi tìm thấy thông tin gần giống sau:")
        st.dataframe(matches)
    else:
        st.error("Xin lỗi, tôi không tìm thấy thông tin liên quan.")
