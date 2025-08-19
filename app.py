import re
import unicodedata
import streamlit as st
import pandas as pd
from rapidfuzz import fuzz

# ================== CONFIG ==================
st.set_page_config(page_title="Trợ lý ảo QC C3", layout="centered")
st.title("🤖 Trợ lý ảo QC C3")
st.caption("Nhập từ khoá gần giống. App sẽ ưu tiên khớp chính xác trước khi fuzzy.")

# Ẩn khung lỗi mặc định của Streamlit
st.markdown(
    """
    <style>
    .stAlert {display: none;} /* ẩn lỗi mặc định */
    </style>
    """,
    unsafe_allow_html=True
)

# ================== HELPERS ==================
def normalize(s: str) -> str:
    """Bỏ dấu, ký tự đặc biệt, viết thường, rút gọn khoảng trắng"""
    s = unicodedata.normalize('NFD', str(s))
    s = ''.join(ch for ch in s if unicodedata.category(ch) != 'Mn')
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def render_row(row, prefix=""):
    st.markdown(prefix + "**📌 Lỗi:** " + row['TB'])
    st.markdown("**🛠️ Cách xử lý:** " + row['CXL'])
    st.divider()

@st.cache_data
def load_data():
    df = pd.read_excel("QCC3.xlsx", sheet_name=0, header=1)

    # Chuẩn hoá tên cột
    cols_norm = {normalize(c): c for c in df.columns}
    col_tb  = cols_norm[[k for k in cols_norm if "thong bao loi" in k][0]]
    col_mt  = cols_norm[[k for k in cols_norm if "mo ta loi" in k][0]]
    col_cxl = cols_norm[[k for k in cols_norm if ("cach xu li" in k or "cach xu ly" in k)][0]]

    df = df.rename(columns={col_tb:"TB", col_mt:"MT", col_cxl:"CXL"})
    for c in ["TB", "MT", "CXL"]:
        df[c] = df[c].astype(str).fillna("")

    df["TB_clean"] = df["TB"].map(normalize)
    df["MT_clean"] = df["MT"].map(normalize)
    return df[["TB", "MT", "CXL", "TB_clean", "MT_clean"]]

# ================== MAIN ==================
try:
    df = load_data()

    q_raw = st.text_input("👉 Bạn muốn hỏi gì?")
    strict = st.toggle("Chế độ nghiêm ngặt (chỉ trả về khi rất giống)", value=False)

    if q_raw:
        q = normalize(q_raw)

        # ---- B1: Exact match ----
        exact_mask = (df["TB_clean"] == q) | (df["MT_clean"] == q)
        exact_rows = df[exact_mask]
        if not exact_rows.empty:
            for _, r in exact_rows.iterrows():
                render_row(r, prefix="✅ ")
            st.stop()

        # ---- B2: Contains ----
        patt = re.escape(q)  # tránh lỗi regex
        contains_mask = df["TB_clean"].str.contains(patt) | df["MT_clean"].str.contains(patt)
        contain_rows = df[contains_mask]
        if not contain_rows.empty:
            for _, r in contain_rows.head(3).iterrows():
                render_row(r, prefix="🔎 ")
            st.stop()

        # ---- B3: Fuzzy ----
        title_scores = df["TB_clean"].apply(lambda s: fuzz.token_set_ratio(q, s))
        desc_scores  = df["MT_clean"].apply(lambda s: fuzz.token_set_ratio(q, s))
        final_score  = 0.7 * title_scores + 0.3 * desc_scores
        df_scored = df.assign(score=final_score).sort_values("score", ascending=False)

        cutoff = 85 if strict else 60
        top = df_scored[df_scored["score"] >= cutoff].head(3)

        if top.empty:
            st.warning("⚠️ Chưa tìm được kết quả phù hợp. Hãy nhập thêm từ khoá đặc thù.")
        else:
            for _, r in top.iterrows():
                render_row(r, prefix=f"⭐ (~{r['score']:.0f}%) ")

except Exception:
    st.error("⚠️ Xin lỗi, đã xảy ra lỗi. Vui lòng thử lại.")
