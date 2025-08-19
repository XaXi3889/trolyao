import re
import unicodedata
import streamlit as st
import pandas as pd
from rapidfuzz import fuzz

st.set_page_config(page_title="Trợ lý ảo QC C3", layout="centered")
st.title("🤖 Trợ lý ảo QC C3")
st.caption("Gõ từ khoá gần giống. App sẽ ưu tiên khớp chính xác hoặc chứa, sau đó mới dùng fuzzy.")

# ============ Helpers ============
def normalize(s: str) -> str:
    """Bỏ dấu, bỏ ký tự đặc biệt, viết thường, rút gọn khoảng trắng."""
    s = unicodedata.normalize('NFD', str(s))
    s = ''.join(ch for ch in s if unicodedata.category(ch) != 'Mn')  # remove accents
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)  # strip non-alnum
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
    # Header ở dòng 2
    df = pd.read_excel("QCC3.xlsx", sheet_name=0, header=1)

    # Tìm tên cột theo dạng chuẩn hoá để tránh sai chính tả/dấu
    cols_norm = {normalize(c): c for c in df.columns}
    try:
        col_bp  = cols_norm[[k for k in cols_norm if "bo phan" in k][0]]
        col_tb  = cols_norm[[k for k in cols_norm if "thong bao loi" in k][0]]
        col_mt  = cols_norm[[k for k in cols_norm if "mo ta loi" in k][0]]
        col_cxl = cols_norm[[k for k in cols_norm if ("cach xu li" in k or "cach xu ly" in k)][0]]
    except IndexError:
        st.error("Thiếu cột: 'Bộ phận' / 'THÔNG BÁO LỖI' / 'MÔ TẢ LỖI' / 'CÁCH XỬ LÍ' trong Excel.")
        st.stop()

    df = df.rename(columns={col_bp:"BP", col_tb:"TB", col_mt:"MT", col_cxl:"CXL"})
    for c in ["BP", "TB", "MT", "CXL"]:
        df[c] = df[c].astype(str).fillna("")

    df["TB_clean"] = df["TB"].map(normalize)
    df["MT_clean"] = df["MT"].map(normalize)
    return df[["BP", "TB", "MT", "CXL", "TB_clean", "MT_clean"]]

df = load_data()

q_raw = st.text_input("Bạn muốn hỏi gì?")
strict = st.toggle("Chế độ nghiêm ngặt (chỉ trả về khi rất giống)", value=False)

if q_raw:
    q = normalize(q_raw)

    # ---------- B1: Khớp chính xác hoặc CHỨA (cả 2 chiều) ----------
    mask_exact = (df["TB_clean"] == q) | (df["MT_clean"] == q)
    mask_contained = df["TB_clean"].apply(lambda s: s in q) | df["MT_clean"].apply(lambda s: s in q)
    exact_rows = df[mask_exact | mask_contained]
    if not exact_rows.empty:
        st.success(f"Khớp chính xác / chứa ({len(exact_rows)} kết quả).")
        for _, r in exact_rows.iterrows():
            render_row(r, prefix="✅ ")
        st.stop()

    # ---------- B2: Khớp chứa CHUỖI (không regex) ----------
    contains_mask = df["TB_clean"].str.contains(q, case=False, regex=False) | \
                    df["MT_clean"].str.contains(q, case=False, regex=False)
    contain_rows = df[contains_mask]
    if not contain_rows.empty:
        st.info(f"Tìm thấy {len(contain_rows)} kết quả chứa.")
        contain_rows = contain_rows.assign(
            closeness=contain_rows.apply(
                lambda r: min(abs(len(r["TB_clean"]) - len(q)), abs(len(r["MT_clean"]) - len(q))), axis=1
            )
        ).sort_values("closeness")
        for _, r in contain_rows.head(3).iterrows():  # giới hạn 3 dòng
            render_row(r, prefix="🔎 ")
        st.stop()

    # ---------- B3: Fuzzy (cuối cùng) ----------
    title_scores = df["TB_clean"].apply(lambda s: fuzz.token_set_ratio(q, s))
    desc_scores  = df["MT_clean"].apply(lambda s: fuzz.token_set_ratio(q, s))
    final_score  = 0.7 * title_scores + 0.3 * desc_scores
    df_scored = df.assign(score=final_score).sort_values("score", ascending=False)

    cutoff = 85 if strict else 60
    top = df_scored[df_scored["score"] >= cutoff].head(3)

    if top.empty:
        st.error("Chưa tìm được kết quả đủ giống. Hãy thêm vài từ khoá đặc thù (trolley, gantry, đèn xanh/đỏ, limit…).")
    else:
        st.success(f"Top {len(top)} kết quả gần nhất (độ giống cao nhất ~{top.iloc[0]['score']:.0f}%).")
        for _, r in top.iterrows():
            render_row(r, prefix=f"⭐ (~{r['score']:.0f}%) ")
