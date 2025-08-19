import re
import unicodedata
import streamlit as st
import pandas as pd
from rapidfuzz import fuzz

st.set_page_config(page_title="Trợ lý ảo QC C3", layout="centered")
st.title("🤖 Trợ lý ảo QC C3")
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
    st.markdown(prefix + "**📌 Lỗi:**")
    st.text(f"{row['TB']} — {row['MT']}")
    st.markdown("**🛠️ Cách xử lý:**")
    st.text(row["CXL"])
    st.divider()

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
q_raw = st.text_input("Bạn muốn hỏi gì?")
if q_raw:
    q = normalize(q_raw)
    keywords = q.split()  # tách thành nhiều từ

    # ---------- B1: Tìm các dòng chứa TẤT CẢ từ khoá ----------
    def row_match_all(row):
        combined = row["TB_clean"] + " " + row["MT_clean"]
        return all(kw in combined for kw in keywords)

    matched = df[df.apply(row_match_all, axis=1)]

    if not matched.empty:
        # lấy kết quả đầu tiên
        best = matched.iloc[0]
        st.success("✅ Tìm thấy kết quả khớp tất cả từ khóa.")
        render_row(best, prefix="✅ ")
        st.stop()

    # ---------- B2: Fuzzy fallback ----------
    def fuzzy_score(row):
        combined = row["TB_clean"] + " " + row["MT_clean"]
        return fuzz.token_set_ratio(q, combined)

    df["score"] = df.apply(fuzzy_score, axis=1)
    best = df.sort_values("score", ascending=False).iloc[0]

    if best["score"] < 60:
        st.error("Không tìm thấy kết quả đủ giống. Thử nhập từ khoá đặc thù hơn.")
    else:
        st.info(f"Kết quả giống nhất (~{best['score']:.0f}%):")
        render_row(best, prefix="⭐ ")
