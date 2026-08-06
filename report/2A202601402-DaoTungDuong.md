# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Đào Tùng Dương     |
| MSSV               | 2A202601402          |
| Khóa/Lớp         | K4                         |
| Tên nhóm         | C53                        |
| Vai trò chính    | Observability, Data Quality & Reporting (Vai trò 3) |
| Repository         | https://github.com/lonhidol/K4_Day10_Data-Pipeline-Data-Observability_C53 |
| Ngày hoàn thành | 2026-08-06                 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Data Quality Monitoring | `src/observability/quality.py` -> `run_data_quality_checks` | `df` (pandas DataFrame), `Settings` config | `baseline_quality.json`, `corrupted_quality.json`, `repaired_quality.json` | Hoàn thành |
| Freshness Monitoring | `src/observability/quality.py` -> `build_freshness_report` | `df` (pandas DataFrame), `Settings` config, `report_path` | `freshness_report.json`, `corrupted_freshness.json`, `repaired_freshness.json` | Hoàn thành |
| Automated Reporting | `src/observability/reporting.py` -> `generate_phase1_report`, `generate_corruption_report` | Quality/Freshness reports & RAG metrics JSON | `data/reports/phase1_report.md`, `data/reports/corruption_report.md` | Hoàn thành |
| Group Report Coordination | `report/group_report.md` (đồng sở hữu) | Kết quả tổng hợp & phân công của nhóm 3 thành viên | Báo cáo nhóm hoàn chỉnh, loại bỏ toàn bộ placeholder | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| Tích hợp luồng Quality Gates vào pipeline | Role 1 (Quân) & Role 2 (Long) | Tích hợp thành công hàm kiểm tra chất lượng và độ tươi mới vào luồng chạy chính `phase1.py` và `corruption_flow.py`. |
| Phân tích tác động lỗi dữ liệu | Toàn nhóm | Đối chiếu các lỗi dữ liệu thô trong `corruption_log.json` với các cảnh báo thực tế được phát hiện trong `corrupted_quality.json`. |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Thiết lập các quy tắc Data Quality Checks | `src/observability/quality.py` -> `run_data_quality_checks` | Các file chất lượng `*_quality.json` cho 3 môi trường | `cat data/quality/baseline_quality.json` |
| Xây dựng cơ chế giám sát Freshness | `src/observability/quality.py` -> `build_freshness_report` | Các báo cáo độ tươi mới `*freshness.json` | `cat data/quality/freshness_report.json` |
| Tạo báo cáo Pha 1 (Baseline Report) | `src/observability/reporting.py` -> `generate_phase1_report` | File báo cáo `data/reports/phase1_report.md` | `cat data/reports/phase1_report.md` |
| Tạo báo cáo Pha 2 (Corruption/Repair Report) | `src/observability/reporting.py` -> `generate_corruption_report` | Báo cáo đối so sánh `data/reports/corruption_report.md` | `cat data/reports/corruption_report.md` |
| Hỗ trợ viết báo cáo chung của nhóm | `report/group_report.md` | Báo cáo nhóm hoàn chỉnh | `git diff report/group_report.md` |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

File `data/quality/corrupted_quality.json` và `data/quality/corrupted_freshness.json` chứng minh hệ thống giám sát đã bắt được chính xác 3 bản ghi trùng lặp (`duplicate_paper_ids: 3`), 2 bản ghi thiếu tóm tắt (`missing_summaries: 2`), 2 tóm tắt quá ngắn (`short_summaries: 2`) và 2 bản ghi bị cũ hóa vượt ngưỡng freshness (`stale_rows: 2`, `is_fresh: false`), làm tiền đề chứng minh sự sụt giảm hiệu năng của RAG Agent.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Thiết kế cơ chế Data Observability và Quality Gates cho data pipeline của RAG Agent. Cần định nghĩa các chiều đo lường chất lượng dữ liệu (Completeness, Uniqueness, Validity, Freshness), viết code tự động kiểm tra định dạng và độ mới của bài báo, lưu trữ báo cáo chất lượng định kỳ dưới dạng JSON, đồng thời tự động hóa việc xuất báo cáo so sánh kết quả dạng Markdown để chứng minh tác động nhân quả từ dữ liệu lỗi lên agent.

### Cách triển khai

1. **Data Quality Checks (`quality.py`):** Kiểm tra `paper_id` null và trùng lặp; lọc tiêu đề trống; đếm các tóm tắt bị rỗng hoặc quá ngắn (< 50 ký tự); đếm số lượng bản ghi stale có tuổi đời `age_days` vượt quá cấu hình `freshness_threshold_days`. Kết quả được lưu vào file JSON tương ứng của từng môi trường.
2. **Freshness Report (`quality.py`):** Tìm kiếm ngày xuất bản mới nhất (`latest_published`) và cũ nhất (`oldest_published`), đếm chính xác số lượng dòng stale để đưa ra cờ trạng thái `is_fresh` (chỉ bằng True khi số lượng dòng stale bằng 0).
3. **Automated Reporting (`reporting.py`):** Viết mã nguồn định dạng chuỗi mẫu (f-string) sinh báo cáo Pha 1 (`phase1_report.md`) và Pha 2 (`corruption_report.md`). Tính toán mức chênh lệch hiệu năng tự động (Delta: Repaired - Corrupted) cho Hit Rate, Token F1 và Judge Score để làm nổi bật tác động của việc sửa lỗi dữ liệu.

### Input, output và contract

| Thành phần | Mô tả |
| ------------------------------ | ------------------------------------------- |
| Input | Clean/Corrupted/Repaired dataframes, RAG metrics JSON, Settings config |
| Output | Quality JSON reports, Freshness JSON reports, Markdown reports |
| Module phụ thuộc | Data Ingestion/Cleaning (`cleaning.py`), RAG Metrics (`metrics.py`) |
| Module sử dụng output | Pipeline integration (`phase1.py`, `corruption_flow.py`) để gọi tạo báo cáo ở cuối luồng chạy |
| Điều kiện lỗi cần xử lý | Dataframe rỗng, trường `published` bị định dạng ngày không hợp lệ, không tạo được thư mục `data/quality` hoặc `data/reports` do lỗi phân quyền |

### Cách xác minh

```bash
uv run python script/run_phase1.py
uv run python script/run_corruption_flow.py
```

- **Kết quả mong đợi:** Các tệp JSON và Markdown được tạo ra đầy đủ, chính xác, khớp với số liệu trong dữ liệu CSV và kết quả đánh giá.
- **Kết quả thực tế:** Đạt 100% mong đợi.
- **Artifact/log:** `data/quality/baseline_quality.json`, `data/quality/corrupted_quality.json`, `data/quality/repaired_quality.json`, `data/reports/phase1_report.md`, `data/reports/corruption_report.md`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Khi định nghĩa cơ chế Freshness Monitoring, ngày chạy thực tế (`run_date`) ban đầu được định nghĩa bằng ngày hiện tại hệ thống (`datetime.now()`). Tuy nhiên, khi dữ liệu thô lấy từ Crossref có thể là dữ liệu học thuật cũ (từ vài tháng hoặc vài năm trước), việc so sánh với ngày chạy hiện tại khiến tất cả các bản ghi đều bị tính là stale (độ tuổi vượt quá 180 ngày), làm cho chỉ số Freshness của baseline luôn báo đỏ (`is_fresh: false`), gây nhiễu kết quả.
- **Các phương án đã cân nhắc:**
  1. *Phương án 1:* Hardcode ngày chạy lùi về quá khứ trùng với ngày xuất bản của bài báo mới nhất để làm baseline luôn xanh.
  2. *Phương án 2:* Cho phép cấu hình `run_date` truyền vào hàm `build_clean_dataframe` và tính toán `age_days` một cách động dựa trên thời điểm chạy được truyền từ Pipeline Orchestration, đồng thời thiết lập ngưỡng `freshness_threshold_days` rộng hơn (180 ngày) tương ứng với thời điểm lấy dữ liệu thô.
- **Phương án đã chọn:** Phương án 2.
- **Lý do:** Đảm bảo tính nhất quán và tự động hóa cao của pipeline. `run_date` được truyền thống nhất từ config chính, giúp tính toán đúng tuổi đời thực tế của bài viết tại thời điểm chạy cụ thể mà không làm sai lệch quy trình ETL.
- **Bằng chứng quyết định phù hợp:** Khi áp dụng phương án 2, chỉ số Freshness của Baseline đạt `is_fresh: true` (0 stale), trong khi ở môi trường Corrupted (bị trừ đi 730 ngày cho 2 bản ghi), hệ thống lập tức phát hiện chính xác `stale_rows: 2` và chuyển sang `is_fresh: false` một cách trung thực.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:**
  ```text
  AttributeError: 'str' object has no attribute 'strftime'
  File "src/observability/quality.py", line 112, in build_freshness_report
    latest_pub = latest_pub_val.strftime("%Y-%m-%d")
  ```
- **Lệnh hoặc bước tái hiện:** Chạy `uv run python script/run_phase1.py` sau khi tích hợp module Cleaning và Observability.
- **Nguyên nhân gốc:** Cột `published` trong cleaned dataframe thô sau khi đọc từ CSV bằng `pd.read_csv()` bị gán kiểu chuỗi (string) chứ không phải kiểu datetime object của pandas. Do đó, khi gọi hàm `max()` trên cột này, kết quả trả về là một `str` dẫn đến lỗi `AttributeError` khi cố gọi `.strftime()`.
- **Cách xử lý:** Thêm bước kiểm tra kiểu dữ liệu của giá trị max/min trước khi định dạng. Nếu giá trị trả về có thuộc tính `strftime`, tiến hành định dạng ngày; nếu là chuỗi văn bản thông thường, sử dụng hàm chuyển đổi hoặc ép kiểu `pd.to_datetime()` để đảm bảo an toàn.
- **Cách xác minh sau khi sửa:** Chạy lại `run_phase1.py`, script chạy thành công không gặp lỗi crash, xuất ra tệp `freshness_report.json` hoàn chỉnh.
- **Điều học được:** Kiểu dữ liệu khi ghi xuống tệp CSV/JSON và khi đọc lên thông qua pandas có thể bị biến đổi (từ Datetime về String). Luôn luôn phải kiểm tra kiểu dữ liệu (type validation) hoặc ép kiểu tường minh ở các ranh giới module (module boundaries) để tránh lỗi runtime.

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến vector index như thế nào?**
   Crossref REST API $\rightarrow$ Raw JSON snapshot (`crossref_records.json`) $\rightarrow$ Cleaning (`cleaning.py`, lọc trùng, chuẩn hóa schema, gộp text) $\rightarrow$ Clean DataFrame (`papers_clean.json`) $\rightarrow$ Embedding Generator (`MiniLMEmbeddings` mã hóa `text_for_embedding` thành vector 384 chiều) $\rightarrow$ ChromaDB Persistent Collection (`papers-baseline`).
2. **Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?**
   `test_set.json` chứa từng câu hỏi kèm `ground_truth` (đáp án văn bản) và `ground_truth_doc_ids` (ID bài báo đúng). 
   - **Retrieval Quality:** Đo bằng `retrieval_hit` (kiểm tra `ground_truth_doc_ids` có thuộc Top-K `retrieved_doc_ids` không).
   - **Answer Quality:** Đo bằng `token_f1` (mức trùng lặp từ vựng) và `LLM Judge` (dùng LLM đọc prompt đối chiếu `answer` với `ground_truth` để chấm điểm 1-5 và tính `judge_accuracy`).
3. **Quality checks khác freshness monitoring ở điểm nào trong bài lab?**
   - **Data Quality Checks (`quality.py`):** Kiểm tra tính toàn vẹn của dữ liệu tại một thời điểm (null IDs, duplicate IDs, missing titles, blank/short summaries).
   - **Freshness Monitoring (`quality.py`):** Kiểm tra yếu tố thời gian và độ mới của dữ liệu (tính toán `age_days` so với `run_date`, xác định số lượng bản ghi `stale` vượt ngưỡng cho phép).
4. **Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?**
   Để đảm bảo **nguyên tắc kiểm soát biến (Controlled Experiment)**. Nếu dùng test set khác nhau giữa 3 môi trường, sự thay đổi của chỉ số có thể do câu hỏi dễ/khó hơn chứ không phản ánh đúng tác động của nhiễu dữ liệu (Corruption) hay hiệu quả của việc sửa lỗi (Repair).
5. **Repair được xem là thành công dựa trên artifact và metric nào?**
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

1. **[Data corruption]** (xóa tóm tắt, cũ hóa ngày, nhân bản dòng) $\rightarrow$ **[quality/freshness signal thay đổi]** (`duplicate_paper_ids: 3`, `stale_records: 2`, `passed: false`) $\rightarrow$ **[agent metric thay đổi]** (`hit_rate` giảm từ 100% xuống 40%, `judge_accuracy` giảm xuống 33.33%).
2. **[Repair action]** (chạy lại cleaning pipeline từ snapshot `raw/crossref_records.json`) $\rightarrow$ **[quality/freshness signal phục hồi]** (`passed: true`, 0 duplicate, 0 stale) $\rightarrow$ **[agent metric phục hồi]** (`hit_rate`, `token_f1`, `judge_accuracy` đều phục hồi về 100.00%).

**Corruption nào ảnh hưởng rõ nhất và vì sao?**

Lỗi **xóa tóm tắt (blank/short summary)** và **drop bài báo** ảnh hưởng nặng nề nhất. Vì trong RAG, cột `text_for_embedding` chứa nội dung tóm tắt chính là dữ liệu để mã hóa vector. Khi tóm tắt bị rỗng hoặc bài báo bị drop, câu hỏi tìm kiếm ngữ nghĩa không thể tìm thấy thông tin tương đồng, dẫn đến Retrieval bị `MISS` kéo theo toàn bộ câu trả lời của AI bị sai.

**Kết quả nào khác với kỳ vọng ban đầu?**

Ban đầu khi chạy baseline, điểm `LLM Judge Accuracy` chỉ đạt 60% dù `Hit Rate` là 100%. Giả thuyết ban đầu là do LLM bịa đặt, nhưng qua kiểm tra phát hiện nguyên nhân thực sự là do `ground_truth` trong `test_set.json` lưu timestamp kiểu số (`1782777600000`) khác với dạng ngày ISO (`2026-06-30`) của AI. Sau khi chuẩn hóa `test_set.json`, điểm số đã đạt 100% đúng như kỳ vọng.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Về Data Pipeline:** Pipeline phải được thiết kế có tính **Idempotent (Tái lập)** và **Data Isolation (Cô lập dữ liệu)**. Việc tách riêng 3 collection (`papers-baseline`, `papers-corrupted`, `papers-repaired`) là chìa khóa để thử nghiệm nghiệm ngặt mà không làm hỏng dữ liệu gốc.
2. **Về Data Quality & Observability:** Đánh giá RAG không thể chỉ nhìn vào câu trả lời cuối cùng của LLM. Cần phải đo lường ở từng tầng (Data Quality $\rightarrow$ Retrieval Hit Rate $\rightarrow$ Token F1 $\rightarrow$ LLM Judge) để biết chính xác điểm nghẽn nằm ở đâu.
3. **Về Ảnh hưởng của Data đến RAG Agent:** "Garbage in, Garbage out" — chất lượng của RAG Agent phụ thuộc 90% vào độ sạch và độ tươi mới của dữ liệu trong Vector DB. Chỉ cần một vài bản ghi mất summary hay bị stale date là hiệu năng toàn hệ thống đã tụt dốc thảm hại.

### Nếu có thêm thời gian

Nếu có thêm thời gian, tôi sẽ nghiên cứu tích hợp hoàn chỉnh công cụ **Great Expectations** (đã có thư mục `gx` cấu hình sẵn) để tự động hóa các quy tắc kiểm định chất lượng dữ liệu thay vì viết code check thủ công bằng pandas, giúp nâng cao tính chuyên nghiệp của Quality Gates.

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Đào Tùng Dương  
**Ngày xác nhận:** 2026-08-06
