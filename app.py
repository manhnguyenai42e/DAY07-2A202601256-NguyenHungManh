from __future__ import annotations

import hashlib
import os
import pickle
import sys
from pathlib import Path
import json
from flask import Flask, Response, jsonify, render_template, request, stream_with_context

# Ensure root directory is on python path
ROOT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(ROOT_DIR))

from ingest import build_knowledge_base, load_documents
from src.agent import KnowledgeBaseAgent
from src.chunking import RecursiveChunker
from src.embeddings import LOCAL_EMBEDDING_MODEL, LocalEmbedder, _mock_embed
from src.store import EmbeddingStore

app = Flask(__name__, template_folder="templates", static_folder="static")

DATA_DIR = ROOT_DIR / "data" / "k4_ecommerce"
EMBED_CACHE_PATH = ROOT_DIR / ".cache" / "embeddings_cache.pkl"

# Singletons
_embedder = None
_store = None
_agent = None


class CachedEmbedder:
    """Bọc quanh 1 embedding_fn bất kỳ, cache vector ra đĩa theo hash nội dung text.

    Tránh phải nhúng lại toàn bộ corpus (~10s+ với LocalEmbedder) mỗi khi app khởi
    động lại — ví dụ HF Spaces free tier sleep rồi wake lại. Lần chạy đầu tiên vẫn
    tốn thời gian nhúng như bình thường; các lần sau (nếu nội dung file .md không
    đổi) sẽ đọc thẳng từ cache.
    """

    def __init__(self, embedding_fn, cache_path: Path) -> None:
        self._embedding_fn = embedding_fn
        self._cache_path = cache_path
        self._writable = True
        try:
            self._cache_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as err:
            print(f"CachedEmbedder: cache dir not writable ({err}); running without persistent cache.")
            self._writable = False
        self._cache: dict[str, list[float]] = self._load()
        self._dirty = False

    def _load(self) -> dict:
        if self._writable and self._cache_path.exists():
            try:
                with open(self._cache_path, "rb") as f:
                    return pickle.load(f)
            except Exception:
                return {}
        return {}

    def save(self) -> None:
        if not self._dirty or not self._writable:
            return
        try:
            with open(self._cache_path, "wb") as f:
                pickle.dump(self._cache, f)
            self._dirty = False
        except OSError as err:
            print(f"CachedEmbedder: could not write cache file ({err}); continuing without it.")
            self._writable = False

    def __call__(self, text: str):
        key = hashlib.sha256(text.encode("utf-8")).hexdigest()
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        vector = self._embedding_fn(text)
        self._cache[key] = vector
        self._dirty = True
        return vector

def get_embedder():
    global _embedder
    if _embedder is None:
        try:
            print("Initializing LocalEmbedder (HuggingFace sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2)...")
            _embedder = LocalEmbedder(model_name=LOCAL_EMBEDDING_MODEL)
            print("LocalEmbedder loaded successfully!")
        except Exception as err:
            print(f"LocalEmbedder failed to load ({err}); falling back to mock embedder.")
            _embedder = _mock_embed
    return _embedder

def get_store():
    global _store
    if _store is None:
        embedder = get_embedder()
        cached_embedder = CachedEmbedder(embedder, EMBED_CACHE_PATH)
        cache_hits_before = len(cached_embedder._cache)
        print(f"Building EmbeddingStore from {DATA_DIR} using RecursiveChunker(chunk_size=500)...")
        _store = build_knowledge_base(
            DATA_DIR,
            embedding_fn=cached_embedder,
            chunker=RecursiveChunker(chunk_size=500),
            collection_name="shopee_policy_kb",
        )
        cached_embedder.save()
        print(
            f"EmbeddingStore initialized with {_store.get_collection_size()} chunks! "
            f"(embedding cache: {cache_hits_before} entries reused, "
            f"{len(cached_embedder._cache) - cache_hits_before} newly computed)"
        )
    return _store

def get_agent():
    global _agent
    if _agent is None:
        store = get_store()
        _agent = KnowledgeBaseAgent(store=store)
    return _agent

# Pre-warm model & vector store at server startup
try:
    print("Pre-warming KnowledgeBaseAgent & EmbeddingStore on server start...")
    get_agent()
except Exception as _err:
    print(f"Pre-warm status: {_err}")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat")
def chat_workspace():
    return render_template("chat.html")

@app.route("/api/documents", methods=["GET"])
def get_documents():
    docs = load_documents(DATA_DIR)
    result = []
    for d in docs:
        result.append({
            "id": d.id,
            "title": d.metadata.get("title", d.id),
            "customer_role": d.metadata.get("customer_role", "both"),
            "category": d.metadata.get("category", "general"),
            "source_url": d.metadata.get("source_url", ""),
            "retrieved_at": d.metadata.get("retrieved_at", ""),
            "document_version": d.metadata.get("document_version", ""),
            "content": d.content,
        })
    return jsonify(result)

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json or {}
    question = (data.get("question") or "").strip()
    role_filter = data.get("customer_role")  # "buyer", "seller", or None
    
    if not question:
        return jsonify({"error": "Question is required."}), 400

    agent = get_agent()
    response = agent.answer(question=question, top_k=3, customer_role=role_filter, return_dict=True)

    return jsonify({
        "question": question,
        "role_filter": role_filter,
        "answer": response["answer"],
        "sources": response["sources"],
    })

@app.route("/api/chat/stream", methods=["POST"])
def chat_stream():
    data = request.json or {}
    question = (data.get("question") or "").strip()
    role_filter = data.get("customer_role")

    if not question:
        return jsonify({"error": "Question is required."}), 400

    agent = get_agent()

    def generate():
        for event in agent.answer_stream(question=question, top_k=3, customer_role=role_filter):
            yield f"data: {json.dumps(event)}\n\n"

    return Response(stream_with_context(generate()), mimetype="text/event-stream")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    print(f"Starting Shopee Help Center Web Server on port {port} ...")
    app.run(host="0.0.0.0", port=port, debug=False)
