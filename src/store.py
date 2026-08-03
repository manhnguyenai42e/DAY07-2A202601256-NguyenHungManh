from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb

            client = chromadb.Client()
            self._collection = client.get_or_create_collection(name=collection_name)
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        embedding = self._embedding_fn(doc.content)
        metadata = dict(doc.metadata) if doc.metadata else {}
        return {
            "id": doc.id,
            "content": doc.content,
            "metadata": metadata,
            "embedding": embedding,
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        if not records:
            return []
        query_emb = self._embedding_fn(query)
        scored_records = []
        for r in records:
            score = _dot(query_emb, r["embedding"])
            record_copy = {
                "id": r["id"],
                "content": r["content"],
                "metadata": r.get("metadata", {}),
                "score": score,
            }
            scored_records.append(record_copy)
        scored_records.sort(key=lambda x: x["score"], reverse=True)
        return scored_records[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        if not docs:
            return
        if self._use_chroma and self._collection is not None:
            ids = [doc.id for doc in docs]
            documents = [doc.content for doc in docs]
            embeddings = [self._embedding_fn(doc.content) for doc in docs]
            metadatas = [doc.metadata for doc in docs]
            self._collection.add(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)
        else:
            for doc in docs:
                self._store.append(self._make_record(doc))

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        if self._use_chroma and self._collection is not None:
            q_emb = self._embedding_fn(query)
            res = self._collection.query(query_embeddings=[q_emb], n_results=top_k)
            out = []
            if res and res.get("documents"):
                for i in range(len(res["documents"][0])):
                    doc_id = res["ids"][0][i]
                    content = res["documents"][0][i]
                    metadata = res["metadatas"][0][i] if res.get("metadatas") else {}
                    dist = res["distances"][0][i] if res.get("distances") else 0.0
                    out.append({"id": doc_id, "content": content, "metadata": metadata, "score": 1.0 - dist})
            return out
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        if self._use_chroma and self._collection is not None:
            return self._collection.count()
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if not metadata_filter:
            return self.search(query, top_k=top_k)

        if self._use_chroma and self._collection is not None:
            q_emb = self._embedding_fn(query)
            res = self._collection.query(query_embeddings=[q_emb], n_results=top_k, where=metadata_filter)
            out = []
            if res and res.get("documents"):
                for i in range(len(res["documents"][0])):
                    doc_id = res["ids"][0][i]
                    content = res["documents"][0][i]
                    metadata = res["metadatas"][0][i] if res.get("metadatas") else {}
                    dist = res["distances"][0][i] if res.get("distances") else 0.0
                    out.append({"id": doc_id, "content": content, "metadata": metadata, "score": 1.0 - dist})
            return out

        filtered_records = []
        for r in self._store:
            meta = r.get("metadata", {})
            matches = all(meta.get(k) == v for k, v in metadata_filter.items())
            if matches:
                filtered_records.append(r)
        return self._search_records(query, filtered_records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        if self._use_chroma and self._collection is not None:
            try:
                self._collection.delete(ids=[doc_id])
                return True
            except Exception:
                return False

        initial_len = len(self._store)
        self._store = [
            r for r in self._store
            if r.get("id") != doc_id and r.get("metadata", {}).get("doc_id") != doc_id
        ]
        return len(self._store) < initial_len
