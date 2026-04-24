import chromadb
from langchain_community.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import uuid # Import thư viện uuid để tạo ID duy nhất

embedding_model = SentenceTransformer("paraphrase-MiniLM-L12-v2")


def search_in_chroma_db(query_text, db_path="chroma_db", collection_name="caregiver", n_results=3):
    try:
        print(f"[SEARCH] Connecting to Chroma DB at '{db_path}', collection '{collection_name}'")
        client = chromadb.PersistentClient(path=db_path)
        collection = client.get_or_create_collection(collection_name)

        print(f"[SEARCH] Encoding query text: '{query_text}' using '{embedding_model.model_name}'")
        embedding = embedding_model.encode(query_text).tolist()

        print(f"[SEARCH] Performing query with top {n_results} results")
        results = collection.query(query_embeddings=[embedding], n_results=n_results)

        print(f"[SEARCH] Query completed. Found {len(results.get('ids', [[]])[0])} result(s).")
        return results
    except Exception as e:
        print(f"[ERROR][SEARCH] Failed to search in Chroma DB: {e}")
        return {"ids": [[]], "metadatas": [[]], "distances": [[]]}


def store_in_chroma_db(text, metadata, db_path="chroma_db", collection_name="caregiver"):
    try:
        print(f"[STORE] Connecting to Chroma DB at '{db_path}', collection '{collection_name}'")
        client = chromadb.PersistentClient(path=db_path)
        collection = client.get_or_create_collection(collection_name)

        print(f"[STORE] Encoding text for storage using '{embedding_model.model_name}'")
        # Sử dụng mô hình đã được thống nhất
        embedding = embedding_model.encode(text).tolist()

        # Tạo ID duy nhất bằng uuid
        doc_id = str(uuid.uuid4())
        print(f"[STORE] Adding document with ID: {doc_id}")
        collection.add(embeddings=[embedding], metadatas=[metadata], ids=[doc_id], documents=[text])
        print(f"[STORE] Text stored successfully.")
    except Exception as e:
        print(f"[ERROR][STORE] Failed to store in Chroma DB: {e}")


def embedding_model(folder_path, persist_directory="chroma_db"):
    try:
        print(f"[EMBEDDING] Loading .md files from '{folder_path}'")
        loader = DirectoryLoader(folder_path, glob="**/*.md")
        documents = loader.load()

        if not documents:
            print(f"[EMBEDDING] No .md files found in {folder_path}. Exiting.")
            return

        print(f"[EMBEDDING] Splitting {len(documents)} documents into chunks.")
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        docs = text_splitter.split_documents(documents)

        if not docs:
            print(f"[EMBEDDING] No chunks generated after splitting. Exiting.")
            return

        print(f"[EMBEDDING] Initializing ChromaDB client for persistence at '{persist_directory}'")
        client = chromadb.PersistentClient(path=persist_directory)

        collection_name = "caregiver" 
        print(f"[EMBEDDING] Getting or creating collection '{collection_name}'")
        collection = client.get_or_create_collection(name=collection_name)

        print(f"[EMBEDDING] Generating embeddings and adding to ChromaDB using '{embedding_model.model_name}'")
        embeddings_to_add = []
        metadatas_to_add = []
        ids_to_add = []
        documents_to_add = [] # Lưu trữ nội dung gốc vào ChromaDB để dễ dàng truy xuất

        for i, doc in enumerate(docs):
            embedding_vec = embedding_model.encode(doc.page_content).tolist()
            embeddings_to_add.append(embedding_vec)
            metadatas_to_add.append(doc.metadata) # metadata từ Langchain loader
            ids_to_add.append(str(uuid.uuid4())) # Tạo ID cho chunk
            documents_to_add.append(doc.page_content) # Lưu nội dung chunk

            # In tiến trình mỗi 100 chunks
            if (i + 1) % 100 == 0:
                print(f"[EMBEDDING] Processed {i + 1}/{len(docs)} chunks.")

        print(f"[EMBEDDING] Adding {len(embeddings_to_add)} embeddings to ChromaDB.")
        collection.add(
            embeddings=embeddings_to_add,
            metadatas=metadatas_to_add,
            ids=ids_to_add,
            documents=documents_to_add # Thêm nội dung vào ChromaDB
        )

        print(f"Indexed {len(docs)} markdown chunks from '{folder_path}' into '{persist_directory}' (collection: '{collection_name}').")

    except Exception as e:
        print(f"[ERROR][EMBEDDING] An error occurred during embedding process: {e}")