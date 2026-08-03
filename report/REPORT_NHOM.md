# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** Nhóm K4 - E-Commerce Policy Experts  
**Thành viên:** Nguyễn Minh Đạt, Nguyễn Hương Trà, Nguyễn Thị Mai Anh, Nguyễn Hùng Mạnh  
**Ngày:** 03/08/2026  

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K4):** Chính sách thương mại điện tử / hỗ trợ khách hàng (thanh toán, đổi trả, giao hàng, quyền riêng tư, điều kiện người bán…).

**Phạm vi cụ thể nhóm tập trung:**
> Nhóm tập trung thu thập toàn bộ 5 tài liệu chính sách nền tảng của Sàn TMĐT Shopee Việt Nam bao gồm: Chính sách đổi trả & hoàn tiền, Quy định đăng bán & hàng cấm, Chính sách vận chuyển, Điều khoản thanh toán & ví ShopeePay/SPayLater, và Chính sách bảo mật thông tin cá nhân.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Chính sách trả hàng và hoàn tiền Shopee | `https://help.shopee.vn/portal/article/77251` | 2026-08-03 / 2026.1 | 19,683 | `customer_role: buyer`, `category: returns` |
| 2 | Quy định về đăng bán sản phẩm và hàng cấm | `https://help.shopee.vn/portal/article/77246` | 2026-08-03 / 2026.1 | 21,678 | `customer_role: seller`, `category: listing` |
| 3 | Chính sách vận chuyển và giao nhận Shopee | `https://help.shopee.vn/portal/article/77250` | 2026-08-03 / 2026.1 | 24,428 | `customer_role: buyer`, `category: shipping` |
| 4 | Điều khoản thanh toán và ví ShopeePay / SPayLater | `https://help.shopee.vn/portal/article/118121` | 2026-08-03 / 2026.1 | 18,012 | `customer_role: both`, `category: payment` |
| 5 | Chính sách bảo mật thông tin cá nhân | `https://help.shopee.vn/portal/article/77244` | 2026-08-03 / 2026.1 | 43,116 | `customer_role: both`, `category: privacy` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `customer_role` | `str` | `buyer`, `seller`, `both` | Phân loại vai trò người dùng để lọc chính xác khi câu hỏi chỉ dành cho Người bán hoặc Người mua. |
| `category` | `str` | `returns`, `listing`, `shipping`, `payment`, `privacy` | Định hướng phạm vi nghiệp vụ, cho phép lọc bỏ các bài viết ngoài danh mục cần tra cứu. |
| `source_url` | `str` | `https://help.shopee.vn/portal/article/77251` | Truy xuất nguồn gốc điều khoản, phục vụ việc trích dẫn trích lọc (citation/grounding). |
| `document_version`| `str` | `2026.1` | Đảm bảo tính hiệu lực thời gian của chính sách, tránh lấy các quy định đã cũ. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare(text, chunk_size=300)` trên 3 tài liệu (số liệu thật, tái lập được từ code):

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| `k4-returns-policy` | FixedSizeChunker (`fixed_size`) | 66 | 298.2 | Trung bình (bị ngắt giữa đoạn văn) |
| `k4-returns-policy` | SentenceChunker (`by_sentences`) | 47 | 415.7 | Tốt (giữ nguyên ranh giới câu) |
| `k4-returns-policy` | RecursiveChunker (`recursive`) | 101 | 192.7 | Tốt (ưu tiên ngắt ở `\n\n`/`\n`, nhưng ở `chunk_size=300` vẫn phải cắt vào dấu `. `/khoảng trắng khá thường xuyên) |
| `k4-seller-listing` | FixedSizeChunker (`fixed_size`) | 73 | 297.0 | Trung bình (bị ngắt giữa đoạn văn) |
| `k4-seller-listing` | SentenceChunker (`by_sentences`) | 78 | 274.6 | Tốt (giữ nguyên ranh giới câu) |
| `k4-seller-listing` | RecursiveChunker (`recursive`) | 104 | 206.3 | Tốt (giữ được các mục a/b/c liền mạch hơn fixed-size) |
| `k4-payment-policy` | FixedSizeChunker (`fixed_size`) | 61 | 295.3 | Trung bình (bị ngắt giữa đoạn văn) |
| `k4-payment-policy` | SentenceChunker (`by_sentences`) | 47 | 380.0 | Tốt (giữ nguyên ranh giới câu) |
| `k4-payment-policy` | RecursiveChunker (`recursive`) | 100 | 177.8 | Tốt (giữ cấu trúc điều khoản, nhưng chunk ngắn hơn 2 chiến lược còn lại ở `chunk_size=300`) |

> **Lưu ý:** `ChunkingStrategyComparator.compare()` dùng cùng `chunk_size` cho `FixedSizeChunker` (overlap=0) và `RecursiveChunker`. Ở `chunk_size=300`, `RecursiveChunker` tạo **nhiều chunk hơn và ngắn hơn** `FixedSizeChunker` trên cả 3 tài liệu — vì văn bản chính sách có rất nhiều đoạn ngắn (mục a/b/c, điều khoản con) nên bộ tách `["\n\n","\n",". "," ",""]` dừng sớm ở các đoạn đó thay vì gộp đủ 300 ký tự. Đây là lý do nhóm chọn `chunk_size=500–600` (xem chiến lược của Nguyễn Hương Trà bên dưới) thay vì dùng mặc định `300` khi triển khai thực tế.

### Chiến lược của từng thành viên

**Thành viên 1 — Nguyễn Minh Đạt**
- **Loại chiến lược:** Fixed-Length Chunking (`FixedSizeChunker`, `chunk_size=300`, `overlap=0`)
- **Mô tả & lý do chọn:** Chia văn bản theo số ký tự cố định 300 ký tự mà không xét ranh giới câu hay đoạn. Phù hợp cho việc prototype nhanh và dữ liệu khá đều.
- **Ưu điểm:** Đơn giản, tính toán nhanh, triển khai dễ dàng.
- **Nhược điểm:** Rất dễ bị cắt giữa chừng ý nghĩa của câu hoặc đoạn điều khoản chính sách.
- **Code snippet:**
```python
chunker = FixedSizeChunker(chunk_size=300, overlap=0)
```

**Thành viên 2 — Nguyễn Hương Trà**
- **Loại chiến lược:** Hierarchical Chunking (`RecursiveChunker`, `chunk_size=600`, separators=`["\n# ", "\n## ", "\n### ", "\n\n", "\n"]`)
- **Mô tả & lý do chọn:** Chia theo cấu trúc tiêu đề (heading, section, subsection) của tài liệu chính sách Markdown. Bám sát cách tác giả tổ chức văn bản pháp lý.
- **Ưu điểm:** Bám sát cấu trúc phân cấp tài liệu, giữ trọn vẹn toàn bộ một Điều/Mục chính sách.
- **Nhược điểm:** Nếu tài liệu gốc trình bày không nhất quán về heading thì hiệu quả giảm.
- **Code snippet:**
```python
chunker = RecursiveChunker(chunk_size=600, separators=["\n# ", "\n## ", "\n### ", "\n\n", "\n"])
```

**Thành viên 3 — Nguyễn Thị Mai Anh**
- **Loại chiến lược:** Sentence-Based Chunking (`SentenceChunker`, `max_sentences_per_chunk=3`)
- **Mô tả & lý do chọn:** Tách chunk dựa trên ranh giới câu (`. `, `! `, `? `). Phù hợp với các đoạn FAQ và câu hỏi trả lời ngắn.
- **Ưu điểm:** Giữ được đơn vị ngữ nghĩa nhỏ nhất tương đối hoàn chỉnh, câu chữ tự nhiên.
- **Nhược điểm:** Các câu trả lời quy định dài cần nhiều câu liên tiếp nên retrieval dễ bị rời rạc ngữ cảnh.
- **Code snippet:**
```python
chunker = SentenceChunker(max_sentences_per_chunk=3)
```

**Thành viên 4 — Nguyễn Hùng Mạnh**
- **Loại chiến lược:** Overlap Chunking (`FixedSizeChunker`, `chunk_size=300`, `overlap=50`)
- **Mô tả & lý do chọn:** Chia theo kích thước cố định 300 ký tự nhưng giữa các chunk liền kề có phần chồng lấn (overlap 50 ký tự). Phù hợp cho các điều khoản pháp lý khó ngắt rạch ròi.
- **Ưu điểm:** Giữ được ngữ cảnh khi ý nghĩa trải dài qua ranh giới chunk, tránh mất thông tin biên.
- **Nhược điểm:** Tăng số lượng chunk, tăng chi phí tính toán embedding và dung lượng lưu trữ vector store.
- **Code snippet:**
```python
chunker = FixedSizeChunker(chunk_size=300, overlap=50)
```

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Ưu điểm | Nhược điểm |
|-----------|----------|----------------------|-----------|----------|
| **Nguyễn Minh Đạt** | Fixed-Length (300/0) | 5 / 10 | Đơn giản, nhanh, khối lượng chunk đồng đều. | Rất dễ cắt giữa chừng ý nghĩa câu/đoạn. |
| **Nguyễn Thị Mai Anh** | Sentence-Based (3 câu) | 5 / 10 | Giữ đơn vị ngữ nghĩa câu hoàn chỉnh. | Retrieval dễ bị rời rạc khi quy định nằm trên nhiều câu. |
| **Nguyễn Hùng Mạnh** | Overlap (300/50) | 5.5 / 10 | Giữ ngữ cảnh biên khi ý nghĩa trải dài qua chunk. | Tăng số lượng chunk và chi phí lưu trữ vector. |
| **Nguyễn Hương Trà** | Hierarchical (600) | 6.5 / 10 | Bám sát cấu trúc Điều/Mục, giữ trọn ngữ cảnh chính sách. | Phụ thuộc vào định dạng Markdown chuẩn của tài liệu. |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> **Hierarchical Chunking (600)** do **Nguyễn Hương Trà** phụ trách là chiến lược tốt nhất cho bộ tài liệu chính sách thương mại điện tử Shopee. Lý do: Các điều khoản pháp lý trên sàn TMĐT được tổ chức theo các Chương, Điều, Mục có tiêu đề phân cấp rõ ràng (`#`, `##`, `###`). Việc chia chunk theo cấu trúc phân cấp giúp giữ trọn toàn bộ một quy định (ví dụ: toàn bộ Mục 1.1 về Điều kiện trả hàng) trong cùng 1 chunk, tránh bị xé nhỏ rời rạc hay cắt ngang giữa chừng ý nghĩa.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Thời hạn gửi yêu cầu trả hàng và hoàn tiền trên Shopee là bao lâu? | Người Mua có thể gửi yêu cầu trả hàng/hoàn tiền trong vòng 15 ngày kể từ lúc đơn hàng được cập nhật giao hàng thành công (riêng thực phẩm tươi sống/đông lạnh là 24 giờ). | `k4-returns-policy::chunk_3` |
| 2 | Người bán bị xử lý thế nào khi vi phạm quy định đăng bán sản phẩm bị cấm? | Người Bán bị xóa sản phẩm vi phạm, khoá/tạm khóa tài khoản Người Bán, tước danh hiệu Shop Yêu Thích và có thể bị báo cáo lên cơ quan nhà nước có thẩm quyền. | `k4-seller-listing::chunk_1` (Filter: `customer_role=seller`) |
| 3 | Quy định về thời gian phản hồi của Người Bán khi nhận yêu cầu trả hàng là bao lâu? | Người Bán cần gửi phản hồi trong vòng 02 ngày lịch kể từ ngày nhận được thông báo của Shopee nếu không đồng ý với quyết định hoàn tiền. | `k4-returns-policy::chunk_8` |
| 4 | Điều kiện để Người Mua nhận hoàn tiền khi thanh toán đơn hàng bằng COD là gì? | Tài khoản Shopee của Người Mua phải liên kết thành công với phương thức nhận hoàn tiền hợp lệ (Ví ShopeePay hoặc Tài khoản ngân hàng). | `k4-returns-policy` — Mục 3.3 (đã xác minh: nội dung COD/liên kết hoàn tiền nằm trong Chính sách Trả hàng &amp; Hoàn tiền, **không** nằm trong `k4-payment-policy` — tài liệu này chỉ nói về điều khoản SPayLater, không chứa từ "COD") |
| 5 | Người dùng có quyền yêu cầu xóa hoặc rút lại sự đồng ý sử dụng dữ liệu cá nhân không? | Người dùng có quyền gửi yêu cầu rút lại sự đồng ý hoặc yêu cầu xóa dữ liệu cá nhân bằng cách liên hệ Nhân viên bảo vệ dữ liệu cá nhân của Shopee. | `k4-privacy-policy::chunk_12` |

### Tổng hợp chất lượng truy xuất của nhóm

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Thời hạn gửi yêu cầu trả hàng và hoàn tiền trên Shopee là bao lâu? | SentenceChunker | Có (Top 2) | Trả về đúng quy định thời hạn 15 ngày. |
| 2 | Người bán bị xử lý thế nào khi vi phạm quy định đăng bán sản phẩm bị cấm? | RecursiveChunker | Có (Top 1 - Điểm 2/2) | **Dùng `metadata_filter={"customer_role": "seller"}`**: đạt độ chính xác 100% Top-1. |
| 3 | Quy định về thời gian phản hồi của Người Bán khi nhận yêu cầu trả hàng là bao lâu? | SentenceChunker | Có (Top 3) | Lấy đúng điều khoản 02 ngày lịch phản hồi của Người bán. |
| 4 | Điều kiện để Người Mua nhận hoàn tiền khi thanh toán đơn hàng bằng COD là gì? | RecursiveChunker | Có (Top 1 - Điểm 2/2) | Trả về chính xác quy định liên kết ngân hàng/ShopeePay. |
| 5 | Người dùng có quyền yêu cầu xóa hoặc rút lại sự đồng ý sử dụng dữ liệu cá nhân không? | RecursiveChunker | Có (Top 1 - Điểm 2/2) | Trả về chính xác quyền rút lại sự đồng ý bảo mật dữ liệu. |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> **Lọc bằng metadata cực kỳ hiệu quả.** Đặc biệt ở **Câu hỏi số 2** (dành cho người bán), khi áp dụng `metadata_filter={"customer_role": "seller"}`, hệ thống loại bỏ hoàn toàn các tài liệu dành cho người mua và trả về chính xác 100% chunk quy định xử lý người bán vi phạm ở vị trí **Top-1**. Việc tiền lọc (pre-filtering) bằng metadata giúp loại bỏ nhiễu ngữ nghĩa tuyệt đối trước khi thực hiện so sánh vector similarity.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

### Phân Tích Lỗi (Failure Analysis) — Bài tập 3.5

**Trường hợp thất bại phát hiện được:** Câu hỏi *"Chính sách bảo mật của Shopee bảo vệ dữ liệu người dùng như thế nào?"* (biến thể gần với chủ đề Câu hỏi #5 trong bộ benchmark) khi đi qua `KnowledgeBaseAgent.answer()` (tầng agent triển khai cho chatbot, không phải gọi thẳng `EmbeddingStore.search()`).

**So sánh có/không filter (đúng theo `docs/EVALUATION.md` — mục 3. Metadata Utility, yêu cầu "So sánh top-3 kết quả giữa `search()` và `search_with_filter()` trên cùng câu hỏi"):**

| Cách gọi | Top-1 trả về | `customer_role` | Score |
|---|---|---|---|
| `store.search()` — không filter (ground truth) | `k4-privacy-policy` | `both` | **0.83** |
| `agent.answer()` — có auto-filter role | `k4-returns-policy` | `buyer` | 0.69 |

**Tại sao thất bại?**
1. `KnowledgeBaseAgent._classify_intent()` ([src/agent.py:151](../src/agent.py#L151)) dùng danh sách từ khóa để tự đoán vai trò người hỏi. Từ "bảo mật" nằm trong `buyer_keywords`, nên câu hỏi trên bị tự động gán `intent="buyer"` dù người dùng không hề chọn role.
2. Agent sau đó tự áp `metadata_filter={"customer_role": "buyer"}` ([src/agent.py:180](../src/agent.py#L180)) — loại bỏ toàn bộ tài liệu gắn `customer_role: both` ra khỏi candidate pool, vì `search_with_filter()` ([src/store.py:137](../src/store.py#L137)) so khớp tuyệt đối (`meta.get(k) == v`): `"both" != "buyer"`.
3. Hệ quả: `k4-privacy-policy` (đúng nhất, score 0.83) và `k4-payment-policy` — cả 2 tài liệu gắn `both` (chiếm 40% corpus) — **biến mất hoàn toàn** bất cứ khi nào có filter buyer/seller được áp, dù nội dung của chúng liên quan đến cả hai vai trò.
4. Cơ chế fallback (`if not results: search không filter`) không cứu được vì filter vẫn trả về vài kết quả (chỉ là sai tài liệu), không rỗng.

**Đề xuất cải thiện:**
- Sửa `search_with_filter()` để coi `customer_role: both` tương thích với cả filter `buyer` và `seller` (không chỉ so khớp tuyệt đối).
- Thu hẹp `seller_keywords`/`buyer_keywords` trong `_classify_intent()`, bỏ các từ khóa chung chung dễ gây nhiễu (`"bảo mật"`, `"người bán"` xuất hiện cả trong văn bản không dành riêng một vai trò).
- Chỉ tự áp metadata filter khi độ tin cậy phân loại đủ cao, hoặc để người dùng chủ động chọn role thay vì suy đoán từ từ khóa đơn lẻ.

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
1. **Tác động của Metadata Pre-filtering:** Tiền lọc theo `customer_role` và `category` giúp tăng độ chính xác tìm kiếm lên đáng kể, giải quyết triệt để vấn đề nhiễu ngữ nghĩa giữa các chính sách trùng từ khóa (ví dụ từ "người bán" xuất hiện ở cả chính sách người mua và chính sách người bán).
2. **Ưu thế của Recursive Chunking với văn bản pháp lý:** Cấu trúc phân cấp của văn bản chính sách thương mại điện tử rất hợp với `RecursiveChunker`, vì giữ nguyên được ngữ cảnh của từng điều khoản thay vì ngắt quãng ngẫu nhiên theo số ký tự.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng một bộ tài liệu chính sách, các chiến lược chunking khác nhau tạo ra sự chênh lệch rõ rệt về chất lượng truy xuất. Phân đoạn quá nhỏ (`FixedSize=300`) làm mất ngữ cảnh điều khoản; trong khi phân đoạn đệ quy theo tiêu đề/đoạn văn (`Recursive=500`) đem lại sự cân bằng tối ưu giữa tính mạch lạc ngữ nghĩa và khả năng truy xuất của RAG Agent.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ bổ sung thêm các trường metadata chi tiết hơn như `section_title` (tiêu đề mục) cho từng chunk và thử nghiệm kỹ thuật **Semantic Chunking** (chia nhỏ dựa trên biến thiên độ tương đồng vector giữa các câu) thay vì chỉ dựa vào phân cách ký tự tĩnh.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **40 / 40** |
