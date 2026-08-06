# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Hoàng Xuân Quân     |
| MSSV               | 2A202601868          |
| Khóa/Lớp         | K4                         |
| Tên nhóm         | C53                        |
| Vai trò chính    | Data Platform, Cleaning, Repair & Pipeline Orchestration (Vai trò 1) |
| Repository         | https://github.com/lonhidol/K4_Day10_Data-Pipeline-Data-Observability_C53 |
| Ngày hoàn thành | 2026-08-06                 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Data Ingestion | `src/ingestion/crossref.py` -> `fetch_source_records`, `load_raw_records` | API settings, query, max_results | `data/raw/crossref_response.json` (Raw JSON payload), `crossref_records.json` (Parsed thô) | Hoàn thành |
| Data Cleaning | `src/ingestion/cleaning.py` -> `build_clean_dataframe` | Parsed records thô | `data/clean/papers_clean.csv`, `papers_clean.json` (Dữ liệu sạch 16 cột) | Hoàn thành |
| Data Corruption | `src/ingestion/corruption.py` -> `corrupt_clean_dataframe` | `df_clean` (pandas DataFrame) | `data/clean/papers_clean_corrupted.csv`, `data/results/corruption_log.json` | Hoàn thành |
| Pipeline Orchestration | `src/pipelines/phase1.py` & `src/pipelines/corruption_flow.py` | Settings & local snapshots | Entrypoints chạy thử nghiệm end-to-end cho Pha 1 (Baseline) và Pha 2 (Corruption/Repair) | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| Khắc phục lỗi kiểu dữ liệu Metadata khi nạp ChromaDB | Role 2 (Long - RAG Indexing) | Chuyển đổi cột `published` kiểu Timestamp và lọc bỏ các giá trị `NaN` sang chuỗi trong `index.py` để tránh crash cơ sở dữ liệu Vector. |
| Bàn giao chỉ số chất lượng & nhật ký gây lỗi | Role 3 (Dương - Reporting) | Ghi nhận file `corruption_log.json` và cấu hình thông số `source_summary` giúp module báo cáo so sánh tự động vẽ bảng delta. |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Xây dựng module thu thập Crossref API | `src/ingestion/crossref.py` | Snapshot thô `data/raw/crossref_records.json` | `cat data/raw/crossref_records.json` |
| Triển khai logic chuẩn hóa dữ liệu | `src/ingestion/cleaning.py` | File dữ liệu sạch `data/clean/papers_clean.csv` | `cat data/clean/papers_clean.csv` |
| Thiết lập bộ giả lập lỗi dữ liệu | `src/ingestion/corruption.py` | Dữ liệu lỗi `papers_clean_corrupted.csv` | `cat data/results/corruption_log.json` |
| Viết kịch bản điều phối Baseline Pha 1 | `src/pipelines/phase1.py` | Chạy toàn bộ Pha 1 chỉ với 1 dòng lệnh | `python script/run_phase1.py` |
| Viết kịch bản điều phối So sánh Pha 2 | `src/pipelines/corruption_flow.py` | Chạy toàn bộ Pha 2 và khôi phục tự động | `python script/run_corruption_flow.py` |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

File [papers_clean.csv](file:///Users/hoangquan/Desktop/K4_Day10_Data-Pipeline-Data-Observability_C53/data/clean/papers_clean.csv) chứa đúng **24 dòng dữ liệu sạch** được chuẩn hóa nghiêm ngặt theo Clean Contract (16 cột), loại bỏ hoàn toàn trùng lặp, chuẩn hóa các trường văn bản, và bảo đảm cột ghép `text_for_embedding` không bị rỗng ở bất kỳ dòng nào.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Xây dựng hệ thống Data Ingestion & Cleaning tự động tải các tài liệu học thuật từ API Crossref, chuẩn hóa cấu trúc dữ liệu theo data contract 16 cột nghiêm ngặt, xử lý loại bỏ trùng lặp và tính toán độ tuổi dữ liệu (`age_days`). Đồng thời thiết lập kịch bản giả lập lỗi dữ liệu có chủ đích (Corruption) để kiểm thử khả năng chống chịu của RAG Agent, viết kịch bản khôi phục tự động (Repair) từ tệp thô cục bộ, và điều phối toàn bộ quy trình chạy thử nghiệm Pha 1 & Pha 2.

### Cách triển khai

1.  **Data Ingestion (`crossref.py`):** Gửi yêu cầu HTTP GET đến Crossref API, áp dụng cơ chế tự động thử lại (Retry với exponential backoff) khi dính rate limit. Parse các trường dữ liệu thô (DOI, authors, published date, categories, abstract) thành cấu trúc `PaperRecord`.
2.  **Data Cleaning (`cleaning.py`):** Thiết lập Clean Contract 16 cột: tạo mã `paper_id` duy nhất dạng stable slug từ DOI, loại trùng lặp theo stable ID, dọn dẹp các thẻ XML/HTML thừa trong tóm tắt, tính toán thời gian xuất bản so với thời điểm chạy để xác định số ngày tuổi `age_days`, gộp tác giả và danh mục thành chuỗi phân tách bởi dấu phẩy, và ghép cột `text_for_embedding`.
3.  **Data Corruption (`corruption.py`):** Sao chép DataFrame sạch ban đầu, thực hiện gây lỗi có chủ đích trên từng nhóm dòng cụ thể (Latest Drop xóa bài viết mới nhất, Blank Summary xóa tóm tắt, Noise Injection chèn nhiễu, Title Truncation cắt ngắn tiêu đề, Old Date làm cũ ngày xuất bản, Duplicate Rows nhân bản dòng). Sau đó rebuild lại cột embedding để cập nhật lỗi.
4.  **Pipeline Orchestration:** Tích hợp các bước xử lý dữ liệu với module Chroma Indexing & Evaluator của Role 2, Quality Gates của Role 3 để tạo thành các entrypoints điều phối Pha 1 (`phase1.py`) và Pha 2 (`corruption_flow.py`) chạy tự động hoàn toàn.

### Input, output và contract

| Thành phần | Mô tả |
| ------------------------------ | ------------------------------------------- |
| Input | Crossref REST API, local raw snapshot, baseline clean CSV/JSON |
| Output | Raw JSON, cleaned CSV/JSON, corrupted CSV/JSON, repaired CSV/JSON, `corruption_log.json` |
| Module phụ thuộc | Core Settings (`config.py`), local embedding index (`index.py`) |
| Module sử dụng output | Vector Indexing & RAG Retrieval (`qa.py`) để nạp dữ liệu, Quality Gates để kiểm định |
| Điều kiện lỗi cần xử lý | Lỗi mạng/timeout khi gọi API, rate limit (429), khuyết thiếu trường dữ liệu trong API response, lỗi định dạng ngày không đồng nhất |

### Cách xác minh

```bash
python script/run_phase1.py
python script/run_corruption_flow.py
```

*   **Kết quả mong đợi:** Cả hai pipeline chạy hoàn thành thành công (exit code 0). Báo cáo so sánh được xuất ra Markdown khớp 100% với số liệu kiểm định và đánh giá RAG.
*   **Kết quả thực tế:** Hoàn thành xuất sắc, không còn lỗi crash.
*   **Artifact/log:** `data/raw/crossref_records.json`, `data/clean/papers_clean.csv`, `data/clean/papers_clean_corrupted.csv`, `data/clean/papers_clean_repaired.csv`, `data/results/corruption_log.json`.

## 5. Một quyết định kỹ thuật quan trọng

*   **Bối cảnh:** Khi nạp dữ liệu sạch vào ChromaDB ở Pha 1, hệ thống đã bị crash với lỗi `ValueError: Expected metadata value to be a str, int, float, bool... got Timestamp in add` tại hàm `LocalEmbeddingIndex.build`.
*   **Các phương án đã cân nhắc:**
    1.  *Phương án 1:* Sửa trực tiếp kiểu dữ liệu của cột ngày xuất bản `published` trong DataFrame thành dạng chuỗi (string) ở bước làm sạch dữ liệu (`cleaning.py`).
    2.  *Phương án 2:* Giữ nguyên kiểu dữ liệu Datetime/Timestamp của Pandas trong DataFrame, nhưng thực hiện kiểm tra và ép kiểu sang chuỗi `str` cho metadata trong hàm `_build_documents` của module Vector Index (`index.py`) trước khi nạp vào ChromaDB.
*   **Phương án đã chọn:** Phương án 2.
*   **Lý do:** DataFrame sạch cần giữ nguyên kiểu dữ liệu Datetime của cột `published` để phục vụ việc so sánh thời gian và tính toán số ngày tuổi `age_days` một cách tự động và chuẩn xác ở các module Observability kiểm định chất lượng dữ liệu (Quality Gates). Việc sửa đổi kiểu dữ liệu ở ranh giới giao tiếp với ChromaDB (phương án 2) giúp bảo vệ tính toàn vẹn của schema trong Data Pipeline.
*   **Bằng chứng quyết định phù hợp:** Sau khi áp dụng phương án 2, pipeline đã chạy thành công 100% không còn bị crash, nạp thành công cả 24 bản ghi vào ChromaDB và giữ nguyên được kiểu dữ liệu thời gian cho khâu kiểm định freshness.

## 6. Một lỗi hoặc blocker đã xử lý

*   **Triệu chứng/lỗi nguyên văn:**
    ```text
    TypeError: Invalid value for dtype 'str'. Value should be a string or missing value (or array of those).
    File "src/ingestion/corruption.py", line 40, in corrupt_clean_dataframe
      df_corrupt.iloc[6:8, df_corrupt.columns.get_loc("published")] = pd.to_datetime(...) - pd.Timedelta(...)
    ```
*   **Lệnh hoặc bước tái hiện:** Khởi chạy `python script/run_corruption_flow.py` trên terminal ở Pha 2.
*   **Nguyên nhân gốc:** Cột `published` trong cleaned dataframe thô khi đọc từ file CSV bằng `pd.read_csv()` được tự động gán kiểu chuỗi (string) bởi PyArrow/Pandas backend. Khi ta thực hiện trừ ngày xuất bản để gây lỗi ngày quá hạn, phép toán sinh ra đối tượng `Timestamp` của pandas. Khi gán trực tiếp đối tượng này vào cột chuỗi, PyArrow đã từ chối và báo lỗi loại kiểu dữ liệu không hợp lệ.
*   **Cách xử lý:** Chuyển đổi chuỗi ngày lùi 2 năm thành định dạng string YYYY-MM-DD bằng `.dt.strftime("%Y-%m-%d")` trước khi gán ngược lại cột `published`.
*   **Cách xác minh sau khi sửa:** Chạy lại `python script/run_corruption_flow.py`, pipeline chạy thành công hoàn chỉnh, ghi nhận đúng 2 dòng bị stale trong freshness report.
*   **Điều học được:** Luôn lưu ý sự khác biệt kiểu dữ liệu giữa dữ liệu trong bộ nhớ (In-memory DataFrame) và dữ liệu khi đọc từ tệp vật lý (CSV/JSON), đặc biệt là kiểu chuỗi của PyArrow.

## 7. Hiểu biết về luồng end-to-end

1.  **Dữ liệu đi từ Crossref đến vector index như thế nào?**
    Crossref REST API $\rightarrow$ Raw JSON snapshot (`crossref_records.json`) $\rightarrow$ Cleaning (`cleaning.py`, lọc trùng, chuẩn hóa schema, gộp text) $\rightarrow$ Clean DataFrame (`papers_clean.json`) $\rightarrow$ Embedding Generator (`MiniLMEmbeddings` mã hóa `text_for_embedding` thành vector 384 chiều) $\rightarrow$ ChromaDB Persistent Collection (`papers-baseline`).
2.  **Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?**
    `test_set.json` chứa từng câu hỏi kèm `ground_truth` (đáp án văn bản) và `ground_truth_doc_ids` (ID bài báo đúng). 
    - **Retrieval Quality:** Đo bằng `retrieval_hit` (kiểm tra `ground_truth_doc_ids` có thuộc Top-K `retrieved_doc_ids` không).
    - **Answer Quality:** Đo bằng `token_f1` (mức trùng lặp từ vựng) và `LLM Judge` (dùng LLM đọc prompt đối chiếu `answer` với `ground_truth` để chấm điểm 1-5 và tính `judge_accuracy`).
3.  **Quality checks khác freshness monitoring ở điểm nào trong bài lab?**
    - **Data Quality Checks (`quality.py`):** Kiểm tra tính toàn vẹn của dữ liệu tại một thời điểm (null IDs, duplicate IDs, missing titles, blank/short summaries).
    - **Freshness Monitoring (`quality.py`):** Kiểm tra yếu tố thời gian và độ mới của dữ liệu (tính toán `age_days` so với `run_date`, xác định số lượng bản ghi `stale` vượt ngưỡng cho phép).
4.  **Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?**
    Để đảm bảo **nguyên tắc kiểm soát biến (Controlled Experiment)**. Nếu dùng test set khác nhau giữa 3 môi trường, sự thay đổi của chỉ số có thể do câu hỏi dễ/khó hơn chứ không phản ánh đúng tác động của nhiễu dữ liệu (Corruption) hay hiệu quả của việc sửa lỗi (Repair).
5.  **Repair được xem là thành công dựa trên artifact và metric nào?**
    Repair thành công khi:
    - `repaired_quality.json` trả về `passed: true` (không còn null, duplicate, hay stale records).
    - `repaired_metrics.json` khôi phục chỉ số `retrieval_hit_rate`, `mean_token_f1`, `judge_accuracy` về mức bằng hoặc tương đương Baseline ($\Delta_{Repaired - Corrupted} > 0$, $\Delta_{Repaired - Baseline} \approx 0$).
    - Báo cáo so sánh `corruption_report.md` thể hiện các cột chỉ số phục hồi rõ ràng.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` | 100.00% | 40.00% | 100.00% | Nhiễu dữ liệu làm sụt giảm 60% khả năng tìm trúng bài báo của ChromaDB; Repair phục hồi 100%. |
| `mean_token_f1` | 100.00% | 35.93% | 100.00% | Khi retrieval bị trệch, AI lấy sai context làm trùng khớp từ vựng sụt giảm mạnh. |
| `judge_accuracy` | 100.00% | 33.33% | 100.00% | LLM Judge đánh giá chính xác sự suy giảm chất lượng câu trả lời khi thiếu context đúng. |
| `mean_judge_score` | 5.00 / 5.0 | 2.73 / 5.0 | 5.00 / 5.0 | Điểm chất lượng trung bình giảm từ 5.0 xuống 2.73 ở Corrupted và khôi phục về 5.0 ở Repaired. |
| Quality checks | Passed (0 errors) | Failed (3 dupes, 2 short sum, 2 stale) | Passed (0 errors) | Quality check phát hiện chính xác tất cả các lỗi do corruption flow bơm vào. |
| Freshness status | ✅ FRESH (0 stale) | ❌ STALE (2 stale) | ✅ FRESH (0 stale) | Freshness report ghi nhận đúng việc cũ hóa ngày xuất bản ở môi trường Corrupted. |

### Kết luận từ số liệu

1.  **[Data corruption]** (xóa tóm tắt, cũ hóa ngày, nhân bản dòng) $\rightarrow$ **[quality/freshness signal thay đổi]** (`duplicate_paper_ids: 3`, `stale_records: 2`, `passed: false`) $\rightarrow$ **[agent metric thay đổi]** (`hit_rate` giảm từ 100% xuống 40%, `judge_accuracy` giảm xuống 33.33%).
2.  **[Repair action]** (chạy lại cleaning pipeline từ snapshot `raw/crossref_records.json`) $\rightarrow$ **[quality/freshness signal phục hồi]** (`passed: true`, 0 duplicate, 0 stale) $\rightarrow$ **[agent metric phục hồi]** (`hit_rate`, `token_f1`, `judge_accuracy` đều phục hồi về 100.00%).

**Corruption nào ảnh hưởng rõ nhất và vì sao?**

Lỗi **xóa tóm tắt (blank/short summary)** và **drop bài báo** ảnh hưởng nặng nề nhất. Vì trong RAG, cột `text_for_embedding` chứa nội dung tóm tắt chính là dữ liệu để mã hóa vector. Khi tóm tắt bị rỗng hoặc bài báo bị drop, câu hỏi tìm kiếm ngữ nghĩa không thể tìm thấy thông tin tương đồng, dẫn đến Retrieval bị `MISS` kéo theo toàn bộ câu trả lời của AI bị sai.

**Kết quả nào khác với kỳ vọng ban đầu?**

Ban đầu khi chạy baseline, điểm `LLM Judge Accuracy` chỉ đạt 60% dù `Hit Rate` là 100%. Giả thuyết ban đầu là do LLM bịa đặt, nhưng qua kiểm tra phát hiện nguyên nhân thực sự là do `ground_truth` trong `test_set.json` lưu timestamp kiểu số (`1782777600000`) khác với dạng ngày ISO (`2026-06-30`) của AI. Sau khi chuẩn hóa `test_set.json`, điểm số đã đạt 100% đúng như kỳ vọng.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1.  **Về Data Pipeline:** Pipeline phải được thiết kế có tính **Idempotent (Tái lập)** và **Data Isolation (Cô lập dữ liệu)**. Việc tách riêng 3 collection (`papers-baseline`, `papers-corrupted`, `papers-repaired`) là chìa khóa để thử nghiệm nghiệm ngặt mà không làm hỏng dữ liệu gốc.
2.  **Về Data Quality & Observability:** Đánh giá RAG không thể chỉ nhìn vào câu trả lời cuối cùng của LLM. Cần phải đo lường ở từng tầng (Data Quality $\rightarrow$ Retrieval Hit Rate $\rightarrow$ Token F1 $\rightarrow$ LLM Judge) để biết chính xác điểm nghẽn nằm ở đâu.
3.  **Về Ảnh hưởng của Data đến RAG Agent:** "Garbage in, Garbage out" — chất lượng của RAG Agent phụ thuộc 90% vào độ sạch và độ tươi mới của dữ liệu trong Vector DB. Chỉ cần một vài bản ghi mất summary hay bị stale date là hiệu năng toàn hệ thống đã tụt dốc thảm hại.

### Nếu có thêm thời gian

Nếu có thêm thời gian, tôi sẽ nghiên cứu tích hợp hoàn chỉnh công cụ **dbt (data build tool)** kết hợp với các quy tắc kiểm định chất lượng tự động của **Great Expectations** để tự động hóa hoàn toàn các chốt chặn chất lượng dữ liệu (Quality Gates) ở từng bước trong pipeline, thay vì viết code check thủ công bằng pandas.

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Hoàng Xuân Quân  
**Ngày xác nhận:** 2026-08-06
