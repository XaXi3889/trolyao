import streamlit as st
import pandas as pd
from rapidfuzz import fuzz
import unicodedata

# ====== Chuẩn hóa text ======
def normalize_text(text):
    if pd.isna(text):
        return ""
    text = str(text)
    text = unicodedata.normalize("NFKC", text)
    return text.lower().strip()

# ====== Tìm kiếm dữ liệu ======
def search_data(df, query, threshold=60):
    query = normalize_text(query)
    best_match = None
    best_score = 0

    for _, row in df.iterrows():
        for col in ["TB", "CXL"]:  # tên cột trong Excel
            if col in row:
                text = normalize_text(row[col])
                score = fuzz.partial_ratio(query, text)
                if score > best_score:
                    best_score = score
                    best_match = row

    if best_score >= threshold:
        return best_match
    return None

# ====== Hàm auto speak ======
def auto_speak(text):
    js_code = f"""
    <script>
    var utterance = new SpeechSynthesisUtterance("{text}");
    utterance.lang = "vi-VN";
    utterance.rate = 1.0;   // tốc độ đọc (1.0 = bình thường)
    speechSynthesis.cancel();
    speechSynthesis.speak(utterance);
    </script>
    """
    st.markdown(js_code, unsafe_allow_html=True)

# ====== Giao diện ======
st.set_page_config(page_title="Trợ lý ảo QCC3", layout="centered")
st.title("🤖 Trợ lý ảo QCC3")

uploaded_file = st.file_uploader("📂 Tải file Excel dữ liệu", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Thêm input tìm kiếm
    query = st.text_input("🔍 Nhập từ khóa cần tra cứu:")

    if query:
        result = search_data(df, query)

        if result is not None:
            st.markdown("### ✅ Kết quả tìm thấy")
            st.write("**Lỗi:**", result["TB"])
            st.write("**Cách xử lý:**", result["CXL"])

            # Auto speak
            speak_text = f"Lỗi: {result['TB']}. Cách xử lý: {result['CXL']}"
            auto_speak(speak_text)

        else:
            st.warning("❌ Không tìm thấy kết quả phù hợp")
