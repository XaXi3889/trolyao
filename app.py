import re, unicodedata
import streamlit as st
import pandas as pd
from rapidfuzz import fuzz

# Cấu hình đầu trang
st.set_page_config(page_title="QC C3 Chat Assistant", layout="centered")
st.markdown(
    """<style>
    .stApp { max-width: 500px; margin: 0 auto; }
    .user-msg { display:flex; justify-content:flex-end; margin:8px 0;}
    .user-msg div { background:#0d6efd; color:white; padding:8px 12px; border-radius:12px; max-width:80%; word-wrap:break-word; font-size:16px; }
    .bot-msg { display:flex; justify-content:flex-start; margin:8px 0; }
    .bot-msg div { background:#f1f3f5; color:black; padding:10px 14px; border-radius:12px; max-width:80%; word-wrap:break-word; font-size:16px; }
    </style>""",
    unsafe_allow_html=True
)

# Helper functions
def normalize(s: str) -> str:
    s = unicodedata.normalize('NFD', str(s))
    s = ''.join(ch for ch in s if unicodedata.category(ch) != 'Mn')
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def show_user(msg):
    st.markdown(f'<div class="user-msg"><div>{msg}</div></div>', unsafe_allow_html=True)

def show_bot(title, tb, mt, cxl):
    content = f"<strong>{title}</strong><br/>{tb} — {mt}<br/><em>Cách xử lý:</em> {cxl}"
    st.markdown(f'<div class="bot-msg"><div>{content}</div></div>', unsafe_allow_html=True)

@st.cache_data
def load_data():
    df = pd.read_excel("QCC3.xlsx", sheet_name=0, header=1)
    cols = {normalize(c): c for c in df.columns}
    col_tb = cols[[k for k in cols if "thong bao loi" in k][0]]
    col_mt = cols[[k for k in cols if "mo ta loi" in k][0]]
    col_cxl= cols[[k for k in cols if "cach xu ly" in k or "cach xu li" in k][0]]
    df = df.rename(columns={col_tb:"TB", col_mt:"MT", col_cxl:"CXL"})
    for c in ["TB","MT","CXL"]: df[c]=df[c].astype(str).fillna("")
    df["TB_clean"]=df["TB"].map(normalize)
    df["MT_clean"]=df["MT"].map(normalize)
    return df

df = load_data()

# Nhập câu hỏi từ người dùng
q_raw = st.text_input("Nhập từ khóa lỗi...", placeholder="Ví dụ: mất đèn đỏ sensor")
if q_raw:
    show_user(q_raw)
    q = normalize(q_raw)

    # B1: exact match
    mask = (df["TB_clean"]==q) | (df["MT_clean"]==q)
    exact = df[mask]
    if not exact.empty:
        r = exact.iloc[0]
        show_bot("Kết quả chính xác", r["TB"], r["MT"], r["CXL"])
        st.stop()

    # B2: contains
    mask2 = df["TB_clean"].str.contains(q, regex=False) | df["MT_clean"].str.contains(q, regex=False)
    contain = df[mask2]
    if not contain.empty:
        r = contain.iloc[0]
        show_bot("Khớp chứa", r["TB"], r["MT"], r["CXL"])
        st.stop()

    # B3: fuzzy
    df["score"] = df.apply(lambda row: fuzz.token_set_ratio(q, row["TB_clean"]+" "+row["MT_clean"]), axis=1)
    top = df.sort_values("score", ascending=False).iloc[0]
    if top["score"]<60:
        show_bot("Không tìm thấy", "---", "Không đủ giống", "Hãy thử từ khóa khác rõ hơn!")
    else:
        show_bot("Kết quả gần nhất", top["TB"], top["MT"], top["CXL"])
