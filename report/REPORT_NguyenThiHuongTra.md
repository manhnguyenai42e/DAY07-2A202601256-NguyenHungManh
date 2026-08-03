# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Thị Hương Trà
**Nhóm:** Gicungduoc
**Ngày:** 2026-08-03

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> *Viết 1-2 câu:* Độ tương tự cosine cao là 2 chunk embeddings vector tạo góc rất bé hoặc trùng nhau, nghĩa là hai đoạn văn bản có sự tương đồng lớn về mặt ngữ nghĩa, mặc dù từ ngữ sử dụng có thể khác nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: Hôm nay thời tiết nắng nóng.
- Câu B: Nhiệt độ ngoài trời hôm nay cao.
- Tại sao tương đồng: Cả hai câu đều miêu tả thời tiết oi nóng, truyền tải cùng ý nghĩa ngữ nghĩa dù cách dùng từ khác nhau.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Tôi rất thích ăn kem vào mùa hè.
- Câu B: Thuật toán sắp xếp nhanh có độ phức tạp trung bình là O(n log n).
- Tại sao khác: Hai câu thuộc hai chủ đề hoàn toàn khác nhau, không có sự liên quan về ngữ nghĩa.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> *Viết 1-2 câu:* Cosine similarity đo góc giữa hai vector nên tập trung vào hướng (ý nghĩa ngữ nghĩa) và không bị ảnh hưởng bởi độ dài văn bản. Trong khi đó, khoảng cách Euclid bị ảnh hưởng bởi độ dài (magnitude) của vector, dễ dẫn đến đánh giá sai lệch khi so sánh các văn bản có độ dài chênh lệch.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* step size = chunk_size - overlap = 500 - 50 = 450
Số chunks = 1 + (10,000 - 500) / 450 = 1 + 22 = 23.
> *Đáp án:* 23 chunks

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> *Viết 1-2 câu:* Khi overlap tăng lên 100, bước dịch chuyển giảm xuống còn 400 khiến số lượng chunk tăng lên thành 25. Muốn tăng overlap để giữ lại nhiều ngữ cảnh nối giữa các ranh giới chunk, tránh làm gián đoạn thông tin quan trọng nằm ở đoạn chuyển tiếp.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> *Viết 2-3 câu: dùng biểu thức chính quy (regex) gì để phát hiện câu? Xử lý trường hợp ngoại lệ (edge case) nào?*
Tác vụ sử dụng regular extension `r'(?<=[.!?])\s+'` để phân tách văn bản thành từng câu riêng biệt dựa trên các dấu kết thúc câu (`.`, `!`, `?`) theo sau bởi khoảng trắng. Các câu sau đó được nhóm lại thành chunk có số lượng câu tối đa không vượt quá `max_sentences_per_chunk`. Thuật toán xử lý edge case cho văn bản rỗng/khoảng trắng thừa bằng cách lọc `.strip()`, đồng thời đảm bảo `max_sentences_per_chunk >= 1`.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> *Viết 2-3 câu: thuật toán hoạt động thế nào? Base case (trường hợp cơ sở) là gì?*
Thuật toán thực hiện chia nhỏ đệ quy theo thứ tự ưu tiên của danh sách các dấu phân cách (`\n\n`, `\n`, `. `, ` `, `""`) và liên kết các đoạn nhỏ lại sao cho độ dài không vượt quá `chunk_size`. Nếu một đoạn nhỏ vượt quá `chunk_size`, nó sẽ đệ quy tiếp với danh sách các dấu phân cách phía sau. Trường hợp cơ sở (base case) xảy ra khi độ dài văn bản `<= chunk_size` (trả về văn bản hiện tại) hoặc khi danh sách dấu phân cách cạn kiệt/gặp chuỗi rỗng (sử dụng `FixedSizeChunker` để cắt cố định).

**`HierarchicalChunker.chunk` / `_split`** — hướng tiếp cận:
> *Viết 2-3 câu: thuật toán hoạt động thế nào?*
Thuật toán chia nhỏ văn bản theo cấp thứ bậc: bắt đầu phân tách theo đoạn văn (`\n\n`), nếu đoạn vượt quá `chunk_size` sẽ tách theo dòng (`\n`), tiếp theo là theo câu (dùng regex), và cuối cùng dùng `FixedSizeChunker` nếu câu vẫn vượt quá giới hạn. Quá trình tích lũy các dòng/câu được thực hiện cuốn chiếu sao cho mỗi chunk không vượt quá `chunk_size`, giúp giữ trọn vẹn cấu trúc tự nhiên của tài liệu.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> *Viết 2-3 câu: lưu trữ thế nào? Tính độ tương tự ra sao?*
Mỗi document được ánh xạ thành record chứa `id`, `content`, `metadata` và embedding do `embedding_fn` tạo. `add_documents` xây dựng record với `_make_record` rồi lưu vào `_store`, trong khi `search` biến query thành embedding và tính độ tương tự với từng record qua dot product để xếp hạng.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> *Viết 2-3 câu: lọc (filter) trước hay sau? Xóa bằng cách nào?*
`search_with_filter` áp dụng filter metadata trước khi thực hiện tìm kiếm tương tự, giúp chỉ so sánh với các record phù hợp. `delete_document` xóa mọi chunk có `doc_id` trùng khớp bằng cách xây lại `_store` chỉ giữ lại record khác, trả về True nếu có xóa thành công.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> *Viết 2-3 câu: cấu trúc prompt? Cách đưa ngữ cảnh (inject context) vào thế nào?*
Thuật toán xây dựng prompt bằng cách nối các chunk top-k được truy xuất từ kho vector vào phần ngữ cảnh, mỗi chunk kèm theo nguồn và nội dung. Cấu trúc prompt gồm phần chỉ dẫn rõ ràng yêu cầu chỉ dùng ngữ cảnh có sẵn và không bịa thông tin, sau đó là câu hỏi. Ngữ cảnh được inject trực tiếp vào prompt dưới dạng các đoạn văn cách nhau bởi hai dòng trống để LLM tham chiếu khi tạo câu trả lời.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
======================= test session starts ========================
platform darwin -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0 -- /Users/empteax214/Documents/vinai/Day07-2A202601416-NguyenThiHuongTra/.venv/bin/python
cachedir: .pytest_cache
rootdir: /Users/empteax214/Documents/vinai/Day07-2A202601416-NguyenThiHuongTra
collected 42 items                                                 

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

======================== 42 passed in 0.08s ========================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán trước khi chạy | Điểm thực tế | Đúng? |
| --- | --------------------------------------------------------------------- | --------------------------------------------------------------- | ---------------------- | -----------: | ----- |
| 1   | Thời hạn gửi yêu cầu trả hàng là 15 ngày. | Người Mua có thể gửi yêu cầu trả hàng trong vòng 15 ngày. | cao | 0.838 | Có |
| 2 | Người bán bị xử lý thế nào khi vi phạm quy định đăng bán sản phẩm bị cấm?| Người bán sẽ tạm thời bị ẩn/khoá tài khoản | Cao                   |     0.791 | Có |
| 3   | Người bán phải phản hồi yêu cầu trả hàng trong 2 ngày.                | Người bán cần gửi phản hồi trong vòng 02 ngày lịch.             | cao                    |     0.810  | Có    |
| 4   | Tài khoản phải liên kết phương thức thanh toán để nhận hoàn tiền COD. | Người dùng có thể rút lại sự đồng ý xử lý dữ liệu cá nhân.      | thấp                   |     0.664  | Không |
| 5   | Chính sách bảo vệ dữ liệu cá nhân cho phép yêu cầu xóa dữ liệu.       | Chính sách bảo vệ dữ liệu cá nhân cho phép yêu cầu sửa dữ liệu. | cao                    |     0.765 | Có    |

Điều bất ngờ nhất là cặp 4 có score khá cao dù hai câu nói về COD và dữ liệu cá nhân, hai chủ đề không hoàn toàn giống nhau. Điều này cho thấy embedding vẫn có thể bị ảnh hưởng bởi các từ và ngữ cảnh chung như “tài khoản”, “phương thức” hoặc “yêu cầu”. Vì vậy similarity là tín hiệu hữu ích cho retrieval nhưng vẫn cần kiểm tra nội dung chunk và đối chiếu câu trả lời chuẩn.

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Theo dữ liệu `CHUNK_COMPARE.md`, chiến lược tốt nhất là **SentenceChunker**. Nó đưa evidence top-1 cho Q1-Q4, trong khi Q5 chỉ có evidence ở rank 3. Vì vậy đây là chiến lược tốt nhất để chấm điểm retrieval.

| #   | Câu hỏi                                                                                 | Top-1 chunk và score                                                                     | Evidence?                                                | Kết luận top-1/top-3                                                                                                  |
| --- | --------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- | -------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| 1   | Thời hạn gửi yêu cầu trả hàng và hoàn tiền trên Shopee là bao lâu?                      | `k4-returns-policy::chunk_7::119`, 0.769; evidence=True                                  | Top-1 evidence                                           | Top-1 đúng câu trả lời 15 ngày; Q1 pass full evidence.                                                               |
| 2   | Người bán bị xử lý thế nào khi vi phạm quy định đăng bán sản phẩm bị cấm?               | `k4-seller-listing::chunk_75::234`, 0.810; evidence=True                                | Top-1 evidence                                           | Top-1 chứa biện pháp xử lý; Q2 pass full evidence.                                                                   |
| 3   | Quy định về thời gian phản hồi của Người Bán khi nhận yêu cầu trả hàng là bao lâu?      | `k4-returns-policy::chunk_27::139`, 0.810; evidence=True                                | Top-1 evidence                                           | Top-1 nêu rõ 02 ngày lịch; Q3 pass full evidence.                                                                   |
| 4   | Điều kiện để Người Mua nhận hoàn tiền khi thanh toán bằng COD là gì?                    | `k4-returns-policy::chunk_8::120`, 0.639; evidence=True                                 | Top-1 evidence                                           | Top-1 nêu điều kiện liên kết phương thức nhận hoàn tiền hợp lệ; Q4 pass full evidence.                              |
| 5   | Người dùng có quyền yêu cầu xóa hoặc rút lại sự đồng ý sử dụng dữ liệu cá nhân không?     | `k4-privacy-policy::chunk_30::77`, 0.763; evidence=False (evidence rank 3)              | Top-3 evidence                                            | Evidence chỉ xuất hiện ở rank 3; Q5 không đạt top-1 mặc dù có trong top-3.                                           |

**Đánh giá:** sentence chunking đạt evidence top-1 cho 4/5 câu, và Q5 có evidence trong top-3. Tổng điểm retrieval theo rubric là **9/10**.

Chiến lược này hiệu quả nhất vì nó giữ được ranh giới câu tự nhiên, giúp tìm đúng đoạn chứa `evidence` mà không làm loãng ngữ cảnh. Metadata filter cho Q2 không đổi kết quả top-1, nhưng vẫn là lựa chọn hữu ích để xác nhận tài liệu đúng trong trường hợp cần giới hạn tìm kiếm.

**Điều tôi học được:** đánh giá retrieval phải dựa vào evidence chunk-level trong top-3, đồng thời ưu tiên evidence top-1 khi đánh giá chất lượng. Sentence chunking tốt hơn fixed-size hoặc hierarchical ở bài toán này vì nó giữ được sentence nguyên vẹn và vẫn đủ gọn để trả về đoạn evidence chính xác.

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí                                        | Điểm tự đánh giá |
| ----------------------------------------------- | ---------------: |
| Khởi động (Warm-up)                             |            5 / 5 |
| Hướng tiếp cận của tôi (My Approach)            |          10 / 10 |
| Hoàn thiện code (Core Implementation — tests)   |          30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions)    |            5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) |           9 / 10 |
| **Tổng phần cá nhân**                           |      **59 / 60** |