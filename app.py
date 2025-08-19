import re
import unicodedata
import streamlit as st
import pandas as pd
from rapidfuzz import fuzz

st.set_page_config(page_title="Trợ lý ảo QC C3", layout="centered")

st.markdown("<h2 style='text-align:center;'>🤖 Trợ lý ảo QC C3</h2>", unsafe_allow_html=True)

# ============ Helpers ============
def normalize(s: str) -> str:
    s = unicodedata.normalize('NFD', str(s))
    s = ''.join(ch for ch in s if unicodedata.category(ch) != 'Mn')
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def render_user_msg(msg: str):
    st.markdown(
        f"""
        <div style="display:flex; justify-content:flex-end; margin:8px 0;">
            <div style="background:#0d6efd; color:white; padding:10px 14px; border-radius:16px; max-width:75%; word-wrap:break-word;">
                {msg}
            </div>
        </div>
        """, unsafe_allow_html=True
    )

def render_bot_msg(title: str, tb: str, mt: str, cxl: str):
    st.markdown(
        f"""
        <div style="display:flex; justify-content:flex-start; margin:8px 0;">
            <div style="background:#f1f3f5; color:black; padding:12px; border-radius:16px; max-width:80%; word-wrap:break-word;">
                <p style="margin:0; font-weight:bold; color:#d6336c;">📌 {title}</p>
                <p style="margin:4px 0; font-size:15px;">{tb} — {mt}</p>
                <p style="margin:0; font-weight:bold; color:#2f9e44;">🛠️ Cách xử lý:</p>
                <p style="margin:4px 0; font-size:15px; white-space:pre-line;">{cxl}</p>
            </div>
        </div>
        """, unsafe_allow_html=True
    )

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

# =================== Chat ===================
q_raw = st.text_input("💬 Nhập câu hỏi (VD: Ngáng mắt đèn xanh)", key="user_input")
if q_raw:
    render_user_msg(q_raw)  # hiển thị tin nhắn người dùng

    q = normalize(q_raw)
    keywords = q.split()

    # ---------- B1: Khớp từ khóa ----------
    def row_match_all(row):
        combined = row["TB_clean"] + " " + row["MT_clean"]
        return all(kw in combined for kw in keywords)

    matched = df[df.apply(row_match_all, axis=1)]

    if not matched.empty:
        best = matched.iloc[0]
        render_bot_msg("✅ Kết quả tìm thấy", best["TB"], best["MT"], best["CXL"])
    else:
        # ---------- B2: Fuzzy ----------
        def fuzzy_score(row):
            combined = row["TB_clean"] + " " + row["MT_clean"]
            return fuzz.token_set_ratio(q, combined)

        df["score"] = df.apply(fuzzy_score, axis=1)
        best = df.sort_values("score", ascending=False).iloc[0]

        if best["score"] < 60:
            render_bot_msg("⚠️ Không tìm thấy", "N/A", "Không có mô tả phù hợp", "Hãy nhập từ khóa đặc thù hơn.")
        else:
            render_bot_msg("⭐ Kết quả gần nhất", best["TB"], best["MT"], best["CXL"])
