# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Hùng Mạnh  
**Nhóm:** Nhóm K4 - E-Commerce Policy Experts  
**Ngày:** 03/08/2026  

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao (gần 1.0) nghĩa là hai vector embedding chỉ cùng hướng trong không gian đa chiều, phản ánh rằng hai đoạn văn bản có ý nghĩa ngữ nghĩa tương đồng nhau, bất kể độ dài ngắn của văn bản.

**Ví dụ có độ tương tự CAO:**
- Câu A: Shopee hỗ trợ đổi trả hàng trong thời hạn 15 ngày.
- Câu B: Khách hàng được quyền hoàn trả sản phẩm trong vòng 15 ngày kể từ khi nhận hàng.
- Tại sao tương đồng: Cả hai câu đều thể hiện cùng một ý nghĩa quy định thời hạn đổi trả 15 ngày của nền tảng thương mại điện tử.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Khách hàng được đổi trả hàng bị lỗi trong 15 ngày.
- Câu B: Thuật toán học máy huấn luyện trên tập dữ liệu lớn.
- Tại sao khác: Câu A thuộc chủ đề chính sách mua sắm, câu B thuộc chủ đề kỹ thuật máy tính; hai chủ đề không liên quan ngữ nghĩa.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Khoảng cách Euclid bị ảnh hưởng mạnh bởi độ dài vector (độ dài câu), khiến hai câu có cùng ý nghĩa nhưng một câu dài và một câu ngắn có khoảng cách xa nhau. Độ tương tự Cosine chỉ đo góc giữa 2 vector, triệt tiêu ảnh hưởng của độ dài văn bản.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Phép tính:  
> Step size = `chunk_size` - `overlap` = 500 - 50 = 450 ký tự.  
> Số lượng chunks = $\lceil (10,000 - 500) / 450 \rceil + 1 = \lceil 9,500 / 450 \rceil + 1 = 22 + 1 = 23$ chunks.  
> Đáp án: **22 hoặc 23 chunks** (tùy thuộc vào xử lý phần dư ở cuối).

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Nếu overlap tăng lên 100, step size giảm xuống 400, làm số lượng chunk tăng lên $\lceil 9,500 / 400 \rceil + 1 = 25$ chunks. Ta muốn tăng độ chồng chéo để tránh ngắt đôi ngữ cảnh hoặc từ ngữ quan trọng nằm ở vị trí giáp ranh giữa hai chunk consecutive.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Sử dụng biểu thức chính quy `re.split(r'(?<=\. |\! |\? |\.\n)', text)` để phát hiện ranh giới kết thúc câu mà vẫn giữ lại dấu câu. Sau đó gom nhóm tối đa `max_sentences_per_chunk` câu vào mỗi chunk và thực hiện strip loại bỏ khoảng trắng thừa.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán duyệt qua danh sách dấu phân cách ưu tiên `["\n\n", "\n", ". ", " ", ""]`. Trường hợp cơ sở (base case) là khi văn bản nhỏ hơn `chunk_size` hoặc đã hết danh sách phân cách thì trả về khối văn bản đó. Khi ngắt, thuật toán tích lũy các đoạn nhỏ vào danh sách cho đến khi vượt quá `chunk_size` thì đệ quy tách tiếp đoạn đó.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Với `add_documents`, chuẩn hóa `Document` thành record dict chứa id, content, metadata và vector embedding (từ `_embedding_fn`). Với `search`, tính vector embedding cho query, sau đó tính tích vô hướng (`_dot`) với tất cả các vector đã lưu, sắp xếp giảm dần theo điểm tương đồng và trả về top-k.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Với `search_with_filter`, thực hiện tiền lọc (pre-filter) danh sách record thỏa mãn tất cả các cặp `key: value` trong `metadata_filter` trước, sau đó mới tính độ tương đồng vector trên danh sách đã lọc. Với `delete_document`, lọc bỏ tất cả record có `id` hoặc `metadata['doc_id']` trùng với `doc_id` cần xóa.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Gọi `store.search(question, top_k=top_k)` để lấy các chunk liên quan nhất. Sau đó định dạng ngữ cảnh thành chuỗi dạng `[1] content1\n\n[2] content2` và chèn vào RAG prompt trước khi truyền sang hàm `llm_fn` để tổng hợp câu trả lời.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```text
============================= test session starts =============================
platform win32 -- Python 3.12.2, pytest-9.1.1, pluggy-1.6.0
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED

============================= 42 passed in 0.09s ==============================
```

**Số lượng bài test vượt qua (pass):** **42** / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Shopee miễn phí vận chuyển đơn từ 45k | Khách hàng được freeship khi mua trên 45.000 đồng | Cao | 0.88 | Đúng |
| 2 | Người bán cần đóng gói hàng cẩn thận | Thời gian giao hàng dự kiến từ 2-3 ngày | Thấp | 0.12 | Đúng |
| 3 | Người mua gửi yêu cầu trả hàng | Khách hàng bấm nút hoàn tiền trên ứng dụng | Cao | 0.81 | Đúng |
| 4 | Tài khoản người bán bị tạm khóa | Người bán vi phạm quy định đăng bán sản phẩm | Cao | 0.76 | Đúng |
| 5 | Phương thức thanh toán khi nhận hàng COD | Chính sách bảo mật thông tin người dùng | Thấp | 0.09 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cặp 3 ("gửi yêu cầu trả hàng" và "bấm nút hoàn tiền") cho điểm tương đồng rất cao (0.81) mặc dù không trùng từ khóa chính. Điều này cho thấy mô hình nhúng (Embedding Model) không hoạt động như tìm kiếm từ khóa truyền thống (Keyword Search) mà mã hóa ngữ nghĩa tiềm ẩn (Latent Semantic Space), nhận diện hai hành động trên đều biểu thị ý định hoàn trả giao dịch.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

**Chiến lược cá nhân tôi chọn thử nghiệm (Nguyễn Hùng Mạnh):** Overlap Chunking (`FixedSizeChunker`, `chunk_size=300`, `overlap=50`)

**Kết quả thực nghiệm 5 câu hỏi Benchmark** (số liệu thật, dùng `EMBEDDING_PROVIDER=local`, tái lập được từ `build_knowledge_base(..., chunker=FixedSizeChunker(chunk_size=300, overlap=50))`):

| # | Câu hỏi | Filter được dùng | Chunk trả về Top-1 | Score | Trạng thái |
|---|---------|-------------------|-------------------|-------|------------|
| 1 | Thời hạn gửi yêu cầu trả hàng và hoàn tiền trên Shopee là bao lâu? | Không | `k4-returns-policy::chunk_57` (nội dung: hạn 03–05 ngày hoàn phí ship, **không phải** mốc "15 ngày" cần tìm) | 0.800 | **Miss (0/2)** — chunk đúng chứa "15 (mười lăm) ngày" (`chunk_12`, score 0.656) xếp hạng ngoài top-10, không lọt top-3 |
| 2 | Người bán bị xử lý thế nào khi vi phạm quy định đăng bán sản phẩm bị cấm? | `customer_role: seller` | `k4-seller-listing::chunk_81` (đúng nội dung xử lý vi phạm) | 0.801 | **Top-1 Hit (2/2)** |
| 3 | Quy định về thời gian phản hồi của Người Bán khi nhận yêu cầu trả hàng là bao lâu? | Không | `k4-returns-policy::chunk_40` (đúng nội dung "phản hồi trong vòng 02 ngày lịch") | 0.749 | **Top-1 Hit (2/2)** |
| 4 | Điều kiện để Người Mua nhận hoàn tiền khi thanh toán đơn hàng bằng COD là gì? | Không | Top-1 `k4-returns-policy::chunk_14` (0.665); target `k4-payment-policy` xuất hiện ở Top-3 (0.625) | 0.625 (target, rank 3) | Top-3 Hit (1/2) — target không ở Top-1 |
| 5 | Người dùng có quyền yêu cầu xóa hoặc rút lại sự đồng ý sử dụng dữ liệu cá nhân không? | Không | Top-1 `k4-privacy-policy::chunk_95` (liên quan nhưng là Mục 7.3, không phải đúng Mục 13.1); Top-2 `k4-privacy-policy::chunk_152` mới đúng Mục 13.1 "Rút Lại Sự Đồng Ý" | 0.741 / 0.740 | Top-3 Hit (1/2) — chunk đúng ở vị trí Top-2, không phải Top-1 |

**Tổng điểm cá nhân đạt được:** **6 / 10** điểm benchmark retrieval (0 + 2 + 2 + 1 + 1).

**Nhận xét cá nhân:**
Chiến lược `Overlap Chunking (300/50)` giữ lại được ngữ cảnh giáp ranh khá tốt cho Câu 2 và 3 — đều Top-1 đúng chunk. Câu 1 là một **case thất bại thật sự**: điểm tương đồng cao nhất (0.80) rơi vào một đoạn khác trong cùng tài liệu (hạn hoàn phí vận chuyển 03–05 ngày) chứ không phải đoạn nêu mốc "15 ngày" — cho thấy điểm similarity cao không đồng nghĩa với đúng nội dung cần trả lời. Câu 4 và Câu 5 đều rơi vào tình huống tương tự: tài liệu/chunk đúng vẫn xuất hiện trong top-3 nhưng bị các chunk liên quan-nhưng-không-phải-đáp-án của cùng chủ đề (hoặc cùng tài liệu) xếp điểm cao hơn, đẩy xuống Top-2/Top-3 thay vì Top-1. Việc chia `chunk_size=300` khá nhỏ khiến các mốc thời gian/điều khoản khác nhau (03-05 ngày, 02 ngày, 15 ngày; các Điều 3.x, 7.x, 13.x) rơi vào các chunk tách biệt, cạnh tranh điểm số với nhau thay vì mốc đúng nổi bật hẳn lên.
