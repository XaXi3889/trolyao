import re
import unicodedata
import streamlit as st
import pandas as pd
from rapidfuzz import fuzz
import base64
from gtts import gTTS
import speech_recognition as sr
from io import BytesIO
from pydub import AudioSegment

st.set_page_config(page_title="Trợ lý ảo QCC 3", layout="centered")

# === Hàm set background từ file ảnh local ===
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

# Gọi hàm để set background
set_bg_from_local("bencang.jpg")

st.title("🤖 Trợ lý ảo QCC 3")
st.caption("Bạn có thể gõ từ khoá hoặc dùng giọng nói để tra cứu.")

# ============ Helpers ============
def normalize(s: str) -> str:
    """Bỏ dấu, ký tự đặc biệt, viết thường, rút gọn khoảng trắng."""
    s = unicodedata.normalize('NFD', str(s))
    s = ''.join(ch for ch in s if unicodedata.category(ch) != 'Mn')
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def render_row(row, prefix=""):
    # Nội dung hiển thị
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

    # === TTS tự động đọc ===
    text = f"Lỗi: {row['TB']} — {row['MT']}. Cách xử lý: {row['CXL']}"
    tts = gTTS(text=text, lang="vi")
    tts.save("tts_output.mp3")
    with open("tts_output.mp3", "rb") as f:
        st.audio(f.read(), format="audio/mp3", autoplay=True)

@st.cache_data
def load_data():
    df = pd.read_excel("QCC3.xlsx", sheet_name=0, header=1)
    # Chuẩn hoá tên cột
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

# =================== Input ===================
tab1, tab2 = st.tabs(["⌨️ Gõ từ khoá", "🎙️ Giọng nói"])

with tab1:
    q_raw = st.text_input("Bạn muốn hỏi gì?", placeholder="VD: Ngáng mắt đèn xanh")

with tab2:
    audio_file = st.file_uploader("Thu âm giọng nói (định dạng WAV/MP3)", type=["wav", "mp3"])
    q_raw = None
    if audio_file:
        # Lưu file tạm
        sound = AudioSegment.from_file(audio_file)
        wav_io = BytesIO()
        sound.export(wav_io, format="wav")
        wav_io.seek(0)

        # Nhận diện giọng nói
        r = sr.Recognizer()
        with sr.AudioFile(wav_io) as source:
            audio = r.record(source)
            try:
                q_raw = r.recognize_google(audio, language="vi-VN")
                st.success(f"🎧 Bạn đã nói: **{q_raw}**")
            except:
                st.error("❌ Không nhận diện được giọng nói, vui lòng thử lại.")
from st_mic_recorder import mic_recorder

    st.subheader("🎙️ Hoặc bấm để nói trực tiếp")
    audio = mic_recorder(
        start_prompt="Bấm để nói 🎤",
        stop_prompt="Dừng 🛑",
        just_once=True,
        use_container_width=True
    )

    if audio:
        wav_file = "temp.wav"
        with open(wav_file, "wb") as f:
            f.write(audio["bytes"])

        r = sr.Recognizer()
        with sr.AudioFile(wav_file) as source:
            audio_data = r.record(source)
            try:
                q_raw = r.recognize_google(audio_data, language="vi-VN")
                st.success(f"🗣️ Bạn vừa nói: **{q_raw}**")
            except:
                st.error("❌ Không nhận diện được giọng nói, thử lại nhé.")

# =================== Search ===================
if q_raw:
    q = normalize(q_raw)
    keywords = q.split()

    # ---------- B1: Khớp từ khoá ----------
    def row_match_all(row):
        combined = row["TB_clean"] + " " + row["MT_clean"]
        return all(kw in combined for kw in keywords)

    matched = df[df.apply(row_match_all, axis=1)]

    if not matched.empty:
        best = matched.iloc[0]
        st.success("✅ Tìm thấy kết quả phù hợp.")
        render_row(best, prefix="✅ ")
        st.stop()

    # ---------- B2: Fuzzy ----------
    def fuzzy_score(row):
        combined = row["TB_clean"] + " " + row["MT_clean"]
        return fuzz.token_set_ratio(q, combined)

    df["score"] = df.apply(fuzzy_score, axis=1)
    best = df.sort_values("score", ascending=False).iloc[0]

    if best["score"] < 60:
        st.warning("⚠️ Không tìm thấy kết quả phù hợp. Vui lòng nhập/tìm lại từ khóa đặc thù hơn.")
    else:
        st.success("⭐ Kết quả gần nhất:")
        render_row(best, prefix="⭐ ")
