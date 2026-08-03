# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** Nhóm K4 - E-Commerce Policy Experts  
**Thành viên:** Nguyễn Minh Đạt, Nguyễn Thị Hương Trà, Trần Hoàng Mai Anh, Nguyễn Hùng Mạnh  
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

> **Lưu ý:** `ChunkingStrategyComparator.compare()` dùng cùng `chunk_size` cho `FixedSizeChunker` (overlap=0) và `RecursiveChunker`. Ở `chunk_size=300`, `RecursiveChunker` tạo **nhiều chunk hơn và ngắn hơn** `FixedSizeChunker` trên cả 3 tài liệu — vì văn bản chính sách có rất nhiều đoạn ngắn (mục a/b/c, điều khoản con) nên bộ tách `["\n\n","\n",". "," ",""]` dừng sớm ở các đoạn đó thay vì gộp đủ 300 ký tự. Đây là lý do nhóm chọn `chunk_size=500–600` (xem chiến lược của Nguyễn Thị Hương Trà bên dưới) thay vì dùng mặc định `300` khi triển khai thực tế.

### Chiến lược của từng thành viên

**Thành viên 1 — Nguyễn Minh Đạt**
- **Loại chiến lược:** Fixed-Length Chunking (`FixedSizeChunker`, tham số mặc định `chunk_size=500`, `overlap=50`)
- **Mô tả & lý do chọn:** Dùng nguyên tham số mặc định của `FixedSizeChunker` làm đường cơ sở, không tinh chỉnh — mục tiêu là có một baseline dễ tái lập để đối chiếu.
- **Ưu điểm:** Đơn giản, tính toán nhanh, dễ tái lập (deterministic hoàn toàn theo `chunk_size`/`overlap`).
- **Nhược điểm:** Cắt cứng theo ký tự nên các đoạn nói cùng chủ đề (thời hạn, khiếu nại...) dễ đứng gần điểm số nhau, khiến đoạn chứa đúng số liệu không nổi bật lên top-1 (xem Failure case 1 bên dưới).
- **Đã tự verify (báo cáo cá nhân):** report/REPORT_NguyenMinhDat.md — dùng phương pháp chấm theo `gold_string` (khớp nội dung, không chỉ `doc_id`), phát hiện 2 failure case có bằng chứng cụ thể.

**Thành viên 2 — Nguyễn Thị Hương Trà**
- **Loại chiến lược:** Hierarchical Chunking (`RecursiveChunker`, `chunk_size=600`, separators=`["\n# ", "\n## ", "\n### ", "\n\n", "\n"]`)
- **Mô tả & lý do chọn:** Chia theo cấu trúc tiêu đề (heading, section, subsection) của tài liệu chính sách Markdown. Bám sát cách tác giả tổ chức văn bản pháp lý.
- **Ưu điểm:** Bám sát cấu trúc phân cấp tài liệu, giữ trọn vẹn toàn bộ một Điều/Mục chính sách.
- **Nhược điểm:** Nếu tài liệu gốc trình bày không nhất quán về heading thì hiệu quả giảm.
- **Code snippet:**
```python
chunker = RecursiveChunker(chunk_size=600, separators=["\n# ", "\n## ", "\n### ", "\n\n", "\n"])
```
- **Theo báo cáo cá nhân** (`report/REPORT_NguyenThiHuongTra.md`): Trà còn tự thử nghiệm thêm so sánh 4 cấu hình (Fixed/Sentence/Recursive/Hierarchical) và chọn **SentenceChunker** làm cấu hình chấm điểm đại diện, tự báo cáo đạt **9/10** (evidence top-1 cho 4/5 câu).

**Thành viên 3 — Trần Hoàng Mai Anh**
- **Loại chiến lược:** Semantic Chunking tự thiết kế (`SemanticChunker` — chia theo độ tương đồng cosine giữa các câu liên tiếp, đóng chunk khi similarity giữa 2 câu liền kề thấp hơn ngưỡng) kết hợp hybrid rerank (`expand_query` + 75% điểm semantic/25% điểm keyword) trong `src/store.py`.
- **Mô tả & lý do chọn:** Thay vì cắt theo ranh giới cố định, chunk được đóng lại khi nội dung "chuyển ý" về mặt ngữ nghĩa — phù hợp với văn bản chính sách có nhiều đoạn liền mạch nhưng đổi chủ đề đột ngột.
- **Kết quả tự báo cáo** (`report/REPORT_TRANHOANGMAIANH.md`): so sánh 4 cấu hình (Fixed/Sentence/Semantic/Recursive), chọn **RecursiveChunker** làm cấu hình đại diện chấm điểm, tự báo cáo đạt **6/10**.

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

**Số liệu thật** (chạy lại bằng `EMBEDDING_PROVIDER=local`, đúng 5 query + gold target đã chốt trong `scripts/benchmark_experiment.py`, chấm theo `doc_id` xuất hiện ở top-3/top-1 — cùng phương pháp cho cả 3 để so sánh công bằng):

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10, theo doc_id) | Điểm theo nội dung chunk thật (gold_string, xem ghi chú) | Ưu điểm | Nhược điểm |
|-----------|----------|----------------------|----------------------|-----------|----------|
| **Nguyễn Minh Đạt** | Fixed-Length (500/50, mặc định) | 8 / 10 | **6 / 10** (tự chấm, xem `REPORT_NguyenMinhDat.md`) | Đơn giản, nhanh, dễ tái lập. | Chunk đúng chủ đề nhưng thường lệch mất đúng số liệu (xem Failure case của Đạt). |
| **Nguyễn Hùng Mạnh** | Overlap (300/50) | 9 / 10 | **6 / 10** (tự chấm, xem `REPORT_CANHAN.md`) | Giữ ngữ cảnh biên khi ý nghĩa trải dài qua chunk. | Tăng số lượng chunk và chi phí lưu trữ vector; vẫn tách rời các mốc thời gian gần nhau. |
| **Nguyễn Thị Hương Trà** | Hierarchical (600); tự so sánh thêm SentenceChunker | 9 / 10 (Hierarchical, xác minh riêng: Câu 1 chunk top-1 chứa nguyên văn "15 mười lăm ngày") | **9 / 10** (SentenceChunker, tự chấm — xem `REPORT_NguyenThiHuongTra.md`) | Bám sát cấu trúc Điều/Mục, giữ trọn ngữ cảnh chính sách. | Phụ thuộc vào định dạng Markdown chuẩn của tài liệu. |
| **Trần Hoàng Mai Anh** | Semantic Chunking tự thiết kế (đại diện chấm: RecursiveChunker) | — | **6 / 10** (tự chấm — xem `REPORT_TRANHOANGMAIANH.md`) | Đóng chunk theo biến động ngữ nghĩa thay vì ranh giới cố định. | Tự báo cáo: nhồi metadata cấp tài liệu giống nhau vào mọi chunk có thể pha loãng khả năng phân biệt giữa các chunk. |

> **Phát hiện quan trọng — chấm theo `doc_id` khác hẳn chấm theo nội dung chunk thật:** Với 2 chiến lược Fixed-length đã tự verify sâu (Đạt, Mạnh), điểm theo `doc_id` (8-9/10) tụt xuống còn 6/10 khi kiểm tra chunk top-1 có thực sự **chứa đúng câu/số liệu trả lời được câu hỏi** hay không (phương pháp `gold_string`, đúng tinh thần "Chấm ở mức chunk, không chỉ doc_id" của Codelabs): nhiều chunk top-1 tuy đúng tài liệu (`returns-policy`) nhưng lại là đoạn nói về mốc thời gian *khác* (vd. "03–05 ngày hoàn phí ship" hoặc "02 ngày phản hồi của Người Bán") thay vì đúng đoạn "15 ngày" mà Câu 1 hỏi. Ngược lại, chunking theo heading/điều khoản (Hierarchical) có chunk top-1 cho Câu 1 **chứa nguyên văn** "15 (mười lăm) ngày" — bằng chứng cụ thể, tái lập được, cho chiến lược này. Đây đúng là "chênh lệch đáng giá nhất" mà bài lab muốn nhóm phát hiện.

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> **Hierarchical Chunking (600)** do **Nguyễn Thị Hương Trà** phụ trách vẫn là chiến lược tốt nhất, nhưng giờ có bằng chứng ở mức chunk chứ không chỉ điểm số doc_id: các điều khoản pháp lý trên sàn TMĐT được tổ chức theo Chương/Điều/Mục có tiêu đề phân cấp rõ ràng, nên chia theo heading giữ trọn một quy định (ví dụ toàn bộ Mục 3.2 về thời hạn 15 ngày) trong cùng 1 chunk — không bị pha lẫn với các mốc thời gian khác trong cùng tài liệu như 2 chiến lược fixed-length.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Thời hạn gửi yêu cầu trả hàng và hoàn tiền trên Shopee là bao lâu? | Người Mua có thể gửi yêu cầu trả hàng/hoàn tiền trong vòng 15 ngày kể từ lúc đơn hàng được cập nhật giao hàng thành công (riêng thực phẩm tươi sống/đông lạnh là 24 giờ). | `k4-returns-policy::chunk_3` |
| 2 | Người bán bị xử lý thế nào khi vi phạm quy định đăng bán sản phẩm bị cấm? | Người Bán bị xóa sản phẩm vi phạm, khoá/tạm khóa tài khoản Người Bán, tước danh hiệu Shop Yêu Thích và có thể bị báo cáo lên cơ quan nhà nước có thẩm quyền. | `k4-seller-listing::chunk_1` (Filter: `customer_role=seller`) |
| 3 | Quy định về thời gian phản hồi của Người Bán khi nhận yêu cầu trả hàng là bao lâu? | Người Bán cần gửi phản hồi trong vòng 02 ngày lịch kể từ ngày nhận được thông báo của Shopee nếu không đồng ý với quyết định hoàn tiền. | `k4-returns-policy::chunk_8` |
| 4 | Điều kiện để Người Mua nhận hoàn tiền khi thanh toán đơn hàng bằng COD là gì? | Tài khoản Shopee của Người Mua phải liên kết thành công với phương thức nhận hoàn tiền hợp lệ (Ví ShopeePay hoặc Tài khoản ngân hàng). | `k4-payment-policy::chunk_4` |
| 5 | Người dùng có quyền yêu cầu xóa hoặc rút lại sự đồng ý sử dụng dữ liệu cá nhân không? | Người dùng có quyền gửi yêu cầu rút lại sự đồng ý hoặc yêu cầu xóa dữ liệu cá nhân bằng cách liên hệ Nhân viên bảo vệ dữ liệu cá nhân của Shopee. | `k4-privacy-policy::chunk_12` |

### Tổng hợp chất lượng truy xuất của nhóm

Bảng dưới tổng hợp kết quả thật (top-1 doc_id + có chứa đúng nội dung/gold_string hay không) trên 3 chiến lược đã verify — Fixed(500/50, Đạt), Overlap(300/50, Mạnh), Hierarchical(600, Trà):

| # | Câu hỏi | Chiến lược cho top-1 **đúng nội dung** (không chỉ đúng doc_id) | Ghi chú |
|---|---------|-------------------------------|---------|
| 1 | Thời hạn gửi yêu cầu trả hàng và hoàn tiền trên Shopee là bao lâu? | **Chỉ Hierarchical (Trà)** | Fixed(500/50) và Overlap(300/50) đều đúng *tài liệu* (`returns-policy`) nhưng top-1 là đoạn khác (03–05 ngày hoàn phí ship / 02 ngày phản hồi Người Bán); chunk chứa đúng "15 ngày" xếp hạng #10 (Đạt) / ngoài top-10 (Mạnh). Hierarchical giữ trọn Mục 3.2 nên top-1 chứa nguyên văn "15 (mười lăm) ngày". |
| 2 | Người bán bị xử lý thế nào khi vi phạm quy định đăng bán sản phẩm bị cấm? | Cả 3 chiến lược | **Dùng `metadata_filter={"customer_role": "seller"}`**: cả 3 đều đạt top-1 đúng nội dung xử lý vi phạm. |
| 3 | Quy định về thời gian phản hồi của Người Bán khi nhận yêu cầu trả hàng là bao lâu? | Fixed(500/50, Đạt) và Overlap(300/50, Mạnh) | Top-1 của cả hai đều chứa đúng "02 ngày lịch". |
| 4 | Điều kiện để Người Mua nhận hoàn tiền khi thanh toán đơn hàng bằng COD là gì? | Cả 3 chiến lược, nhưng target chính thức (`k4-payment-policy`) chỉ ở top-2/top-3 | Top-1 thực tế của cả 3 là `k4-returns-policy` Mục 3.3 (nội dung COD/liên kết hoàn tiền) — xem ghi chú golden test ở Phần 3. |
| 5 | Người dùng có quyền yêu cầu xóa hoặc rút lại sự đồng ý sử dụng dữ liệu cá nhân không? | Không chiến lược nào đạt top-1 tuyệt đối | Cả 3 đều đúng tài liệu (`privacy-policy`) nhưng đoạn "Rút Lại Sự Đồng Ý" (Mục 13.1) thường ở top-2/top-3, không phải top-1 — xem Failure case liên quan trong Phần 4. |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> **Lọc bằng metadata cực kỳ hiệu quả.** Đặc biệt ở **Câu hỏi số 2** (dành cho người bán), khi áp dụng `metadata_filter={"customer_role": "seller"}`, hệ thống loại bỏ hoàn toàn các tài liệu dành cho người mua và trả về chính xác 100% chunk quy định xử lý người bán vi phạm ở vị trí **Top-1**. Việc tiền lọc (pre-filtering) bằng metadata giúp loại bỏ nhiễu ngữ nghĩa tuyệt đối trước khi thực hiện so sánh vector similarity.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

### Phân Tích Lỗi (Failure Analysis) — Bài tập 3.5

**Failure case chính (từ chính 5 câu hỏi benchmark của nhóm) — do Nguyễn Minh Đạt phát hiện, đã verify lại khớp 100%:**

- **Câu 1** (Fixed-Length 500/50): top-3 gồm `shipping-policy` (0.767), `returns-policy` (0.760), `returns-policy` (0.739) — không chunk nào chứa số "15 (mười lăm) ngày". Chunk chứa đúng đáp án xếp hạng **#10/284** (score 0.646) trong toàn bộ store — quá thấp để lọt top-3. Nguyên nhân: `returns-policy.md` có nhiều đoạn cùng nói về "thời hạn"/"hoàn tiền" (Điều 9.3, khiếu nại vận chuyển...) nên cạnh tranh điểm số với đúng đoạn chứa đáp án (Điều 3.2); `FixedSizeChunker` cắt cứng theo ký tự khiến Điều 3.2 bị tách rời khỏi phần mở đầu, không "cộng dồn" được độ liên quan. Đề xuất: chunker theo điều khoản/heading (đã verify ở trên: Hierarchical giải quyết đúng case này), hoặc tăng `top_k`.
- **Câu 5** (Fixed-Length 500/50): cả 3/3 top-3 đều đúng tài liệu `privacy-policy` nhưng không chunk nào chứa `"dpo.vn@shopee.com"` (đầu mối liên hệ thật để thực hiện quyền, Điều 13.1.1) — chunk đúng xếp hạng #11/284. Nguyên nhân: `privacy-policy.md` là tài liệu dài nhất (96 chunk khi chia 500/50, gần 1/3 tổng corpus), nhiều đoạn đều "nói về quyền riêng tư" nói chung nên đoạn cụ thể (Mục 13) dễ bị các đoạn khác lấn át dù không trả lời trực tiếp câu hỏi.

*(Chi tiết đầy đủ + phương pháp chấm theo `gold_string`: xem `report/REPORT_NguyenMinhDat.md`.)*

**Failure case bổ sung (từ tầng agent, phát hiện thêm ngoài 5 câu benchmark chính thức):** Câu hỏi *"Chính sách bảo mật của Shopee bảo vệ dữ liệu người dùng như thế nào?"* (biến thể gần với chủ đề Câu hỏi #5 trong bộ benchmark) khi đi qua `KnowledgeBaseAgent.answer()` (tầng agent triển khai cho chatbot, không phải gọi thẳng `EmbeddingStore.search()`).

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
> Cùng một bộ tài liệu chính sách, các chiến lược chunking khác nhau tạo ra sự chênh lệch rõ rệt — nhưng chỉ thấy rõ khi chấm ở mức nội dung chunk, không chỉ ở mức `doc_id`. Cả 2 chiến lược fixed-length (Đạt 500/50, Mạnh 300/50) đều đúng tài liệu cho hầu hết câu hỏi (8-9/10 theo `doc_id`) nhưng tụt còn 6/10 khi kiểm tra chunk top-1 có thực sự chứa đúng số liệu/điều khoản hay không. Chunking theo heading/điều khoản (`Recursive=600`, Trà) là chiến lược duy nhất verify được ở mức chunk cho Câu 1 — bằng chứng cụ thể nhất trong buổi benchmark của nhóm.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ bổ sung thêm các trường metadata chi tiết hơn như `section_title` (tiêu đề mục) cho từng chunk. Mai Anh đã thử hướng **Semantic Chunking** (chia nhỏ dựa trên biến thiên độ tương đồng vector giữa các câu) — nhóm sẽ tiếp tục khai thác hướng này ở các lần benchmark sau.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **40 / 40** |
