from __future__ import annotations

import os
import sys
from pathlib import Path
from flask import Flask, jsonify, render_template, request

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

# Singletons
_embedder = None
_store = None
_agent = None

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
        print(f"Building EmbeddingStore from {DATA_DIR} using RecursiveChunker(chunk_size=500)...")
        _store = build_knowledge_base(
            DATA_DIR,
            embedding_fn=embedder,
            chunker=RecursiveChunker(chunk_size=500),
            collection_name="shopee_policy_kb",
        )
        print(f"EmbeddingStore initialized with {_store.get_collection_size()} chunks!")
    return _store

def get_agent():
    global _agent
    if _agent is None:
        store = get_store()
        _agent = KnowledgeBaseAgent(store=store)
    return _agent

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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    print(f"Starting Shopee Help Center Web Server on port {port} ...")
    app.run(host="0.0.0.0", port=port, debug=False)
