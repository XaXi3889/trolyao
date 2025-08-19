import re, unicodedata
import streamlit as st
import pandas as pd
from rapidfuzz import fuzz

st.set_page_config(page_title="Trợ lý ảo QCC 3", layout="centered")
st.title("🤖 Trợ lý ảo QCC 3")
st.caption("Bạn chỉ cần gõ các từ khoá liên quan (không cần chính xác tuyệt đối).")

# ============ Helpers ============
def normalize(s: str) -> str:
    s = unicodedata.normalize('NFD', str(s))
    s = ''.join(ch for ch in s if unicodedata.category(ch) != 'Mn')
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", s.lower())).strip()

def render_row(row):
    st.markdown(f"""
    <div style="padding:12px; border-radius:12px; background:#f8f9fa; margin-bottom:12px; box-shadow:0 2px 6px rgba(0,0,0,0.08)">
        <p style="margin:0; font-weight:bold; color:#d6336c;">📌 Lỗi:</p>
        <p style="margin:4px 0; font-size:15px;">{row['TB']} — {row['MT']}</p>
        <p style="margin:0; font-weight:bold; color:#2f9e44;">🛠️ Cách xử lý:</p>
        <p style="margin:4px 0; font-size:15px; white-space:pre-line;">{row['CXL']}</p>
    </div>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    df = pd.read_excel("QCC3.xlsx", sheet_name=0, header=1)
    cols = {normalize(c): c for c in df.columns}
    mapping = {
        "BP":  [k for k in cols if "bo phan" in k][0],
        "TB":  [k for k in cols if "thong bao loi" in k][0],
        "MT":  [k for k in cols if "mo ta loi" in k][0],
        "CXL": [k for k in cols if "cach xu l" in k][0],
    }
    df = df.rename(columns={v: k for k, v in mapping.items()})
    for c in ["BP","TB","MT","CXL"]: df[c] = df[c].astype(str).fillna("")
    df["TB_clean"], df["MT_clean"] = df["TB"].map(normalize), df["MT"].map(normalize)
    return df[["BP","TB","MT","CXL","TB_clean","MT_clean"]]

df = load_data()

# =================== Search ===================
q_raw = st.text_input("Bạn muốn hỏi gì? (gõ từ khoá lỗi)", placeholder="VD: Ngáng mắt đèn xanh")
if q_raw:
    q, keywords = normalize(q_raw), normalize(q_raw).split()

    # B1: Exact match
    matched = df[df.apply(lambda r: all(kw in (r["TB_clean"]+" "+r["MT_clean"]) for kw in keywords), axis=1)]
    if not matched.empty:
        st.success("✅ Tìm thấy kết quả phù hợp.")
        render_row(matched.iloc[0])
    else:
        # B2: Fuzzy
        df["score"] = df.apply(lambda r: fuzz.token_set_ratio(q, r["TB_clean"]+" "+r["MT_clean"]), axis=1)
        best = df.loc[df["score"].idxmax()]
        if best["score"] < 60:
            st.warning("⚠️ Không tìm thấy kết quả phù hợp. Vui lòng nhập từ khóa đặc thù hơn.")
        else:
            st.success("⭐ Kết quả gần nhất:")
            render_row(best)
