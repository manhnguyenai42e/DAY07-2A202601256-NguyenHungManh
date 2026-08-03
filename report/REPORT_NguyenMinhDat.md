# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Minh Đạt
**Nhóm:** Gicungduoc
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai đoạn văn bản có vector embedding "chỉ cùng hướng" trong không gian nhiều chiều — tức chúng mang ý nghĩa/ngữ cảnh gần nhau, dù cách diễn đạt (từ ngữ, độ dài câu) có thể khác nhau. Cosine similarity đo góc giữa hai vector chứ không đo độ dài, nên hai câu diễn đạt cùng một ý bằng từ ngữ khác nhau vẫn có thể cho điểm gần 1.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Người mua có thể yêu cầu hoàn tiền trong vòng 15 ngày kể từ khi nhận hàng."
- Câu B: "Khách hàng được phép đề nghị trả lại tiền trong 15 ngày sau khi đơn hàng giao thành công."
- Tại sao tương đồng: cùng nói về một chính sách (thời hạn hoàn tiền 15 ngày cho người mua), chỉ khác từ vựng/cách diễn đạt — embedding sẽ đặt hai câu này gần nhau về hướng.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Người mua có thể yêu cầu hoàn tiền trong vòng 15 ngày kể từ khi nhận hàng."
- Câu B: "Người bán không được đăng bán các sản phẩm nằm trong danh mục hàng cấm của Shopee."
- Tại sao khác: hai câu nói về hai chủ đề chính sách khác hẳn nhau (hoàn tiền cho buyer vs. quy định đăng bán cho seller), không chia sẻ ngữ cảnh hay từ khóa quan trọng nào.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity chuẩn hoá theo độ dài vector nên không bị ảnh hưởng bởi độ dài văn bản (một đoạn dài tự nhiên có vector "lớn" hơn một câu ngắn dù nói cùng một ý) — nó chỉ quan tâm hướng/ý nghĩa. Euclidean distance thì nhạy với độ lớn (magnitude) của vector, nên hai văn bản cùng ý nhưng độ dài khác nhau có thể bị coi là "xa nhau" một cách sai lệch.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Trình bày phép tính: số_chunk = ceil((10000 − 50) / (500 − 50)) = ceil(9950 / 450) = ceil(22.11) = **23**
> Đáp án: **23 chunks**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> số_chunk = ceil((10000 − 100) / (500 − 100)) = ceil(9900 / 400) = ceil(24.75) = **25 chunks** (tăng từ 23 lên 25, vì bước trượt (chunk_size − overlap) nhỏ lại nên cần nhiều cửa sổ hơn để phủ hết văn bản). Tăng overlap giúp giữ ngữ cảnh liên tục qua ranh giới chunk — với văn bản chính sách nhiều điều khoản, một câu/điều kiện quan trọng nằm vắt qua ranh giới hai chunk vẫn có khả năng xuất hiện trọn vẹn trong ít nhất một chunk, tránh mất thông tin khi truy xuất chỉ lấy đúng 1 chunk.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng regex lookbehind `(?<=[.!?])\s+` để tách tại khoảng trắng **ngay sau** dấu `.`, `!`, `?` — nhờ lookbehind nên dấu câu vẫn được giữ lại ở cuối câu đứng trước (không bị mất khi split), rồi `strip()` từng câu và loại câu rỗng. Gom các câu theo nhóm `max_sentences_per_chunk` bằng cách duyệt list với bước nhảy `range(0, len(sentences), max_sentences_per_chunk)`, nối lại bằng khoảng trắng. Edge case: văn bản rỗng trả về `[]` ngay từ đầu.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán đệ quy kinh điển kiểu "RecursiveCharacterTextSplitter": thử tách bằng separator đầu tiên trong danh sách; nếu tách được (>1 phần), gộp các phần lại thành từng chunk ≤ `chunk_size` theo kiểu tham lam (greedy); phần nào sau khi gộp vẫn dài hơn `chunk_size` thì đệ quy tiếp với separator kế tiếp còn lại. Base case: `len(current_text) <= chunk_size` → trả về `[current_text]`; hoặc hết separator (`remaining_separators` rỗng, hoặc separator là chuỗi rỗng `""`) → cắt cứng theo `chunk_size`. Nhờ vậy separator luôn giảm dần ở mỗi lần đệ quy nên không bị lặp vô hạn.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Với nhánh in-memory (khi không có ChromaDB): mỗi `Document` được chuẩn hoá qua `_make_record` thành `dict` gồm `id`, `content`, `embedding` (gọi `self._embedding_fn(doc.content)`), và `metadata` đã gộp thêm `doc_id`; append vào `self._store`. `search` nhúng câu query rồi tính tích vô hướng (dot product, hàm `_dot` có sẵn) giữa vector query và từng embedding đã lưu, sort giảm dần theo `score`, cắt lấy `top_k`.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Lọc **trước**: duyệt `self._store`, chỉ giữ record có `record["metadata"].get(k) == v` cho mọi cặp trong `metadata_filter`, rồi mới gọi `_search_records` (tái dùng logic tính similarity + sort + top_k) trên tập đã lọc — tránh phải tính embedding/score cho record chắc chắn bị loại. `delete_document` lọc `self._store` giữ lại các record có `metadata["doc_id"] != doc_id`, so sánh độ dài trước/sau để biết có xoá được gì không (trả `True`/`False`).

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Gọi `store.search(question, top_k=top_k)` lấy các chunk liên quan, nối nội dung (`content`) của chúng bằng `"\n\n"` làm phần `Context`. Prompt có cấu trúc rõ 3 khối: hướng dẫn ngắn (chỉ dùng context để trả lời, nói "không biết" nếu context không đủ) → `Context:` → `Question:` → `Answer:`, rồi gọi `llm_fn(prompt)` và trả thẳng kết quả.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0
rootdir: H:\Lab_day7\K4-Day07-Data-Foundations
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED
tests/test_solution.py::TestFixedSizeChunker (7 tests) PASSED
tests/test_solution.py::TestSentenceChunker (4 tests) PASSED
tests/test_solution.py::TestRecursiveChunker (4 tests) PASSED
tests/test_solution.py::TestEmbeddingStore (8 tests) PASSED
tests/test_solution.py::TestKnowledgeBaseAgent (2 tests) PASSED
tests/test_solution.py::TestComputeSimilarity (4 tests) PASSED
tests/test_solution.py::TestCompareChunkingStrategies (3 tests) PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter (3 tests) PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument (3 tests) PASSED

============================= 42 passed in 0.09s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

> Dùng `_mock_embed` (mặc định của lab, không cấu hình `EMBEDDING_PROVIDER=local`) — README đã cảnh báo mock chỉ hợp cho unit test, gần như ngẫu nhiên theo chuỗi, **không phản ánh ngữ nghĩa thật**. Dự đoán dưới đây được đưa ra dựa trên ý nghĩa câu như thể dùng embedding thật, để đối chiếu xem mock có "bắt" được ý nghĩa không.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | "Người mua có thể yêu cầu hoàn tiền trong vòng 15 ngày kể từ khi nhận hàng." | "Khách hàng được phép đề nghị trả lại tiền trong 15 ngày sau khi đơn hàng giao thành công." | cao (cùng ý nghĩa, diễn đạt khác) | -0.0709 | Sai |
| 2 | "Người mua có thể yêu cầu hoàn tiền trong vòng 15 ngày kể từ khi nhận hàng." | "Người bán không được đăng bán các sản phẩm nằm trong danh mục hàng cấm của Shopee." | thấp (khác chủ đề hoàn toàn) | 0.0507 | Đúng (nhưng gần bằng cặp 1) |
| 3 | "Con mèo đang ngủ trên ghế sofa." | "Con mèo đang ngủ trên ghế sofa." | cao (giống hệt) | 1.0000 | Đúng |
| 4 | "Chính sách vận chuyển áp dụng cho cả người mua và người bán." | "Người dùng có quyền yêu cầu xóa dữ liệu cá nhân của mình." | thấp (khác chủ đề: vận chuyển vs. quyền riêng tư) | 0.0836 | Đúng |
| 5 | "Thời tiết hôm nay rất đẹp." | "Tôi thích ăn phở vào buổi sáng." | thấp (không liên quan gì nhau) | -0.0339 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Bất ngờ nhất là **cặp 1** — hai câu diễn đạt lại đúng một chính sách (hoàn tiền 15 ngày) nhưng bằng từ ngữ khác nhau, tôi dự đoán "cao" vì cùng ý nghĩa, nhưng điểm thực tế (-0.0709) lại thấp hơn cả cặp 5 gồm hai câu hoàn toàn không liên quan (thời tiết vs. ăn phở). Ngoại trừ trường hợp hai câu **giống hệt nhau tuyệt đối** (cặp 3, luôn = 1.0), mọi cặp còn lại — dù liên quan hay không liên quan về ý nghĩa — đều cho điểm dao động ngẫu nhiên quanh 0. Điều này khẳng định đúng cảnh báo trong README: `_mock_embed` chỉ sinh vector giả lập xác định theo hash của chuỗi ký tự, **không mã hoá ngữ nghĩa thật** — nó hữu ích để unit test chạy được nhanh, ổn định, nhưng hoàn toàn không dùng được để đánh giá "câu nào giống câu nào về ý nghĩa". Muốn kết luận về chất lượng ngữ nghĩa (vd. so sánh chiến lược chunking ở Giai đoạn 2) bắt buộc phải đặt `EMBEDDING_PROVIDER=local`.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

**Chiến lược chunking đã chọn:** Fixed-Length Chunking (`FixedSizeChunker`, chunking theo cửa sổ trượt kích thước cố định + overlap).

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

> Chạy thật bằng `python main.py "<câu hỏi>"` với `EMBEDDING_PROVIDER=local` (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`), chunker mặc định `FixedSizeChunker` (500/50) — 284 chunk được nạp từ `data/k4_ecommerce/`. `llm_fn` dùng là `demo_llm` có sẵn trong `main.py` — chỉ echo lại đoạn đầu của prompt (context đã ghép), **không phải LLM sinh câu trả lời tự nhiên thật**, nên cột "Câu trả lời của Agent" bên dưới là tóm tắt nội dung context mà agent đã lấy được (grounding), không phải câu trả lời tổng hợp.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Thời hạn gửi yêu cầu trả hàng và hoàn tiền trên Shopee là bao lâu? | `shipping-policy.md` — "...mà Người Bán không liên hệ với Shopee để xử lý đơn hàng, Shopee miễn trừ trách nhiệm..." | 0.767 | Có, nhưng **không ở top-1** — chunk đúng chủ đề (`returns-policy.md`) chỉ đứng top-2 (0.760) và top-3 (0.739) | Agent ghép context từ `shipping-policy.md` (sai chủ đề) làm câu trả lời chính — không phản ánh đúng chính sách 15 ngày ở `returns-policy.md` |
| 2 | Người bán bị xử lý thế nào khi vi phạm quy định đăng bán sản phẩm bị cấm? *(có filter `metadata_filter={"customer_role":"seller"}` theo K4_VARIANT.md)* | `k4-seller-listing::chunk_45` — "...tùy theo mức độ vi phạm, Shopee sẽ tiến hành một số biện pháp xử lý (i) xóa/khóa/tạm ẩn sản phẩm; (ii) giới hạn/khóa tài khoản; (iii) yêu cầu đền bù..." | 0.782 (top-1 giống nhau dù có/không filter) | Có (top-1, đúng chủ đề) | Agent trả về đúng danh sách biện pháp xử lý vi phạm từ mục E. XỬ LÝ VI PHẠM |
| 3 | Quy định về thời gian phản hồi của Người Bán khi nhận yêu cầu trả hàng là bao lâu? | `returns-policy.md` — "...Người Bán cần gửi phản hồi trong vòng 02 ngày lịch... kể từ ngày nhận được thông báo của Shopee..." | 0.720 | Có (top-1, đúng chủ đề) | Agent trả về đúng mốc "02 ngày lịch" từ mục 5. QUYỀN CỦA NGƯỜI BÁN |
| 4 | Điều kiện để Người Mua nhận hoàn tiền khi thanh toán đơn hàng bằng COD là gì? | `returns-policy.md` — "...tài khoản Shopee của Người Mua phải liên kết với các phương thức nhận hoàn tiền hợp lệ..." | 0.661 | Có (top-1, đúng chủ đề) | Agent trả về đúng điều kiện liên kết phương thức nhận hoàn tiền (Điều 3.3) |
| 5 | Người dùng có quyền yêu cầu xóa hoặc rút lại sự đồng ý sử dụng dữ liệu cá nhân không? | `privacy-policy.md` — "...xóa, tiêu hủy dữ liệu trong trường hợp yêu cầu của bạn phù hợp với quy định của Luật riêng tư hiện hành..." | 0.756 | Có (top-1, đúng chủ đề) | Agent trả về đúng nội dung quyền rút lại đồng ý/yêu cầu xóa dữ liệu (mục 13) |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5 (4 câu đạt top-1: câu 2, 3, 4, 5; riêng câu 1 chunk đúng chủ đề chỉ đạt top-2/top-3, không phải top-1)

> **So sánh có/không filter cho câu 2** (chạy trực tiếp `store.search()` vs `store.search_with_filter(metadata_filter={"customer_role": "seller"})`):
>
> | | Không filter | Có filter `customer_role: seller` |
> |---|---|---|
> | Top-1 | `k4-seller-listing::chunk_45` (0.782, role=seller) | `k4-seller-listing::chunk_45` (0.782, role=seller) |
> | Top-2 | `k4-shipping-policy::chunk_3` (0.764, **role=buyer** — lạc chủ đề) | `k4-seller-listing::chunk_2` (0.751, role=seller) |
> | Top-3 | `k4-seller-listing::chunk_2` (0.751, role=seller) | `k4-seller-listing::chunk_36` (0.734, role=seller) |
>
> **Nhận xét:** Top-1 giống nhau ở cả hai cách vì đã đúng ngay từ đầu, nhưng **không filter thì top-2 bị lẫn 1 chunk sai vai trò** (`shipping-policy`, `role=buyer`) chen vào giữa 2 chunk đúng chủ đề — filter theo `customer_role` đã loại bỏ noise này, giúp cả 3/3 kết quả đều đúng vai trò `seller`. Đây là bằng chứng cụ thể cho thấy `search_with_filter()` cải thiện độ "sạch" của context, dù không đổi kết quả top-1 trong trường hợp này.

---

### Chấm điểm ở mức chunk (evidence-based), không chỉ theo doc_id

**Phương pháp:** với mỗi câu, khai báo trước một `gold_string` — chuỗi đặc trưng phải xuất hiện nguyên văn trong chunk mới coi là "có bằng chứng trả lời được", rồi kiểm tra thật trên top-3 (không chỉ nhìn `doc_id` có "đúng tài liệu" hay không). Chấm theo đúng rubric `docs/SCORING.md`: **2đ** nếu gold_string ở top-1, **1đ** nếu ở top-2/top-3, **0đ** nếu không xuất hiện trong top-3.

| # | Câu hỏi | `gold_string` kỳ vọng | `doc_id` top-3 có "đúng chủ đề" không? | `gold_string` có thật trong top-3 không? | Điểm (evidence-based) |
|---|---------|------------------------|------------------------------------------|---------------------------------------------|------------------------|
| 1 | Thời hạn gửi yêu cầu trả hàng... | `"15 (mười lăm) ngày"` | Có (`returns-policy` ở top-2, top-3) | **Không** — không có trong bất kỳ chunk nào của top-3 | **0 / 2** |
| 2 | Người bán bị xử lý thế nào... (có filter) | `"xóa/khóa/tạm ẩn hiển thị sản phẩm"` | Có (`seller-listing` cả 3/3) | Có, ở top-1 | **2 / 2** |
| 3 | Thời gian phản hồi của Người Bán... | `"02 ngày lịch"` | Có (`returns-policy` ở top-1, top-3) | Có, ở top-1 | **2 / 2** |
| 4 | Điều kiện hoàn tiền COD... | `"trước khi thực hiện yêu cầu Trả hàng / Hoàn tiền"` | Có (`returns-policy` ở top-1, top-3) | Có, ở top-1 | **2 / 2** |
| 5 | Quyền xóa/rút lại đồng ý dữ liệu cá nhân... | `"dpo.vn@shopee.com"` | Có (`privacy-policy` cả 3/3) | **Không** — không có trong bất kỳ chunk nào của top-3 | **0 / 2** |

**Tổng theo evidence-based scoring: 6 / 10** — thấp hơn hẳn so với cách chấm hời hợt theo `doc_id` (5/5 câu "trông có vẻ đúng tài liệu", tưởng gần như 10/10). Đây đúng là "chênh lệch đáng giá nhất" mà bài đề cập: **`doc_id` đúng không có nghĩa là chunk chứa câu trả lời** — với `FixedSizeChunker`, một tài liệu dài bị cắt thành hàng chục chunk gần giống nhau về chủ đề, nên retrieval có thể chọn đúng văn bản nhưng sai đoạn.

### Failure case 1 — Câu 1: chunk đúng chủ đề nhưng không chứa số liệu lại thắng chunk có đáp án

- **Query:** "Thời hạn gửi yêu cầu trả hàng và hoàn tiền trên Shopee là bao lâu?"
- **Bằng chứng từ top-k:** top-3 là `shipping-policy` (0.767), `returns-policy` (0.760), `returns-policy` (0.739) — đều là chunk nói về "khiếu nại", "hoàn tiền", "thời hạn" nhưng **không chunk nào chứa con số "15 (mười lăm) ngày"**. Truy ngược toàn bộ 284 chunk trong store: chunk thật sự chứa `"15 (mười lăm) ngày"` (trích Điều 3.2 `returns-policy.md`) chỉ xếp hạng **#10** (score 0.646) — thấp hơn hẳn ngưỡng top-3.
- **Nguyên nhân:** `returns-policy.md` có nhiều đoạn cùng nói về "thời hạn"/"khiếu nại"/"hoàn tiền" (Điều 9.3, 9.4 về cách hoàn tiền; các điều khoản khiếu nại vận chuyển) — các đoạn này **giống chủ đề** với câu hỏi hơn cả đoạn chứa đáp án thật (Điều 3.2), vì embedding đo độ tương đồng ngữ nghĩa tổng thể chứ không đo "có chứa con số trả lời được câu hỏi hay không". `FixedSizeChunker` cắt cứng theo 500 ký tự nên Điều 3.2 (chứa "15 ngày") bị tách khỏi các đoạn ngữ cảnh liên quan khác, không có cơ hội "cộng dồn" độ liên quan.
- **Đề xuất sửa:** (a) thử `SentenceChunker`/chunker theo điều khoản để Điều 3.2 không bị cắt rời khỏi phần mở đầu "Người Mua có thể gửi yêu cầu..."; (b) tăng `top_k` khi query có khả năng cạnh tranh cao giữa nhiều đoạn cùng chủ đề; (c) thêm metadata `category: returns-deadline` chi tiết hơn `category: returns` để lọc thu hẹp trước khi rank.

### Failure case 2 — Câu 5: top-3 đúng tài liệu nhưng sai section

- **Query:** "Người dùng có quyền yêu cầu xóa hoặc rút lại sự đồng ý sử dụng dữ liệu cá nhân không?"
- **Bằng chứng từ top-k:** cả 3/3 kết quả top-3 đều là `privacy-policy` (0.756, 0.730, 0.728) — "đúng tài liệu" tuyệt đối, nhưng **không chunk nào chứa `"dpo.vn@shopee.com"`** (địa chỉ liên hệ thật để thực hiện quyền này, trích Điều 13.1.1). Chunk chứa thông tin đúng xếp hạng **#11** (score 0.654) trong toàn bộ store.
- **Nguyên nhân:** `privacy-policy.md` là tài liệu dài nhất trong corpus, bị `FixedSizeChunker` cắt thành **96 chunk** (gần 1/3 tổng số 284 chunk toàn corpus) — rất nhiều chunk trong số đó đều "nói về quyền riêng tư/dữ liệu cá nhân" nói chung (thu thập dữ liệu, cookie, chia sẻ bên thứ ba, trẻ em dưới 13 tuổi...) nên có độ tương đồng cosine gần bằng nhau với câu hỏi. Phần trả lời cụ thể (mục 13 — quyền rút lại đồng ý) chỉ là 1 trong ~96 "ứng viên" gần giống nhau, dễ bị các đoạn khác lấn át dù không trả lời trực tiếp câu hỏi.
- **Đề xuất sửa:** chunker theo heading/điều khoản sẽ giúp nhiều ở đây vì mỗi mục (`13. BẠN CÓ THỂ RÚT LẠI SỰ ĐỒNG Ý...`) vốn đã là một đơn vị ngữ nghĩa trọn vẹn trong văn bản gốc; nếu vẫn dùng `FixedSizeChunker`, nên giảm `chunk_size` (tăng số chunk mỗi điều khoản dễ đứng độc lập hơn) hoặc tăng `top_k` lên 5-10 cho các tài liệu dài bất thường như `privacy-policy`.

**Kết luận chung:** Fixed-Length Chunking là baseline đơn giản, ổn định để chạy được ngay, nhưng với văn bản pháp lý dài nhiều điều khoản tương tự nhau về chủ đề, nó dễ mắc đúng 2 lỗi checkpoint liệt kê: "chunk đúng chủ đề nhưng thiếu số liệu thắng chunk có đáp án" và "top-3 đúng tài liệu nhưng sai section". Score cosine cao là tín hiệu **xếp hạng độ liên quan chủ đề**, không phải bằng chứng nội dung đúng — bài học rõ nhất của lần benchmark này.

---

### Thử nghiệm phụ — Metadata-Enhanced Chunking (ngoài chiến lược chính thức)

Sau khi thấy 2 failure case ở trên đều là dạng "đúng tài liệu nhưng sai đoạn", tôi thử một biến thể tự thiết kế để xem có khắc phục được không: **giữ nguyên cách cắt Fixed-Length, nhưng thêm 1 dòng ngữ cảnh (title + category + customer_role của tài liệu gốc) vào đầu mỗi chunk trước khi nhúng**, ví dụ:

```
[Tài liệu: Chính sách trả hàng và hoàn tiền Shopee | Chủ đề: returns | Đối tượng: buyer]
<nội dung chunk gốc...>
```

**Kết quả (evidence-based, cùng 5 câu, cùng embedder local, chỉ khác cách nhúng):**

| Câu | Fixed-Length (baseline) | Metadata-Enhanced |
|---|---|---|
| 1 — 15 ngày | 0/2 | 0/2 (không đổi) |
| 2 — seller, có filter | 2/2 | 2/2 (không đổi) |
| 3 — 02 ngày lịch | **2/2** | **0/2** ⬇️ |
| 4 — COD | **2/2** | **1/2** ⬇️ (tụt xuống hạng 3) |
| 5 — rút lại đồng ý | 0/2 | 0/2 (không đổi) |
| **Tổng** | **6/10** | **3/10** ❌ |

**Kết luận — thử nghiệm này thất bại, và lý do đã dự đoán được trước khi chạy:** metadata dùng ở đây là metadata **cấp tài liệu** (title/category/customer_role), nên **mọi chunk trong cùng 1 file bị gắn đúng một dòng ngữ cảnh giống hệt nhau** — với `returns-policy.md` (44 chunk), cả 44 chunk đều có chung dòng `"[Tài liệu: Chính sách trả hàng... | Chủ đề: returns...]"`. Dòng lặp lại này không giúp phân biệt chunk nào trong 44 chunk đó, mà còn "pha loãng" phần nội dung thật sự khác biệt giữa các chunk (mô hình embedding có ngân sách biểu diễn hữu hạn, một phần bị tiêu tốn cho đoạn prefix giống nhau) — khiến 2 câu vốn đã đúng ở baseline (câu 3, câu 4) bị tụt hạng.

**Bài học:** Metadata chỉ có giá trị khi nó **khác nhau giữa các chunk** để lọc bớt ứng viên sai (như filter `customer_role: seller` giúp câu 2 — không hề đổi vì tôi không chạm vào cách nhúng của câu này). Nhồi metadata **giống nhau** vào nội dung nhúng không giúp phân biệt gì cả, chỉ gây nhiễu. Nếu muốn dùng metadata để giải quyết đúng 2 failure case trên, cách đúng hơn là chunker theo heading/điều khoản (mỗi chunk có "danh tính" riêng, không phải metadata cấp file dùng chung) — đúng như đề xuất sửa đã ghi ở 2 failure case phía trên.

---

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 (42/42 test pass) |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 6 / 10 (chấm evidence-based theo gold_string, xem Mục 5 — không tính theo `doc_id` hời hợt) |
| **Tổng phần cá nhân** | **56 / 60** |
