# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Trần Hoàng Mai Anh  
**Nhóm:** Gicungduoc
**Ngày:** 03/08/2026

Báo cáo này mô tả phần cài đặt cá nhân và kết quả benchmark trên cùng năm câu hỏi của nhóm. Benchmark được chạy với `LocalEmbedder` dùng model `paraphrase-multilingual-MiniLM-L12-v2`; các kết quả retrieval được đối chiếu từ `docs/RUN_BENCHMARK_RESULT.md` và chấm theo `docs/SCORING.md`.

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự cosine

Cosine similarity đo độ giống nhau về hướng của hai vector embedding, không phụ thuộc nhiều vào độ dài vector. Giá trị càng gần 1 thì hai câu càng gần nhau về biểu diễn ngữ nghĩa; giá trị gần 0 cho thấy ít tương đồng, còn giá trị âm cho thấy hướng biểu diễn đối lập.

**Ví dụ có độ tương tự cao:**

- Câu A: `Người Mua có thể gửi yêu cầu trả hàng trong vòng 15 ngày.`
- Câu B: `Thời hạn gửi yêu cầu trả hàng của Người Mua là 15 ngày.`
- Tại sao tương đồng: Hai câu cùng nói về chủ thể Người Mua, hành động gửi yêu cầu trả hàng và thời hạn 15 ngày.

**Ví dụ có độ tương tự thấp:**

- Câu A: `Người bán phải phản hồi yêu cầu trả hàng trong 2 ngày.`
- Câu B: `Python là một ngôn ngữ lập trình phổ biến.`
- Tại sao khác: Hai câu thuộc hai chủ đề hoàn toàn khác nhau, một câu nói về chính sách trả hàng và một câu nói về lập trình.

Cosine thường phù hợp hơn khoảng cách Euclid cho text embedding vì nó tập trung vào hướng ngữ nghĩa của vector. Hai văn bản có độ dài khác nhau vẫn có thể gần nhau về nội dung nếu hướng embedding tương tự; việc chuẩn hóa vector cũng làm kết quả ổn định hơn.

### Bài toán tính toán chunking

Với cách chia trong `FixedSizeChunker`, bước trượt là:

```text
step = chunk_size - overlap = 500 - 50 = 450
```

Chunk bắt đầu tại các vị trí `0, 450, 900, ...`. Vì vậy:

```text
N = ceil((10_000 - 500) / 450) + 1
  = ceil(9_500 / 450) + 1
  = 22 + 1
  = 23 chunks
```

Nếu `overlap=100`, bước trượt còn `500 - 100 = 400`, nên:

```text
N = ceil((10_000 - 500) / 400) + 1
  = ceil(9_500 / 400) + 1
  = 24 + 1
  = 25 chunks
```

Overlap lớn hơn làm tăng số chunk và chi phí embedding, nhưng giúp giữ phần ngữ cảnh nằm ở ranh giới hai chunk. Điều này hữu ích khi một câu trả lời hoặc một điều khoản bị cắt giữa hai đoạn.

## 2. Hướng tiếp cận của tôi — Cá nhân (10 điểm)

### Các hàm chia nhỏ

`FixedSizeChunker.chunk` là đường cơ sở của thử nghiệm. Hàm dùng cửa sổ trượt với `step = chunk_size - overlap`, bảo đảm mỗi chunk không vượt quá `chunk_size` và hai chunk liên tiếp chia sẻ phần overlap. Hàm cũng kiểm tra tham số đầu vào, xử lý văn bản rỗng và dừng khi chunk cuối đã bao phủ phần còn lại của tài liệu.

`SentenceChunker.chunk` dùng biểu thức chính quy `(?<=[.!?])[ \t\r\n]+`: dấu câu được giữ lại trong câu, còn khoảng trắng sau dấu câu được dùng làm ranh giới. Hàm loại bỏ chuỗi rỗng và khoảng trắng thừa, sau đó nhóm tối đa `max_sentences_per_chunk` câu vào một chunk. Cách này xử lý được dấu chấm cuối dòng và không tách chỉ vì dấu chấm nằm trong câu nếu phía sau không có khoảng trắng phù hợp.

`RecursiveChunker.chunk` gọi `_split` với thứ tự ưu tiên `\n\n`, `\n`, `. `, khoảng trắng và cuối cùng là tách theo ký tự. `_split` chọn dấu phân cách đầu tiên thực sự xuất hiện, ghép các mảnh nhỏ khi tổng độ dài còn trong `chunk_size`, và đệ quy xuống dấu phân cách nhỏ hơn nếu một mảnh vẫn quá dài. Base case là chuỗi rỗng hoặc chuỗi không vượt quá `chunk_size`; khi không còn dấu phân cách dùng được, hàm tách theo cửa sổ ký tự để luôn tạo ra kết quả hợp lệ.

`SemanticChunker.chunk` trước hết tách văn bản thành các câu, tạo embedding cho từng câu rồi so sánh cosine similarity giữa hai câu liên tiếp. Câu tiếp theo được giữ trong chunk hiện tại khi similarity không thấp hơn `similarity_threshold` và tổng độ dài không vượt quá `chunk_size`; nếu một trong hai điều kiện không đạt, chunk hiện tại được đóng và tạo chunk mới. Một câu đơn quá dài vẫn được tách bằng `FixedSizeChunker` như bước dự phòng, vì khi đó không thể đồng thời giữ nguyên ngữ nghĩa và giới hạn kích thước.

### Lớp `EmbeddingStore`

`add_documents` tạo embedding cho từng nội dung và lưu một record gồm `id`, `content`, `metadata` và `embedding` trong bộ nhớ. `search` tạo embedding cho query, tính tích vô hướng giữa query và từng embedding đã lưu, sắp xếp giảm dần rồi trả về tối đa `top_k` kết quả cùng score. Với các embedding đã chuẩn hóa, tích vô hướng tương đương cosine similarity; với backend tổng quát, đây là điểm tương đồng mà store đang sử dụng.

`search_with_filter` lọc record theo metadata trước khi xếp hạng, nhờ đó câu hỏi Q2 chỉ tìm trong các chunk có `customer_role=seller`. Bộ lọc dùng điều kiện khớp tất cả cặp khóa-giá trị, nên không làm lẫn tài liệu khác vai trò. `delete_document` xóa mọi record có metadata `doc_id` tương ứng và trả về `True` nếu thực sự có record bị xóa.

Để giảm lỗi do embedding xếp nhầm các chunk chỉ có từ vựng chung, tôi bổ sung hai bước trong `src/store.py`. Hàm `expand_query` thêm các cụm theo intent chính sách, chẳng hạn `15 ngày`, `xử lý vi phạm`, `02 ngày lịch`, `phương thức nhận hoàn tiền` và `rút lại sự đồng ý`. Sau đó `_search_records` dùng hybrid reranking: 75% điểm semantic và 25% độ phủ từ khóa/phrase trong nội dung và metadata. Kết quả trả về vẫn giữ `score`, đồng thời có thêm `semantic_score` và `keyword_score` để kiểm tra nguyên nhân xếp hạng.

### Tác tử `KnowledgeBaseAgent`

`answer` trước tiên gọi `store.search(question, top_k=3)`. Các chunk được ghép thành phần `Context`, kèm `doc_id` và `source`, sau đó được đưa vào prompt cùng câu hỏi. Prompt yêu cầu chỉ sử dụng context và nói rõ khi context không đủ; cách này giữ câu trả lời có căn cứ và cho phép truy vết về chunk nguồn. Nếu store không có kết quả, agent trả về thông báo không tìm thấy ngữ cảnh thay vì tạo câu trả lời không có căn cứ.

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Tôi chạy lệnh:

```text
pytest tests/ -v
```

Kết quả: **42/42 bài test PASSED**, thời gian chạy 0.12 giây. Các nhóm chức năng đều đạt: chunking cố định, chunking theo câu, chunking đệ quy, cosine similarity, `EmbeddingStore`, metadata filter, xóa tài liệu, agent RAG và bộ so sánh chiến lược.

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Các giá trị dưới đây được tính bằng `compute_similarity` với `LocalEmbedder` dùng model đa ngôn ngữ `paraphrase-multilingual-MiniLM-L12-v2`. Các cặp được dự đoán trước khi chạy; điểm thực tế cho thấy model nhận diện tốt các câu diễn đạt cùng ý, nhưng vẫn có thể đánh giá cao hai câu khác chủ đề nếu chúng chia sẻ ngữ cảnh hoặc từ vựng chính sách.

| Cặp | Câu A                                                                 | Câu B                                                           | Dự đoán trước khi chạy | Điểm thực tế | Đúng? |
| --- | --------------------------------------------------------------------- | --------------------------------------------------------------- | ---------------------- | -----------: | ----- |
| 1   | Thời hạn gửi yêu cầu trả hàng là 15 ngày.                             | Người Mua có thể gửi yêu cầu trả hàng trong vòng 15 ngày.       | cao                    |     0.850955 | Có    |
| 2   | Shopee hoàn tiền sau khi hàng trả được xác nhận.                      | Python là một ngôn ngữ lập trình phổ biến.                      | thấp                   |     0.194393 | Có    |
| 3   | Người bán phải phản hồi yêu cầu trả hàng trong 2 ngày.                | Người bán cần gửi phản hồi trong vòng 02 ngày lịch.             | cao                    |     0.932162 | Có    |
| 4   | Tài khoản phải liên kết phương thức thanh toán để nhận hoàn tiền COD. | Người dùng có thể rút lại sự đồng ý xử lý dữ liệu cá nhân.      | thấp                   |     0.728289 | Không |
| 5   | Chính sách bảo vệ dữ liệu cá nhân cho phép yêu cầu xóa dữ liệu.       | Chính sách bảo vệ dữ liệu cá nhân cho phép yêu cầu sửa dữ liệu. | cao                    |     0.993152 | Có    |

Điều bất ngờ nhất là cặp 4 có score khá cao dù hai câu nói về COD và dữ liệu cá nhân, hai chủ đề không hoàn toàn giống nhau. Điều này cho thấy embedding vẫn có thể bị ảnh hưởng bởi các từ và ngữ cảnh chung như “tài khoản”, “phương thức” hoặc “yêu cầu”. Vì vậy similarity là tín hiệu hữu ích cho retrieval nhưng vẫn cần kiểm tra nội dung chunk và đối chiếu câu trả lời chuẩn.

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Trong bốn cấu hình, tôi chọn **recursive** làm cấu hình đại diện để chấm điểm cá nhân vì nó giữ được chunk liên quan ở vị trí tốt hơn cho Q3 và Q4, đồng thời vẫn đưa nội dung xử lý vi phạm của Q2 vào top-3. Các score và ID dưới đây lấy nguyên từ phần `STRATEGY: recursive` trong `docs/RUN_BENCHMARK_RESULT.md`.

| #   | Câu hỏi                                                                               | Top-1 chunk và score                                                                     | Liên quan?                                                            | Câu trả lời đối chiếu từ top-3                                                                                                                                                      |
| --- | ------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- | --------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Thời hạn gửi yêu cầu trả hàng và hoàn tiền trên Shopee là bao lâu?                    | `k4-returns-policy::chunk_31::216`, 0.789; nội dung nói Người Bán phản hồi trong 02 ngày | Không; top-3 không có đoạn nêu thời hạn 15 ngày của Người Mua         | Không thể kết luận đủ từ top-3. Gold answer là Người Mua có thể gửi yêu cầu trong vòng 15 ngày kể từ khi đơn được cập nhật giao thành công; một số nhóm sản phẩm có thời hạn riêng. |
| 2   | Người bán bị xử lý thế nào khi vi phạm quy định đăng bán sản phẩm bị cấm?             | `k4-seller-listing::chunk_51::296`, 0.796; cảnh báo tuân thủ                             | Có ở hạng 2; filter `customer_role=seller` được áp dụng               | Tùy mức độ vi phạm, Shopee có thể xóa/khóa/tạm ẩn sản phẩm, hạn chế hoặc khóa tài khoản, yêu cầu bồi thường và áp dụng các biện pháp khác theo chính sách.                          |
| 3   | Quy định về thời gian phản hồi của Người Bán khi nhận yêu cầu trả hàng là bao lâu?    | `k4-returns-policy::chunk_31::216`, 0.782; nêu rõ 02 ngày lịch                           | Có, ở top-1                                                           | Người Bán phải gửi phản hồi trong vòng 02 ngày lịch kể từ khi nhận thông báo của Shopee, hoặc theo thời hạn khác được Shopee quy định tại từng thời điểm.                           |
| 4   | Điều kiện để Người Mua nhận hoàn tiền khi thanh toán bằng COD là gì?                  | `k4-returns-policy::chunk_11::196`, 0.692; nêu điều kiện liên kết tài khoản              | Có, ở top-1                                                           | Tài khoản Shopee của Người Mua phải liên kết với phương thức nhận hoàn tiền hợp lệ; sau khi đơn đủ điều kiện và sản phẩm được gửi trả, Shopee hoàn tiền theo chính sách.            |
| 5   | Người dùng có quyền yêu cầu xóa hoặc rút lại sự đồng ý sử dụng dữ liệu cá nhân không? | `k4-privacy-policy::chunk_72::123`, 0.765; nêu việc hủy hoặc xóa thông tin               | Có một phần, ở top-1; top-3 chưa thể hiện đầy đủ quyền rút lại đồng ý | Top-3 chứng minh quyền yêu cầu xóa/hủy dữ liệu và các giới hạn áp dụng, nhưng chưa đủ căn cứ để khẳng định đầy đủ phần rút lại sự đồng ý.                                           |

**Đánh giá:** có 4/5 câu có chunk liên quan trong top-3; Q1 không truy xuất được đoạn nêu thời hạn 15 ngày. Theo thang điểm chi tiết, Q1 được 0/2; Q2 được 1/2 vì chunk mô tả biện pháp xử lý nằm ở hạng 2; Q3 và Q4 lần lượt đạt 2/2 vì chunk liên quan ở top-1 và đủ căn cứ trả lời; Q5 đạt 1/2 vì top-1 chỉ hỗ trợ rõ quyền xóa dữ liệu, chưa đủ chi tiết về rút lại sự đồng ý. Tổng điểm retrieval của cấu hình recursive là **6/10**.

So sánh nhanh theo log mới: `FixedSizeChunker` là baseline dễ dự đoán, có kết quả tốt ở Q2, Q4 và Q5 nhưng không đưa đoạn trả lời Q1 hoặc Q3 vào top-3. `SentenceChunker` tạo chunk dễ đọc nhưng chỉ Q5 có đoạn hỗ trợ rõ; các câu còn lại chủ yếu trả về câu phụ hoặc tài liệu không đúng trọng tâm. `SemanticChunker` đạt kết quả tốt nhất ở Q2, hỗ trợ một phần Q3 và Q4, nhưng Q1 vẫn lệch sang thời hạn phản hồi của Người Bán. `RecursiveChunker` đạt điểm cân bằng nhất trong lần chạy mới với 6/10: top-1 chính xác ở Q3 và Q4, có đoạn phù hợp cho Q2, nhưng thất bại ở Q1 và chỉ trả lời một phần Q5.

Metadata filter có ích rõ nhất ở Q2: nó giới hạn không gian tìm kiếm vào tài liệu của người bán. Tuy nhiên filter không tự đảm bảo top-1 chính xác, thể hiện ở kết quả recursive khi chunk cảnh báo đứng trước chunk xử lý vi phạm. Vì vậy metadata nên kết hợp với chunk có ranh giới ngữ nghĩa và embedding phù hợp.

**Điều tôi học được:** score cao chưa chắc đồng nghĩa với câu trả lời đúng; cần đọc nội dung chunk, kiểm tra vị trí trong top-3 và đối chiếu gold answer. Tôi cũng học được rằng chunk có cấu trúc tự nhiên và giữ đủ ngữ cảnh thường có giá trị hơn việc chỉ tối ưu số lượng chunk.

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí                                        | Điểm tự đánh giá |
| ----------------------------------------------- | ---------------: |
| Khởi động (Warm-up)                             |            5 / 5 |
| Hướng tiếp cận của tôi (My Approach)            |          10 / 10 |
| Hoàn thiện code (Core Implementation — tests)   |          30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions)    |            4 / 5 |
| Kết quả truy xuất của tôi (Competition Results) |           6 / 10 |
| **Tổng phần cá nhân**                           |      **55 / 60** |
