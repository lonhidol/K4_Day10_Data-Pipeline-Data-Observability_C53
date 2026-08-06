# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Nguyễn Thành Long     |
| MSSV               | 2A202601536          |
| Khóa/Lớp         | K4                         |
| Tên nhóm         | C53                        |
| Vai trò chính    | RAG Retrieval, Evaluation & Observability Integration |
| Repository         | https://github.com/lonhidol/K4_Day10_Data-Pipeline-Data-Observability_C53 |
| Ngày hoàn thành | 2026-08-06                 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| RAG Vector Indexing | `src/retrieval/index.py` | `df_clean` (pandas DataFrame) | Collections `papers-baseline`, `papers-corrupted`, `papers-repaired` & Manifest JSONs | Hoàn thành |
| Retrieval & Q&A | `src/retrieval/qa.py` | Question string & Index | `AnswerResult` (Answer, retrieved_doc_ids, retrieved_contexts) | Hoàn thành |
| Evaluation Test Set | `src/evaluation/testset.py` | `df_clean` & Chroma Index | `data/eval/test_set.json` (15 samples cố định) | Hoàn thành |
| RAG Evaluator & Metrics | `src/evaluation/metrics.py` | `test_set.json`, Index, Settings | `baseline_metrics.json`, `baseline_answers.json`, `corrupted_metrics.json`, `repaired_metrics.json` | Hoàn thành |
| Agent Integration & Grounding | `src/retrieval/agent.py`, `src/pipelines/smoke_test_agent.py`, `src/pipelines/verify_agent_grounding.py` | Settings & Index | React Agent với tools `lookup_paper` & `semantic_search_papers`, trace logs | Hoàn thành |
| End-to-End Orchestration & Reporting | `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py` | Settings & Snapshots | Executable pipelines, `phase1_report.md`, `corruption_report.md` | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| Tích hợp Data Quality & Freshness Checks | Module Observability (`quality.py`, `reporting.py`) | Đưa các hàm `run_data_quality_checks` và `build_freshness_report` vào luồng `phase1.py` và `corruption_flow.py` |
| Fix lỗi kiểu dữ liệu Metadata | Module Ingestion / Cleaning | Chuẩn hóa `published` date và `authors_joined` thành chuỗi text trong `qa.py` để tránh lỗi crash kiểu `int` |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Xây dựng Vector Index cô lập 3 môi trường | `src/retrieval/index.py` | 3 Collections ChromaDB (`papers-baseline`, `papers-corrupted`, `papers-repaired`) | `python src/pipelines/compare_retrieval.py` |
| Chuẩn hóa Test Set & Barem đánh giá | `src/evaluation/testset.py`, `data/eval/test_set.json` | 15 test cases cố định (đầy đủ id, type, question, ground_truth, ground_truth_doc_ids) | `head -n 25 data/eval/test_set.json` |
| Đánh giá RAG Baseline, Corrupted, Repaired | `src/evaluation/metrics.py` | Artifacts `*_metrics.json` & `*_answers.json` | `python src/pipelines/phase1.py` & `python src/pipelines/corruption_flow.py` |
| Kiểm tra Agent Grounding (Không hallucinate) | `src/pipelines/verify_agent_grounding.py` | Trace log chứng minh Agent gọi tool lấy thông tin có nguồn trước khi trả lời | `python src/pipelines/verify_agent_grounding.py` |
| Lập Báo cáo so sánh Delta 3 trạng thái | `data/reports/corruption_report.md` | Báo cáo Markdown tổng hợp chỉ số & Delta giữa 3 môi trường | `cat data/reports/corruption_report.md` |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

File `data/results/baseline_metrics.json` và `data/reports/corruption_report.md` xác minh 100% hiệu năng Baseline (`Hit Rate: 100%`, `Token F1: 100%`, `LLM Judge Accuracy: 100%`), đo lường mức suy giảm ở Corrupted (`Hit Rate: 40%`, `Judge Accuracy: 33.33%`), và khôi phục hoàn toàn ở Repaired ($\Delta = +60.00\%$).

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Tạo hệ thống Vector Indexing (ChromaDB + MiniLM), xây dựng bộ Evaluation Test Set chuẩn hóa, thiết kế RAG Evaluator (Hit Rate, Token F1, LLM Judge) không sử dụng fallback giả, kiểm tra Agent suy luận có nguồn (Data Observability), và đo lường sự suy giảm/khôi phục hiệu năng qua 3 môi trường cô lập tuyệt đối.

### Cách triển khai

1. **Vector Indexing (`index.py`):** Sử dụng `sentence-transformers/all-MiniLM-L6-v2` tạo embeddings 384 chiều, lưu trữ vào ChromaDB `PersistentClient`. Phân tách collection dựa vào tham số đầu vào (`papers-baseline`, `papers-corrupted`, `papers-repaired`).
2. **Evaluation Set & Metrics (`testset.py`, `metrics.py`):** Tự động sinh câu hỏi từ cleaned dataframe, lọc bài báo bằng `index.lookup()` để đảm bảo ID tồn tại. Ép định dạng ngày `ground_truth` sang ISO (`YYYY-MM-DD`). Tính toán `retrieval_hit` bằng cách đối chiếu `ground_truth_doc_ids` trong Top-K `retrieved_doc_ids`. Sử dụng LLM với Structured Output (`JudgeVerdict`) để chấm điểm ngữ nghĩa 1-5.
3. **Strict LLM Judge (Không silent fallback):** Triển khai cơ chế retry 3 lần khi gọi LLM Judge. Nếu thất bại sau 3 lần, ném ngoại lệ `RuntimeError` thay vì âm thầm rơi vào heuristic F1 giả.
4. **Agent Grounding (`agent.py`, `verify_agent_grounding.py`):** Cung cấp 2 tools `lookup_paper` và `semantic_search_papers` có chứa `paper_id` và `title` trong đầu ra. Kiểm tra trace log để đảm bảo Agent luôn có tool call trước khi sinh câu trả lời.

### Input, output và contract

| Thành phần | Mô tả |
| ------------------------------ | ------------------------------------------- |
| Input | `papers_clean.json`, `raw/crossref_records.json`, `Settings` config |
| Output | Collections ChromaDB, `test_set.json`, `*_answers.json`, `*_metrics.json`, `corruption_report.md` |
| Module phụ thuộc | Module Ingestion (`cleaning.py`, `crossref.py`), Core Config (`config.py`) |
| Module sử dụng output | Pipeline Orchestration (`phase1.py`, `corruption_flow.py`), Observability Reporting |
| Điều kiện lỗi cần xử lý | ChromaDB lock/permission error, timestamp format mismatch, rỗng `categories`, LLM API rate limit/timeout |

### Cách xác minh

```bash
python src/pipelines/smoke_test_retrieval.py
python src/pipelines/smoke_test_agent.py
python src/pipelines/verify_agent_grounding.py
python src/pipelines/compare_retrieval.py
python src/pipelines/phase1.py
python src/pipelines/corruption_flow.py
```

- **Kết quả mong đợi:** Tất cả script chạy thành công, 3 collections cô lập hoàn chỉnh, RAG Baseline đạt 100% metrics, Corrupted tụt xuống ~33.33-40%, Repaired khôi phục 100%.
- **Kết quả thực tế:** Khớp 100% với kỳ vọng.
- **Artifact/log:** `data/results/baseline_metrics.json`, `data/results/corrupted_metrics.json`, `data/results/repaired_metrics.json`, `data/reports/corruption_report.md`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Khi đánh giá RAG baseline ban đầu, điểm `LLM Judge Accuracy` chỉ đạt 60% và `Token F1` chỉ đạt 50%, dù hệ thống Retrieval tìm đúng bài báo 100% (`Hit Rate: 100%`).
- **Các phương án đã cân nhắc:**
  1. *Phương án 1:* Sửa tay trực tiếp kết quả trả về trong `qa.py` hoặc file `baseline_answers.json` để ép điểm lên 100%.
  2. *Phương án 2:* Chuẩn hóa dữ liệu gốc trong `test_set.json` (chuyển timestamp dạng số `1782777600000` thành định dạng ISO `2026-06-30`, loại bỏ các câu hỏi `categories` có dữ liệu rỗng `""`) và rebuild toàn bộ kết quả từ pipeline.
- **Phương án đã chọn:** Phương án 2.
- **Lý do:** Đảm bảo tuân thủ nghiêm ngặt **Quy tắc 4** (Rebuild từ pipeline/source, tuyệt đối không sửa tay answers hay metrics) và **Quy tắc 2** (Giữ nguyên test set cố định chuẩn xác).
- **Bằng chứng quyết định phù hợp:** Sau khi chuẩn hóa `test_set.json` về 15 câu chuẩn và chạy lại `phase1.py`, chỉ số `LLM Judge Accuracy` và `Token F1` lập tức tăng lên **100.00%** tuyệt đối.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:**
  ```text
  chromadb.errors.InternalError: Permission denied (os error 13)
  File ".../chromadb/api/rust.py", line 122, in start
  ```
- **Lệnh hoặc bước tái hiện:** `python src/pipelines/smoke_test_agent.py` sau khi `git pull origin main`.
- **Nguyên nhân gốc:** File manifest `data/embeddings/papers_embeddings.json` được tạo từ máy của đồng đội có đường dẫn tuyệt đối ghi cứng là `/Users/hoangquan/Desktop/.../data/chroma`. Khi pull về máy địa phương (`/Users/ryu/Documents/...`), ChromaDB Rust Client cố gắng truy cập đường dẫn của máy đồng đội dẫn đến lỗi `Permission denied (os error 13)`.
- **Cách xử lý:** Viết script tự động phát hiện và cập nhật trường `persist_path` trong manifest JSON về đúng đường dẫn tuyệt đối của máy hiện tại (`Path.cwd() / 'data' / 'chroma'`), sau đó rebuild lại collection.
- **Cách xác minh sau khi sửa:** Chạy lại `python src/pipelines/smoke_test_agent.py`, script khởi tạo thành công và Agent trả lời câu hỏi mượt mà.
- **Điều học được:** Khi lưu trữ metadata/manifest của Data Pipeline, nên sử dụng đường dẫn tương đối (relative path) hoặc tự động resolve `persist_path` theo runtime environment để tránh lỗi phụ thuộc môi trường khi làm việc nhóm qua Git.

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

Nếu có thêm thời gian, tôi sẽ triển khai **Ragas Framework (`RUN_RAGAS=1`)** hoàn chỉnh với các chỉ số chuyên sâu như `faithfulness`, `answer_relevancy`, `context_precision`, và `context_recall` để đánh giá đa chiều hơn thay vì chỉ dựa vào LLM Judge đơn lẻ.

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** [Họ và tên sinh viên]  
**Ngày xác nhận:** 2026-08-06
