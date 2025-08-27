import re
import unicodedata
import streamlit as st
import pandas as pd
from rapidfuzz import fuzz
import base64
from gtts import gTTS
import speech_recognition as sr  # Thêm thư viện nhận dạng giọng nói

st.set_page_config(page_title="Trợ lý ảo QCC 3", layout="centered")

def set_bg_from_local(image_file):
    with open(image_file, "rb") as f:
        data = f.read()
    encoded = base64.b64encode(data).decode()
    css = f"""
    <style>
    .stApp {{
        background-image: url("data:image/jpg;base64,{encoded}");
        background-size: cover;
        background-repeat: no-repeat;
        background-position: center;
        background-attachment: fixed;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

set_bg_from_local("bencang.jpg")

st.title("🤖 Trợ lý ảo QCC 3")
st.caption("Bạn chỉ cần gõ hoặc nói các từ khoá liên quan (không cần chính xác tuyệt đối).")

def normalize(s: str) -> str:
    s = unicodedata.normalize('NFD', str(s))
    s = ''.join(ch for ch in s if unicodedata.category(ch) != 'Mn')
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def render_row(row, prefix=""):
    st.markdown(
        f"""
        <div style="padding:12px; border-radius:12px; background:#f8f9fa; margin-bottom:12px; box-shadow:0 2px 6px rgba(0,0,0,0.08)">
            <p style="margin:0; font-weight:bold; color:#d6336c;">📌 Lỗi:</p>
            <p style="margin:4px 0; font-size:15px;">{row['TB']} — {row['MT']}</p>
            <p style="margin:0; font-weight:bold; color:#2f9e44;">🛠️ Cách xử lý:</p>
            <p style="margin:4px 0; font-size:15px; white-space:pre-line;">{row['CXL']}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    text = f"Lỗi: {row['TB']} — {row['MT']}. Cách xử lý: {row['CXL']}"
    tts = gTTS(text=text, lang="vi")
    tts.save("tts_output.mp3")
    with open("tts_output.mp3", "rb") as f:
        st.audio(f.read(), format="audio/mp3", autoplay=True)

@st.cache_data
def load_data():
    df = pd.read_excel("QCC3.xlsx", sheet_name=0, header=1)
    cols_norm = {normalize(c): c for c in df.columns}
    col_bp  = cols_norm[[k for k in cols_norm if "bo phan" in k][0]]
    col_tb  = cols_norm[[k for k in cols_norm if "thong bao loi" in k][0]]
    col_mt  = cols_norm[[k for k in cols_norm if "mo ta loi" in k][0]]
    col_cxl = cols_norm[[k for k in cols_norm if ("cach xu li" in k or "cach xu ly" in k)][0]]

    df = df.rename(columns={col_bp:"BP", col_tb:"TB", col_mt:"MT", col_cxl:"CXL"})
    for c in ["BP", "TB", "MT", "CXL"]:
        df[c] = df[c].astype(str).fillna("")

    df["TB_clean"] = df["TB"].map(normalize)
    df["MT_clean"] = df["MT"].map(normalize)
    return df[["BP", "TB", "MT", "CXL", "TB_clean", "MT_clean"]]

df = load_data()

# --- Nhận giọng nói ---
def speech_to_text():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source:
        st.info("🎙️ Vui lòng nói từ khoá lỗi...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source, phrase_time_limit=5)
    try:
        text = recognizer.recognize_google(audio, language="vi-VN")
        st.success(f"Bạn đã nói: {text}")
        return text
    except sr.UnknownValueError:
        st.error("Không nhận diện được giọng nói. Vui lòng thử lại.")
        return ""
    except sr.RequestError as e:
        st.error(f"Lỗi kết nối dịch vụ nhận dạng giọng nói: {e}")
        return ""

# --- Streamlit UI ---
mode = st.radio("Chọn phương thức nhập:", ["Gõ từ khoá", "Nói từ khoá"])

if mode == "Gõ từ khoá":
    q_raw = st.text_input("Bạn muốn hỏi gì? (gõ từ khoá lỗi)", placeholder="VD: Ngáng mắt đèn xanh")
else:
    if st.button("Nhấn để nói"):
        q_raw = speech_to_text()
    else:
        q_raw = ""

if q_raw:
    q = normalize(q_raw)
    keywords = q.split()

    def row_match_all(row):
        combined = row["TB_clean"] + " " + row["MT_clean"]
        return all(kw in combined for kw in keywords)

    matched = df[df.apply(row_match_all, axis=1)]

    if not matched.empty:
        best = matched.iloc[0]
        st.success("✅ Tìm thấy kết quả phù hợp.")
        render_row(best, prefix="✅ ")
        st.stop()

    def fuzzy_score(row):
        combined = row["TB_clean"] + " " + row["MT_clean"]
        return fuzz.token_set_ratio(q, combined)

    df["score"] = df.apply(fuzzy_score, axis=1)
    best = df.sort_values("score", ascending=False).iloc[0]

    if best["score"] < 60:
        st.warning("⚠️ Không tìm thấy kết quả phù hợp. Vui lòng nhập từ khóa đặc thù hơn.")
    else:
        st.success("⭐ Kết quả gần nhất:")
        render_row(best, prefix="⭐ ")
