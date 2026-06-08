"""ChromaDB client wrapper."""
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from config import get_settings

settings = get_settings()


class ChromaClient:
    def __init__(self, host: str = None, port: int = None):
        try:
            self._client = chromadb.HttpClient(
                host=host or settings.chroma_host,
                port=port or settings.chroma_port,
            )
        except Exception:
            # Fallback to in-memory for local dev without Docker
            self._client = chromadb.Client()

        ef = SentenceTransformerEmbeddingFunction(model_name=settings.embedding_model)
        self.collection = self._client.get_or_create_collection(
            name=settings.chroma_collection,
            embedding_function=ef,
        )

    def query(self, text: str, n_results: int = 4) -> list[str]:
        try:
            results = self.collection.query(query_texts=[text], n_results=n_results)
            return results.get("documents", [[]])[0]
        except Exception:
            return []

    def upsert(self, ids: list, documents: list, metadatas: list = None):
        self.collection.upsert(ids=ids, documents=documents, metadatas=metadatas or [{}]*len(ids))
