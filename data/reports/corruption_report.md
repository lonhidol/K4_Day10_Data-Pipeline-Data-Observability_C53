# Báo Cáo So Sánh & Đánh Giá Ảnh Hưởng Chất Lượng Dữ Liệu (Pha 2)

Báo cáo này phân tích mức độ tác động của lỗi dữ liệu (Data Corruption) lên chất lượng câu trả lời của RAG Agent, đồng thời chứng minh hiệu quả khôi phục sau khi sửa đổi dữ liệu (Repair).

## 1. Bảng So Sánh 3 Trạng Thái (Baseline vs Corrupted vs Repaired)

| Chỉ số | Baseline (Sạch) | Corrupted (Lỗi) | Repaired (Đã sửa) | Delta (Repaired - Corrupted) |
| :--- | :---: | :---: | :---: | :---: |
| **Số lượng dòng (Row Count)** | N/A | 24 | 24 | 0 |
| **Mã paper_id thiếu (Null)** | 0 | 0 | 0 | 0 |
| **Mã paper_id lặp (Duplicate)** | 0 | 3 | 0 | -3 |
| **Dòng quá hạn (Stale)** | 0 | 2 | 0 | -2 |
| **Tóm tắt bị rỗng / ngắn** | 0 | 2 | 0 | -2 |
| **Retrieval Hit Rate** | 100.00% | 40.00% | 100.00% | +60.00% |
| **Mean Token F1** | 50.00% | 35.93% | 100.00% | +64.07% |
| **Mean Judge Score** | 3.40 / 5.0 | 2.73 / 5.0 | 5.00 / 5.0 | +2.27 |

## 2. Phân Tích Tác Động Của Dữ Liệu Lỗi
*   **Xóa các bản ghi mới nhất (stale date / missing latest):** Làm cho RAG Agent không thể trả lời các câu hỏi về những bài báo mới nhất hoặc trả lời sai do dữ liệu lỗi thời.
*   **Trống tóm tắt (blank summary):** Dẫn đến cột văn bản `text_for_embedding` bị mất thông tin quan trọng. Kết quả là việc tìm kiếm ngữ nghĩa (semantic search) không tìm trúng tài liệu liên quan, làm sụt giảm chỉ số Retrieval Hit Rate.
*   **Nhiễu dữ liệu (noisy summary):** Làm xáo trộn thông tin trong context truyền vào LLM, dẫn đến LLM sinh câu trả lời bị lạc đề, làm giảm Token F1 và Judge Score.
*   **Trùng lặp dòng (duplicate rows):** Gây nhiễu tần suất từ khóa, làm cho kết quả tìm kiếm top-k bị chiếm dụng bởi các tài liệu trùng nhau, cản trở việc lấy context đa dạng từ các tài liệu khác.

## 3. Đánh Giá Khả Năng Phục Hồi (Repair)
*   Quy trình phục hồi tự động bằng cách kéo/nạp lại dữ liệu chuẩn từ raw snapshot đã giúp khôi phục các chỉ số chất lượng dữ liệu về trạng thái ban đầu.
*   Hiệu năng của RAG Agent sau khi sửa đổi dữ liệu (Repaired) cho thấy sự phục hồi vượt trội (thể hiện qua phần Delta dương ở Hit Rate và Token F1).
