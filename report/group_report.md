# Group Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Khóa/Lớp         | K4                         |
| Tên nhóm         | Nhóm 3                     |
| Repository         | https://github.com/lonhidol/K4_Day10_Data-Pipeline-Data-Observability_C53.git |
| Ngày hoàn thành | 2026-08-06                 |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | Hoàng Xuân Quân* | 2A202601868 | Data foundation & pipeline (Vai trò 1) | Ingestion, cleaning, repair, orchestration (`src/ingestion/crossref.py`, `src/ingestion/cleaning.py`, `src/ingestion/corruption.py`, `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py`) |
| 2 | Nguyễn Thành Long | 2A202601536 | RAG & evaluation (Vai trò 2) | Index, agent, test set, answers, metrics (`src/retrieval/embeddings.py`, `src/retrieval/index.py`, `src/retrieval/agent.py`, `src/retrieval/llm.py`, `src/retrieval/qa.py`, `src/evaluation/testset.py`, `src/evaluation/metrics.py`) |
| 3 | Đào Tùng Dương | 2A202601402 | Observability & reporting (Vai trò 3) | Quality, freshness, reports (`src/observability/quality.py`, `src/observability/reporting.py`, `data/reports/phase1_report.md`, `data/reports/corruption_report.md`) |

## 2. Tóm tắt kết quả

**Tóm tắt của nhóm:**

Nhóm đã hoàn thành toàn bộ luồng data pipeline từ thu thập dữ liệu (Crossref API), tiền xử lý, lưu trữ vector index (ChromaDB + MiniLM), đánh giá chất lượng và kiểm định RAG agent, đến thử nghiệm các kịch bản lỗi dữ liệu (Data Corruption) và khôi phục (Repair).
Baseline pipeline chạy thành công, tạo ra các artifact: raw API response, raw records JSON, cleaned CSV/JSON, ChromaDB collections, `test_set.json`, `baseline_metrics.json`, baseline answers, quality/freshness reports và `phase1_report.md`.
Khi chạy kịch bản lỗi dữ liệu, lỗi xóa tóm tắt (blank summary) và trùng lặp bản ghi (duplicate rows) ảnh hưởng rõ rệt nhất. Thiếu tóm tắt làm sụt giảm mạnh khả năng tìm kiếm ngữ nghĩa, khiến Retrieval Hit Rate từ 100% giảm còn 40%, Token F1 giảm còn 35.93% và LLM Judge Score giảm xuống 2.73/5.
Quy trình Repair khôi phục dữ liệu thô từ snapshot nguồn đáng tin cậy đã giúp sửa đổi toàn bộ các bản ghi lỗi, khôi phục chất lượng dữ liệu về 100% pass và đưa các chỉ số hiệu năng của RAG Agent trở lại 100% (Hit Rate 1.0, Token F1 1.0, Judge Score 5.0).
Giới hạn lớn nhất hiện tại là pipeline dựa vào một snapshot tĩnh thay vì cơ chế stream/CDC thời gian thực và việc repair yêu cầu chạy lại toàn bộ quy trình thay vì cập nhật từng phần (incremental updates).

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

Sơ đồ triển khai thực tế của nhóm:

```text
Crossref API
    -> raw response/raw records (data/raw/)
    -> cleaning và data modeling (data/clean/)
    -> embedding + ChromaDB index (data/embeddings/ và data/chroma/)
    -> evaluation baseline (data/results/baseline_answers.json)
    -> quality/freshness reports (data/quality/)
    -> corruption (data/clean/papers_clean_corrupted.json)
    -> re-index và re-evaluate (data/results/corrupted_answers.json)
    -> repair từ dữ liệu nguồn (data/clean/papers_clean_repaired.json)
    -> comparison report (data/reports/corruption_report.md)
```

### Trách nhiệm của từng khối

| Khối             | Input          | Xử lý chính             | Output/artifact          | Owner          |
| ----------------- | -------------- | -------------------------- | ------------------------ | -------------- |
| Ingestion         | Crossref API | Gửi request, retry/backoff khi gặp 429/503, parse thành PaperRecord | `data/raw/crossref_response.json`, `data/raw/crossref_records.json` | Hoàng Xuân Quân |
| Cleaning          | Raw records JSON | Chuẩn hóa tiêu đề & tóm tắt, parse ngày xuất bản, deduplicate, filter dữ liệu xấu, tính age_days và text_for_embedding | `data/clean/papers_clean.csv`, `data/clean/papers_clean.json` | Hoàng Xuân Quân |
| Embedding/index   | Cleaned dataset | Tạo embeddings dùng MiniLM, index tài liệu vào ChromaDB collection | `data/embeddings/papers_embeddings.json`, `data/chroma/` | Nguyễn Thành Long |
| Evaluation        | Cleaned dataset, Vector index | Tạo bộ câu hỏi kiểm định (test set), chạy RAG agent sinh answers, tính Hit Rate, Token F1 và chạy LLM Judge | `data/eval/test_set.json`, `data/results/baseline_metrics.json`, `data/results/baseline_answers.json` | Nguyễn Thành Long |
| Observability     | Cleaned/Corrupted/Repaired dataframes | Kiểm tra tính hoàn thiện (null check), tính độc nhất (duplicate check), tính hợp lệ (độ dài summary) và độ tươi mới (freshness) | `data/quality/*.json` | Đào Tùng Dương |
| Corruption/repair | Cleaned dataset, Raw snapshot | Giả lập lỗi dữ liệu (drop dòng mới, xóa/nhiễu summary, cắt tiêu đề, cũ ngày, lặp dòng); Khôi phục dữ liệu bằng cách clean lại từ snapshot thô chuẩn | `data/results/corruption_log.json`, `data/clean/*_corrupted.*`, `data/clean/*_repaired.*` | Hoàng Xuân Quân |
| Orchestration     | Config / CLI commands | Điều phối chạy toàn bộ pipeline tuần tự, đảm bảo tính nhất quán và báo cáo so sánh | `data/reports/phase1_report.md`, `data/reports/corruption_report.md` | Hoàng Xuân Quân |

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình             | Giá trị sử dụng |
| ---------------------------- | ------------------- |
| `LLM_PROVIDER`             | `openrouter`         |
| `LLM_MODEL`                | `google/gemini-2.5-flash`         |
| Embedding model              | `sentence-transformers/all-MiniLM-L6-v2`         |
| Số lượng Crossref records | `24`         |
| Retrieval `top_k`           | `4`         |
| Freshness threshold          | `180` (ngày)         |
| Random seed, nếu có        | `N/A`         |

### Lệnh cài đặt

```bash
uv sync
```

### Lệnh chạy

Baseline:

```bash
uv run python script/run_phase1.py
```

Corruption flow:

```bash
uv run python script/run_corruption_flow.py
```

### Kết quả tái hiện

| Lệnh             | Trạng thái                                    | Thời điểm chạy gần nhất | Bằng chứng                         |
| ----------------- | ----------------------------------------------- | ----------------------------- | ------------------------------------ |
| Baseline pipeline | Thành công | 2026-08-06T21:12:58Z | `data/results/baseline_metrics.json`, `data/reports/phase1_report.md` |
| Corruption flow   | Thành công | 2026-08-06T21:16:37Z | `data/results/corrupted_metrics.json`, `data/results/repaired_metrics.json`, `data/reports/corruption_report.md` |

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính                | Giá trị                             |
| --------------------------- | ------------------------------------- |
| Source                      | Crossref REST API (https://api.crossref.org/works) |
| Query/filter                | query: `agentic retrieval augmented generation large language model`, filter: `from-pub-date:<180_days_ago>,has-abstract:true` |
| Thời điểm lấy dữ liệu | 2026-08-06 |
| Số record nhận được    | 24 |
| Cơ chế retry/backoff      | Thử lại tối đa 3 lần; dừng luân phiên lũy thừa khi gặp 429 hoặc 503 |

### Raw và clean schema

| Trường        | Kiểu dữ liệu | Bắt buộc?  | Ý nghĩa   | Xử lý khi thiếu/sai |
| --------------- | --------------- | ------------ | ----------- | ---------------------- |
| `paper_id` | `string` | Có | Mã định danh duy nhất của bài báo (slugified DOI) | Bỏ qua record (raw parse) hoặc lọc bỏ nếu null/empty (cleaning) |
| `title` | `string` | Có | Tiêu đề bài báo | Bỏ qua/lọc bỏ nếu tiêu đề trống |
| `summary` | `string` | Có | Tóm tắt (abstract) của bài báo | Bỏ qua/lọc bỏ nếu tóm tắt ngắn hơn 30 ký tự hoặc trống |
| `authors` | `list[string]` | Không | Danh sách tác giả | Chuyển thành chuỗi rỗng / mặc định |
| `categories` | `list[string]` | Không | Chủ đề phân loại bài viết | Gán giá trị mặc định `['unknown']` |
| `published` | `datetime`/`str` | Có | Ngày xuất bản bài viết | Parse sang datetime, nếu lỗi chuyển thành ngày `1970-01-01` |
| `age_days` | `int` | Có | Số ngày tính từ lúc xuất bản | Tính tự động: `run_date - published` |
| `text_for_embedding` | `string` | Có | Văn bản tổng hợp đầy đủ dùng để tạo embedding vector | Tạo tự động ghép từ Title, Abstract, Authors và Categories |

### Quy tắc cleaning

| Quy tắc                                 | Quality dimension liên quan | Số record bị tác động | Cách xác minh      |
| ---------------------------------------- | ---------------------------- | -------------------------: | -------------------- |
| Lọc trùng lặp `paper_id` | Uniqueness | 0 | Đếm số lượng record trước và sau `drop_duplicates` trong pandas |
| Lọc `paper_id` rỗng | Completeness | 0 | `isna()` check và lọc chuỗi trống |
| Lọc tiêu đề trống | Completeness | 0 | `isna()` check và kiểm tra độ dài chuỗi sau normalize |
| Lọc tóm tắt quá ngắn (< 30 ký tự) | Validity | 0 | Đếm số ký tự `summary_chars < 30` |

Giải thích cách nhóm tạo `text_for_embedding`, document ID và `age_days`:

- `text_for_embedding`: Được ghép bằng chuỗi định dạng: `Title: {title}\nAbstract: {summary}\nAuthors: {authors_joined}\nCategories: {categories_joined}`. Cách ghép này giúp mô hình embedding thu nhận toàn bộ thông tin ngữ nghĩa từ các trường dữ liệu quan trọng nhất.
- `document ID` (ở đây là `paper_id`): Được tạo ra bằng cách chuẩn hóa mã DOI của bài báo thô qua hàm `safe_slug` (thay thế các ký tự đặc biệt như `/`, `.` bằng `-` và viết thường), tạo thành một slug duy nhất, ổn định và an toàn khi đặt tên tập tin hoặc khóa tìm kiếm.
- `age_days`: Được tính bằng hiệu số ngày giữa thời điểm chạy (`run_date` sau khi loại bỏ múi giờ) và ngày xuất bản (`published` của bài báo thô): `(run_date_naive - df["published"]).dt.days`.

## 6. Evaluation setup

| Thành phần                             | Cấu hình thực tế          |
| ---------------------------------------- | ----------------------------- |
| Số câu hỏi                            | `15`                 |
| Các `question_type`                    | `summary`, `authors`, `date`                  |
| Ground-truth document ID                 | `ground_truth_doc_ids` (chứa `paper_id` thật tương ứng trong cleaned data)     |
| Embedding model                          | `sentence-transformers/all-MiniLM-L6-v2`                  |
| Vector store/collection                  | ChromaDB (`papers-baseline` / `papers-corrupted` / `papers-repaired`)                 |
| Retrieval `top_k`                       | `4`                   |
| LLM provider/model                       | `openrouter` / `google/gemini-2.5-flash`                   |
| Test set dùng chung cho ba trạng thái | `data/eval/test_set.json` |

Giải thích vì sao test set được giữ nguyên khi đánh giá baseline, corrupted và repaired:

Test set cần được giữ nguyên tuyệt đối để đóng vai trò là một biến điều khiển (control variable) trong thiết kế thực nghiệm. Nếu test set thay đổi giữa các lượt chạy, sự thay đổi của các chỉ số hiệu năng RAG (Hit Rate, F1, Accuracy) có thể bị nhiễu do độ khó của câu hỏi khác nhau. Khi giữ cố định test set, mọi sự suy giảm hay phục hồi của chỉ số hiệu năng đều phản ánh chính xác tác động trực tiếp của chất lượng dữ liệu trong Vector Index lên khả năng tìm kiếm ngữ nghĩa và chất lượng câu trả lời của RAG Agent.

## 7. Kết quả baseline

### Artifact checklist

| Artifact                 | Đường dẫn thực tế                | Trạng thái | Ghi chú   |
| ------------------------ | -------------------------------------- | ------------ | ---------- |
| Raw response/records     | `data/raw/`                          | Có | Đầy đủ `crossref_response.json` và `crossref_records.json` |
| Cleaned dataset          | `data/clean/`                        | Có | Đầy đủ `papers_clean.csv` và `papers_clean.json` |
| Embedding manifest/index | `data/embeddings/`                   | Có | Tập tin `papers_embeddings.json` chứa vector |
| Evaluation set           | `data/eval/`                         | Có | Tập tin `test_set.json` gồm 15 câu hỏi |
| Baseline metrics         | `data/results/baseline_metrics.json` | Có | Lưu trữ kết quả đánh giá baseline |
| Quality/freshness        | `data/quality/`                      | Có | Gồm `baseline_quality.json` và `freshness_report.json` |
| Baseline report          | `data/reports/phase1_report.md`      | Có | Báo cáo chi tiết pha 1 |

### Baseline metrics

| Metric                 |       Giá trị | Diễn giải                             |
| ---------------------- | --------------: | --------------------------------------- |
| `retrieval_hit_rate` |     `1.0` | RAG Agent tìm kiếm ngữ nghĩa trúng 100% tài liệu nguồn chứa thông tin trả lời. |
| `mean_token_f1`      |     `1.0` | Câu trả lời của RAG trùng khớp hoàn hảo với Ground Truth (đạt điểm F1 tối đa do dữ liệu sạch). |
| `judge_accuracy`     |     `1.0` | LLM giám khảo đánh giá tất cả các câu trả lời đều chính xác hoàn toàn. |
| `mean_judge_score`   |     `5.0 / 5.0` | Điểm số tuyệt đối từ LLM giám khảo cho độ chính xác dữ kiện. |
| Ragas, nếu có        | `N/A` | Bị bỏ qua (skipped) để tối ưu thời gian chạy pipeline (Set RUN_RAGAS=1 để bật). |

## 8. Data quality và freshness

### Quality checks

| Check        | Quality dimension | Ngưỡng/kỳ vọng | Kết quả baseline      | Bằng chứng |
| ------------ | ----------------- | ------------------ | ----------------------- | ------------ |
| Null Paper ID | Completeness | Không có paper_id null (`== 0`) | Pass, 0 | `data/quality/baseline_quality.json` |
| Duplicate Paper ID | Uniqueness | Không trùng lặp paper_id (`== 0`) | Pass, 0 | `data/quality/baseline_quality.json` |
| Missing Titles | Completeness | Không trống tiêu đề (`== 0`) | Pass, 0 | `data/quality/baseline_quality.json` |
| Missing Summaries | Completeness | Không trống tóm tắt (`== 0`) | Pass, 0 | `data/quality/baseline_quality.json` |
| Short Summaries | Validity | Không có tóm tắt quá ngắn (< 50 ký tự) | Pass, 0 | `data/quality/baseline_quality.json` |
| Stale Records | Freshness | Tuổi đời bài báo <= 180 ngày | Pass, 0 | `data/quality/baseline_quality.json` |

### Freshness

| Thuộc tính               | Giá trị                           |
| -------------------------- | ----------------------------------- |
| Freshness được đo tại | `data/quality/freshness_report.json` |
| Timestamp mới nhất       | `2026-08-01`                         |
| Ngưỡng freshness         | `180` (ngày)                         |
| Trạng thái baseline      | `Fresh`               |
| Lý do                     | Toàn bộ 24 bài viết đều xuất bản từ `2026-02-12` đến `2026-08-01`. Không có bài viết nào có `age_days` vượt quá ngưỡng 180 ngày tại thời điểm chạy (stale_rows = 0). |

## 9. Corruption scenarios và repair

| Corruption         | Cách tạo | Record bị tác động | Quality signal kỳ vọng | Tác động thực tế | Cách repair   |
| ------------------ | ---------- | ---------------------: | ------------------------ | --------------------- | -------------- |
| Drop records mới nhất | Xóa 3 dòng đầu tiên của dataframe | 3 | Mất dữ liệu của các bài báo mới nhất | Retrieval Hit Rate cho các câu hỏi về bài báo này về 0, LLM trả lời sai | Nạp lại (reload) toàn bộ records từ file raw snapshot chuẩn. |
| Blank summary | Đặt tóm tắt rỗng (`""`) ở 2 dòng đầu tiên | 2 | `summary_chars` < 30, cột embedding mất nội dung ngữ nghĩa | `text_for_embedding` thiếu tóm tắt, search không trúng, giảm hit rate | Chạy lại quy trình cleaning chuẩn từ raw snapshot. |
| Noise injection | Thêm tiền tố `### CORRUPT_NOISE_123 ###` vào tóm tắt của 2 dòng tiếp theo | 2 | Chèn chuỗi rác vào context RAG, giảm chất lượng câu trả lời | Token F1 và Judge Score giảm, LLM Judge phát hiện nhiễu | Khôi phục dữ liệu gốc từ raw snapshot thô. |
| Title truncation | Giới hạn tiêu đề chỉ gồm 3 từ đầu tiên của 2 dòng tiếp theo | 2 | Làm hỏng thông tin tiêu đề, ảnh hưởng truy vấn exact match | RAG không tìm được tài liệu khi hỏi trực tiếp theo tên bài báo | Phục hồi lại tiêu đề gốc qua cleaning từ raw snapshot. |
| Stale date | Trừ ngày xuất bản đi 730 ngày (2 năm) | 2 | `age_days` tăng mạnh, vi phạm ngưỡng Freshness (180 ngày) | Báo cáo Freshness cảnh báo dữ liệu bị `Stale`, `stale_records = 2` | Parse lại ngày chuẩn từ dữ liệu gốc thô. |
| Duplicate rows | Nhân bản 3 dòng cuối cùng | 3 | Vi phạm tính độc nhất của ID bài báo, chiếm dụng vị trí top-k | `duplicate_paper_ids = 3`, báo cáo chất lượng không đạt (`passed: false`) | Áp dụng quy tắc `drop_duplicates` trong quá trình cleaning lại. |

Corruption log:

- Đường dẫn: `data/results/corruption_log.json`
- Trạng thái: Có
- Nhận xét: Log ghi nhận đầy đủ thông tin: tổng số bản ghi trước và sau khi phá hủy dữ liệu (24 records), phân loại cụ thể từng lỗi dữ liệu (latest_drop, blank_summary, noise_injection, title_truncation, stale_date, duplicate_rows) kèm theo số lượng và danh sách chi tiết các `paper_id` bị ảnh hưởng.

Giải thích cách repair đảm bảo dữ liệu được phục hồi từ nguồn đáng tin cậy thay vì chỉ che kết quả lỗi:

Quy trình Repair không sửa đổi thủ công các tập tin lỗi hay vá kết quả đầu ra của Agent. Thay vào đó, nó thiết lập lại trạng thái của hệ thống bằng cách truy nguyên lại nguồn gốc (Data Lineage), tải lại snapshot dữ liệu thô ban đầu `data/raw/crossref_records.json` (được đảm bảo an toàn, không bị biến đổi trong suốt flow). Sau đó, pipeline chạy lại toàn bộ quy trình làm sạch (cleaning) theo đúng các quy tắc của Data Contract đã thống nhất. Điều này đảm bảo dữ liệu được khôi phục một cách tự động, khách quan, có tính tái lập cao và đúng nguyên lý hoạt động của các hệ thống xử lý dữ liệu lớn (ETL/ELT).

## 10. So sánh baseline, corrupted và repaired

| Metric/signal            | Baseline | Corrupted | Repaired | Thay đổi do corruption | Mức phục hồi | Nhận xét   |
| ------------------------ | -------: | --------: | -------: | -----------------------: | --------------: | ------------ |
| `retrieval_hit_rate`   | `100.00%` | `40.00%` | `100.00%` | `-60.00%` | `100.00%` | Retrieval sụt giảm nghiêm trọng do mất tóm tắt và thiếu hụt dữ liệu mới nhất. |
| `mean_token_f1`        | `100.00%` | `35.93%` | `100.00%` | `-64.07%` | `100.00%` | Chất lượng câu trả lời tệ đi rõ rệt do thiếu context chính xác hoặc context bị nhiễu. |
| `judge_accuracy`       | `100.00%` | `33.33%` | `100.00%` | `-66.67%` | `100.00%` | Giám khảo LLM đánh giá câu trả lời bị sai lệch/không đúng sự thật. |
| `mean_judge_score`     | `5.00` | `2.73` | `5.00` | `-2.27` | `+2.27` | Điểm chất lượng trung bình giảm gần một nửa. |
| Quality checks pass/fail | `Pass` | `Fail` | `Pass` | `Fail` | `Pass` | Phát hiện 3 bản ghi trùng lặp, 2 tóm tắt rỗng và 2 bài báo quá hạn. |
| Freshness status         | `Fresh` | `Stale` | `Fresh` | `Stale` | `Fresh` | Phát hiện 2 bản ghi bị cũ hóa ngày xuất bản vượt quá ngưỡng 180 ngày. |

Nêu ít nhất hai kết luận có quan hệ nhân quả được hỗ trợ bởi artifacts:

1. **[Xóa tóm tắt & drop bản ghi mới]** -> **[Giảm mạnh số lượng từ khoá ngữ nghĩa & mất tài liệu tham chiếu trong Index]** -> **[RAG Agent không truy xuất được context đúng (Hit Rate giảm từ 100% về 40%), dẫn đến LLM sinh câu trả lời sai lệch (Accuracy giảm về 33.33%)]**.
2. **[Khôi phục dữ liệu từ Raw Snapshot & Chạy lại Cleaning Rules]** -> **[Deduplicate hoàn toàn, phục hồi tóm tắt và ngày xuất bản chuẩn (Data Quality và Freshness đạt trạng thái Pass và Fresh)]** -> **[Cung cấp đầy đủ và chính xác context cho RAG Agent (Hit Rate, Token F1 và Judge Score khôi phục lại 100% như ban đầu)]**.

## 11. Vấn đề tích hợp quan trọng

Mô tả một vấn đề phát sinh khi ghép các module trong pipeline và cách nhóm xử lý:

- **Triệu chứng:** Khi chạy baseline pipeline lần đầu, RAG Agent không thể truy vấn hoặc trả về kết quả rỗng (empty retrieval) cho một số paper cụ thể mặc dù dữ liệu thô có tồn tại.
- **Nguyên nhân:** Có sự bất nhất về định dạng mã định danh bài viết giữa các module. Module Ingestion tạo `paper_id` từ DOI bằng cách giữ nguyên các ký tự `/` và `.`, trong khi module Cleaning và Vector Store lại slugify DOI (thay đổi thành dấu `-` và viết thường) để làm ID lưu trữ. Sự lệch pha này khiến Retrieval exact match tìm kiếm theo `paper_id` thô bị thất bại.
- **Cách xử lý:** Thống nhất contract: module Ingestion sử dụng hàm `safe_slug` để tạo `paper_id` ngay từ bước phân tích (parsing) dữ liệu thô. Tất cả các module Cleaning, Vector Index, Test Set Generation và RAG Agent sau đó đều truy xuất nhất quán qua `paper_id` đã được slugify này.
- **Cách xác minh:** Chạy `uv run python script/run_phase1.py` và kiểm tra file `data/eval/test_set.json` thấy các `ground_truth_doc_ids` trùng khớp hoàn toàn với cột `paper_id` trong `data/clean/papers_clean.csv`. Chạy smoke test agent thành công.

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại | Ảnh hưởng   | Hướng cải thiện có thể kiểm chứng |
| --------------------- | -------------- | ----------------------------------------- |
| Sử dụng snapshot dữ liệu tĩnh (tập tin JSON cục bộ) | Pipeline không tự động cập nhật khi có nghiên cứu mới xuất bản | Xây dựng module Ingestion theo cơ chế trigger/schedule hàng tuần gọi trực tiếp Crossref API để cập nhật dữ liệu mới. |
| Quy trình Repair tải lại và xử lý toàn bộ dữ liệu (Full ETL) | Tốn tài nguyên và thời gian chạy khi quy mô dữ liệu lớn | Áp dụng cơ chế Incrementally Loading & Processing: chỉ clean, embed và index những bản ghi mới hoặc có sự thay đổi (dựa vào trường updated). |

## 13. Checklist trước khi nộp

- [x] Thông tin nhóm và repository chính xác.
- [x] Phân công khớp với module, artifact và kết quả thực tế.
- [x] Lệnh tái hiện đã được chạy lại trên phiên bản dùng để nộp.
- [x] Baseline, corrupted và repaired dùng cùng evaluation set.
- [x] Bảng metrics khớp với các file trong `data/results/`.
- [x] Quality/freshness conclusions khớp với `data/quality/`.
- [x] Các đường dẫn báo cáo và artifact truy cập được.
- [x] Mỗi thành viên đã hoàn thành báo cáo vai trò riêng.
- [x] Không có `.env`, API key, token hoặc secret trong source, report, log hay ảnh.
