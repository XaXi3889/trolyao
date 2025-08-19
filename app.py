import streamlit as st

st.title("🤖 Trợ lý ảo")
st.write("Xin chào, tôi là trợ lý ảo của bạn!")

# Ô nhập câu hỏi
question = st.text_input("Bạn muốn hỏi gì?")

# Xử lý đơn giản
if question:
    st.success(f"Bạn vừa hỏi: {question}")
