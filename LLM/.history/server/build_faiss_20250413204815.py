# File này dùng để khởi tạo và nạp dữ liệu vào vector database
import chromadb
from chromadb.utils import embedding_functions

# Khởi tạo ChromaDB
chroma_client = chromadb.PersistentClient(path="vector_db")

# Tạo collection với model embedding
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

collection = chroma_client.get_or_create_collection(
    name="knowledge_base",
    embedding_function=sentence_transformer_ef
)

# [Thêm code xử lý tài liệu ở đây...]