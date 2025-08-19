import pandas as pd
import streamlit as st
from sentence_transformers import SentenceTransformer, util

# 1. Đọc dữ liệu từ Excel
file_path = "THỐNG KÊ LỖI QCC3.xlsx"
df = pd.read_excel(file_path)

# Ghép dữ liệu mỗi dòng thành 1 đoạn text
documents = []
for _, row in df.iterrows():
    row_text = " ".join([str(cell) for cell in row if pd.notna(cell)])
    documents.append(row_text)

# 2. Tạo mô hình embedding (chạy offline, không cần API)
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

# Encode toàn bộ dữ liệu thành vector
doc_embeddings = model.encode(documents, convert_to_tensor=True)

# 3. Giao diện Streamlit
st.set_page_config(page_title="CraneCare Assistant (Offline)", page_icon="🛠️", layout="centered")

st.title("🛠️ Trợ lý ảo CraneCare (Offline)")
st.write("Hỏi về lỗi cẩu, bảo dưỡng, sửa chữa...")

query = st.text_input("Nhập câu hỏi của bạn:")

if query:
    query_embedding = model.encode(query, convert_to_tensor=True)
    # Tìm câu giống nhất trong dữ liệu
    scores = util.cos_sim(query_embedding, doc_embeddings)[0]
    best_idx = int(scores.argmax())
    best_answer = documents[best_idx]

    st.success(best_answer)

    