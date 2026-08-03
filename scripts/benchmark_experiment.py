import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from main import _select_embedder
from ingest import load_documents, chunk_document, build_knowledge_base
from src.chunking import FixedSizeChunker, SentenceChunker, RecursiveChunker, ChunkingStrategyComparator
from src.store import EmbeddingStore
from src.agent import KnowledgeBaseAgent
from src.embeddings import _mock_embed, LocalEmbedder

DATA_DIR = "data/k4_ecommerce"

BENCHMARK_QUERIES = [
    {
        "id": 1,
        "query": "Thời hạn gửi yêu cầu trả hàng và hoàn tiền trên Shopee là bao lâu?",
        "gold_answer": "Người Mua có thể gửi yêu cầu trả hàng/hoàn tiền trong vòng 15 (mười lăm) ngày kể từ lúc đơn hàng được cập nhật giao hàng thành công (riêng thực phẩm tươi sống/đông lạnh là 24 giờ).",
        "target_doc_id": "k4-returns-policy",
        "filter": None,
    },
    {
        "id": 2,
        "query": "Người bán bị xử lý thế nào khi vi phạm quy định đăng bán sản phẩm bị cấm?",
        "gold_answer": "Người Bán bị xóa sản phẩm vi phạm, khoá/tạm khóa tài khoản Người Bán, tước danh hiệu Shop Yêu Thích và có thể bị báo cáo lên cơ quan nhà nước có thẩm quyền.",
        "target_doc_id": "k4-seller-listing",
        "filter": {"customer_role": "seller"},
    },
    {
        "id": 3,
        "query": "Quy định về thời gian phản hồi của Người Bán khi nhận yêu cầu trả hàng là bao lâu?",
        "gold_answer": "Người Bán cần gửi phản hồi trong vòng 02 ngày lịch kể từ ngày nhận được thông báo của Shopee nếu không đồng ý với quyết định hoàn tiền.",
        "target_doc_id": "k4-returns-policy",
        "filter": None,
    },
    {
        "id": 4,
        "query": "Điều kiện để Người Mua nhận hoàn tiền khi thanh toán đơn hàng bằng COD là gì?",
        "gold_answer": "Tài khoản Shopee của Người Mua phải liên kết thành công với phương thức nhận hoàn tiền hợp lệ (ví dụ Tài Khoản Ngân Hàng hoặc Ví ShopeePay) trước khi thực hiện yêu cầu.",
        "target_doc_id": "k4-payment-policy",
        "filter": None,
    },
    {
        "id": 5,
        "query": "Người dùng có quyền yêu cầu xóa hoặc rút lại sự đồng ý sử dụng dữ liệu cá nhân không?",
        "gold_answer": "Người dùng có quyền gửi yêu cầu rút lại sự đồng ý hoặc yêu cầu xóa dữ liệu cá nhân bằng cách liên hệ Nhân viên bảo vệ dữ liệu cá nhân của Shopee.",
        "target_doc_id": "k4-privacy-policy",
        "filter": None,
    },
]

def run_experiment():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print("=========================================================")
    print("   RUNNING K4 E-COMMERCE RETRIEVAL BENCHMARK EXPERIMENT  ")
    print("=========================================================\n")
    
    docs = load_documents(DATA_DIR)
    print(f"Loaded {len(docs)} documents from {DATA_DIR}.\n")

    embedder = _select_embedder()
    backend = getattr(embedder, "_backend_name", embedder.__class__.__name__)
    print(f"Embedding backend: {backend}")
    if backend == "mock embeddings fallback":
        print(
            "CANH BAO: dang dung MOCK embedder. Diem so ben duoi CHI kiem tra duoc luong chay "
            "ky thuat, KHONG phan anh chat luong ngu nghia va KHONG duoc dung de ket luan "
            "chien luoc chunking nao tot hon. Dat EMBEDDING_PROVIDER=local truoc khi chay "
            "de co so sanh co y nghia.\n"
        )

    # 1. Baseline Comparison
    comparator = ChunkingStrategyComparator()
    print("--- 1. BASELINE CHUNKING STRATEGY COMPARISON ---")
    for doc in docs[:3]:
        comp = comparator.compare(doc.content, chunk_size=500)
        print(f"\nDocument: {doc.id} ({doc.metadata.get('title')}) - len: {len(doc.content)}")
        for strat, stats in comp.items():
            print(f"  - {strat:15s}: count={stats['count']:2d}, avg_len={stats['avg_length']:.1f}")

    # 2. Evaluate 3 Chunkers
    chunkers = {
        "FixedSize (300/50)": FixedSizeChunker(chunk_size=300, overlap=50),
        "Sentence (max=3)": SentenceChunker(max_sentences_per_chunk=3),
        "Recursive (500)": RecursiveChunker(chunk_size=500),
    }

    print("\n\n--- 2. RETRIEVAL BENCHMARK EVALUATION ACROSS STRATEGIES ---")
    
    results_summary = {}

    for name, chunker in chunkers.items():
        print(f"\n==========================================")
        print(f"   Strategy: {name}")
        print(f"==========================================")
        store = build_knowledge_base(DATA_DIR, embedding_fn=embedder, chunker=chunker, collection_name=name)
        print(f"Total chunks in store: {store.get_collection_size()}")

        strategy_scores = []
        for q in BENCHMARK_QUERIES:
            if q["filter"]:
                search_res = store.search_with_filter(q["query"], top_k=3, metadata_filter=q["filter"])
            else:
                search_res = store.search(q["query"], top_k=3)
            
            top_ids = [r["metadata"].get("doc_id") for r in search_res]
            hit = q["target_doc_id"] in top_ids
            top1_hit = len(top_ids) > 0 and top_ids[0] == q["target_doc_id"]

            score = 2 if top1_hit else (1 if hit else 0)
            strategy_scores.append(score)

            print(f"\nQuery {q['id']}: {q['query']}")
            if q["filter"]:
                print(f"  Filter: {q['filter']}")
            print(f"  Target doc: {q['target_doc_id']} | Top-1 doc: {top_ids[0] if top_ids else 'None'} | Hit top-3: {hit} | Score: {score}/2")
            for idx, res in enumerate(search_res, start=1):
                print(f"    [{idx}] score={res['score']:.3f} doc_id={res['metadata'].get('doc_id')} content={res['content'][:80].replace(chr(10), ' ')}...")
        
        avg_score = sum(strategy_scores)
        results_summary[name] = {
            "scores": strategy_scores,
            "total_score": avg_score,
            "chunk_count": store.get_collection_size(),
        }

    print("\n\n==========================================")
    print("          BENCHMARK SUMMARY RESULTS       ")
    print("==========================================")
    for strat, res in results_summary.items():
        print(f"{strat:20s}: Total Score = {res['total_score']}/10  (Chunk Count = {res['chunk_count']})")

if __name__ == "__main__":
    run_experiment()
