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
    combined = df.apply(lambda row: " ".join(row.values), axis=1)

    # Lấy ra kết quả gần nhất
    best_match = process.extractOne(q, combined, scorer=fuzz.partial_ratio)

    if best_match:
        matched_text, score, idx = best_match
        if score >= 60:   # ngưỡng độ giống (có thể chỉnh 50–70)
            st.success(f"🔎 Tôi tìm thấy kết quả gần nhất (độ giống {score}%):")
            st.dataframe(df.iloc[[idx]])
        else:
            st.error("Xin lỗi, tôi không tìm thấy thông tin phù hợp.")
    else:
        st.error("Xin lỗi, tôi không tìm thấy thông tin phù hợp.")
