import re
import unicodedata
import streamlit as st
import pandas as pd
from rapidfuzz import fuzz, process

st.set_page_config(page_title="Trợ lý ảo QC C3", layout="centered")
st.title("🤖 Trợ lý ảo QC C3")
st.caption("Gõ từ khoá gần giống. App sẽ ưu tiên khớp chính xác trước khi dùng fuzzy.")

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
    # Hiện câu hỏi gốc (nếu muốn)
    st.write("**❓ Câu hỏi:** " + q_raw)

    # Chỉ hiện cách xử lý
    st.write("**✅ Trả lời:** " + row["CXL"])

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

    # ---------- B1: Khớp CHÍNH XÁC ----------
    exact_mask = (df["TB_clean"] == q) | (df["MT_clean"] == q)
    exact_rows = df[exact_mask]
    if not exact_rows.empty:
        st.success(f"Khớp chính xác {len(exact_rows)} kết quả.")
        for _, r in exact_rows.iterrows():
            render_row(r, prefix="✅ ")
        st.stop()

    # ---------- B2: Khớp chứa NGUYÊN TỪ ----------
    # an toàn vì ta đã normalize (chỉ còn a-z0-9 và space)
    patt = rf"\b{re.escape(q)}\b"
    contains_mask = df["TB_clean"].str.contains(patt) | df["MT_clean"].str.contains(patt)
    contain_rows = df[contains_mask]
    if not contain_rows.empty:
        st.info(f"Tìm thấy {len(contain_rows)} kết quả chứa nguyên từ.")
        # sắp xếp theo độ dài phần mô tả gần nhất với truy vấn (ngắn hơn thường sát hơn)
        contain_rows = contain_rows.assign(
            closeness=contain_rows.apply(
                lambda r: min(abs(len(r["TB_clean"]) - len(q)), abs(len(r["MT_clean"]) - len(q))), axis=1
            )
        ).sort_values("closeness")
        for _, r in contain_rows.head(3).iterrows():  # giới hạn 3 dòng
            render_row(r, prefix="🔎 ")
        st.stop()

    # ---------- B3: Fuzzy (rơi xuống cuối) ----------
    # Điểm tối đa giữa TB và MT, có trọng số ưu tiên TB
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
