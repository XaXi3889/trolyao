import re
import streamlit as st
import pandas as pd
from rapidfuzz import process, fuzz
from unidecode import unidecode

st.set_page_config(page_title="Trợ lý ảo QC C3", layout="centered")
st.title("🤖 Trợ lý ảo QC C3")
st.caption("Gõ từ khoá gần giống (ví dụ: 'mất đèn xanh trolley')")

# ---------- Helpers ----------
def normalize(s: str) -> str:
    s = unidecode(str(s).lower())
    s = re.sub(r"[^a-z0-9\s]", " ", s)   # bỏ ký tự đặc biệt
    s = re.sub(r"\s+", " ", s).strip()
    return s

@st.cache_data
def load_data():
    # Header ở dòng 2 của Excel
    df = pd.read_excel("QCC3.xlsx", sheet_name=0, header=1)

    # Đổi tên cột về dạng chuẩn, chịu được khác biệt chính tả/dấu
    cols_norm = {normalize(c): c for c in df.columns}
    col_bp  = cols_norm[[k for k in cols_norm if "bo phan" in k][0]]
    col_tb  = cols_norm[[k for k in cols_norm if "thong bao loi" in k][0]]
    col_mt  = cols_norm[[k for k in cols_norm if "mo ta loi" in k][0]]
    col_cxl = cols_norm[[k for k in cols_norm if ("cach xu li" in k or "cach xu ly" in k)][0]]

    df = df.rename(columns={
        col_bp: "BP", col_tb: "TB", col_mt: "MT", col_cxl: "CXL"
    })

    # Bản sạch để so khớp
    for c in ["BP", "TB", "MT", "CXL"]:
        df[c] = df[c].astype(str).fillna("")

    df["TB_clean"] = df["TB"].map(normalize)
    df["MT_clean"] = df["MT"].map(normalize)
    return df[["BP", "TB", "MT", "CXL", "TB_clean", "MT_clean"]]

df = load_data()

q_raw = st.text_input("Bạn muốn hỏi gì?")
if q_raw:
    q = normalize(q_raw)

    # Tính điểm có trọng số: TB 70% + MT 30%
    title_matches = process.extract(q, df["TB_clean"], scorer=fuzz.token_set_ratio, limit=20)
    desc_matches  = process.extract(q, df["MT_clean"], scorer=fuzz.token_set_ratio, limit=20)

    scores = {}
    for _, s, idx in title_matches:
        scores[idx] = scores.get(idx, 0) + 0.7 * s
    for _, s, idx in desc_matches:
        scores[idx] = scores.get(idx, 0) + 0.3 * s

    top = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]  # lấy top 3
    if not top or top[0][1] < 55:  # ngưỡng tự chỉnh
        st.error("Chưa tìm được kết quả đủ giống. Thử từ khoá khác (ví dụ thêm 'trolley', 'gantry', 'đèn xanh', …).")
    else:
        st.success(f"Đã tìm thấy {len(top)} kết quả gần nhất (độ giống cao nhất ~{top[0][1]:.0f}%).")
        for rank, (idx, score) in enumerate(top, 1):
            row = df.loc[idx]
            st.markdown(f"**#{rank} • Độ giống ~{score:.0f}%**")
            st.markdown("**📌 Lỗi:**")
            st.text(f"{row['TB']} — {row['MT']}")
            st.markdown("**🛠️ Cách xử lý:**")
            st.text(row["CXL"])
            st.divider()
