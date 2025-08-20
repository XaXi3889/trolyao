import re
import unicodedata
import streamlit as st
import pandas as pd
from rapidfuzz import fuzz
import base64   # 👈 thêm dòng này
from gtts import gTTS
import tempfile

def speak_text(text):
    """Chuyển văn bản thành giọng nói tiếng Việt và phát trên Streamlit"""
    tts = gTTS(text=text, lang="vi")
    with tempfile.NamedTemporaryFile(delete=True, suffix=".mp3") as tmp:
        tts.save(tmp.name)
        st.audio(tmp.name, format="audio/mp3")
        
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
st.caption("Bạn chỉ cần gõ các từ khoá liên quan (không cần chính xác tuyệt đối).")

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

# =================== Search ===================
q_raw = st.text_input("Bạn muốn hỏi gì? (gõ từ khoá lỗi)", placeholder="VD: Ngáng mắt đèn xanh")
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
        speak_text(f"Lỗi: {best['TB']}. Cách xử lý: {best['CXL']}")
        st.stop()

    # ---------- B2: Fuzzy ----------
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
        speak_text(f"Lỗi: {best['TB']}. Cách xử lý: {best['CXL']}")

