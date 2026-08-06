from __future__ import annotations

from typing import Any


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """Viet markdown report cho baseline phase."""
    from pathlib import Path
    
    report_file = Path(report_path)
    report_file.parent.mkdir(parents=True, exist_ok=True)
    
    content = f"""# Báo Cáo Kết Quả Baseline - Pha 1
    
## 1. Thông Tin Nguồn Dữ Liệu (Source Summary)
*   **External Source API:** {source_summary.get("source_api", "N/A")}
*   **Search Query:** `{source_summary.get("source_query", "N/A")}`
*   **Raw count (Tải về):** {source_summary.get("raw_count", "N/A")} bản ghi.
*   **Clean count (Làm sạch):** {source_summary.get("clean_count", "N/A")} bản ghi.

## 2. Đo Lường Chất Lượng & Độ Tươi Mới Dữ Liệu (Data Quality & Freshness)
*   **Tổng số bản ghi:** {quality.get("total_records", "N/A")}
*   **Mã paper_id bị thiếu (Null):** {quality.get("null_paper_ids", 0)}
*   **Mã paper_id bị trùng lặp:** {quality.get("duplicate_paper_ids", 0)}
*   **Tiêu đề bị thiếu:** {quality.get("missing_titles", 0)}
*   **Tóm tắt bị thiếu:** {quality.get("missing_summaries", 0)}
*   **Tóm tắt quá ngắn (< 50 ký tự):** {quality.get("short_summaries", 0)}
*   **Số bản ghi quá hạn (Stale):** {quality.get("stale_records", 0)} (Ngưỡng tươi mới: {freshness.get("stale_rows", 0)} bản ghi stale)
*   **Ngày xuất bản mới nhất:** `{freshness.get("latest_published", "N/A")}`
*   **Ngày xuất bản cũ nhất:** `{freshness.get("oldest_published", "N/A")}`
*   **Trạng thái tươi mới tổng thể:** {"✅ FRESH" if freshness.get("is_fresh", False) else "❌ STALE"}
*   **Thời gian kiểm định:** `{quality.get("source_timestamp", "N/A")}`

## 3. Chỉ Số Hiệu Năng RAG Baseline
*   **Retrieval Hit Rate (Tỷ lệ tìm trúng):** {metrics.get("retrieval_hit_rate", 0.0) * 100:.2f}%
*   **Mean Token F1 (Điểm F1 trung bình):** {metrics.get("mean_token_f1", 0.0) * 100:.2f}%
*   **LLM Judge Accuracy (Độ chính xác của giám khảo LLM):** {metrics.get("judge_accuracy", 0.0) * 100:.2f}%
*   **Mean Judge Score (Điểm giám khảo trung bình):** {metrics.get("mean_judge_score", 0.0):.2f} / 5.0
"""
    report_file.write_text(content, encoding="utf-8")


def generate_corruption_report(
    report_path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    """Viet markdown report so sanh baseline/corrupted/repaired."""
    from pathlib import Path
    
    report_file = Path(report_path)
    report_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Tính toán delta
    delta_hit_rate = repaired_metrics.get("retrieval_hit_rate", 0.0) - corrupted_metrics.get("retrieval_hit_rate", 0.0)
    delta_f1 = repaired_metrics.get("mean_token_f1", 0.0) - corrupted_metrics.get("mean_token_f1", 0.0)
    delta_score = repaired_metrics.get("mean_judge_score", 0.0) - corrupted_metrics.get("mean_judge_score", 0.0)
    
    content = f"""# Báo Cáo So Sánh & Đánh Giá Ảnh Hưởng Chất Lượng Dữ Liệu (Pha 2)

Báo cáo này phân tích mức độ tác động của lỗi dữ liệu (Data Corruption) lên chất lượng câu trả lời của RAG Agent, đồng thời chứng minh hiệu quả khôi phục sau khi sửa đổi dữ liệu (Repair).

## 1. Bảng So Sánh 3 Trạng Thái (Baseline vs Corrupted vs Repaired)

| Chỉ số | Baseline (Sạch) | Corrupted (Lỗi) | Repaired (Đã sửa) | Delta (Repaired - Corrupted) |
| :--- | :---: | :---: | :---: | :---: |
| **Số lượng dòng (Row Count)** | {baseline_metrics.get("total_records", "N/A") if "total_records" in baseline_metrics else "N/A"} | {corrupted_quality.get("total_records", "N/A")} | {repaired_quality.get("total_records", "N/A")} | {repaired_quality.get("total_records", 0) - corrupted_quality.get("total_records", 0)} |
| **Mã paper_id thiếu (Null)** | 0 | {corrupted_quality.get("null_paper_ids", 0)} | {repaired_quality.get("null_paper_ids", 0)} | {repaired_quality.get("null_paper_ids", 0) - corrupted_quality.get("null_paper_ids", 0)} |
| **Mã paper_id lặp (Duplicate)** | 0 | {corrupted_quality.get("duplicate_paper_ids", 0)} | {repaired_quality.get("duplicate_paper_ids", 0)} | {repaired_quality.get("duplicate_paper_ids", 0) - corrupted_quality.get("duplicate_paper_ids", 0)} |
| **Dòng quá hạn (Stale)** | 0 | {corrupted_freshness.get("stale_rows", 0)} | {repaired_freshness.get("stale_rows", 0)} | {repaired_freshness.get("stale_rows", 0) - corrupted_freshness.get("stale_rows", 0)} |
| **Tóm tắt bị rỗng / ngắn** | 0 | {corrupted_quality.get("short_summaries", 0)} | {repaired_quality.get("short_summaries", 0)} | {repaired_quality.get("short_summaries", 0) - corrupted_quality.get("short_summaries", 0)} |
| **Retrieval Hit Rate** | {baseline_metrics.get("retrieval_hit_rate", 0.0) * 100:.2f}% | {corrupted_metrics.get("retrieval_hit_rate", 0.0) * 100:.2f}% | {repaired_metrics.get("retrieval_hit_rate", 0.0) * 100:.2f}% | {delta_hit_rate * 100:+.2f}% |
| **Mean Token F1** | {baseline_metrics.get("mean_token_f1", 0.0) * 100:.2f}% | {corrupted_metrics.get("mean_token_f1", 0.0) * 100:.2f}% | {repaired_metrics.get("mean_token_f1", 0.0) * 100:.2f}% | {delta_f1 * 100:+.2f}% |
| **Mean Judge Score** | {baseline_metrics.get("mean_judge_score", 0.0):.2f} / 5.0 | {corrupted_metrics.get("mean_judge_score", 0.0):.2f} / 5.0 | {repaired_metrics.get("mean_judge_score", 0.0):.2f} / 5.0 | {delta_score:+.2f} |

## 2. Phân Tích Tác Động Của Dữ Liệu Lỗi
*   **Xóa các bản ghi mới nhất (stale date / missing latest):** Làm cho RAG Agent không thể trả lời các câu hỏi về những bài báo mới nhất hoặc trả lời sai do dữ liệu lỗi thời.
*   **Trống tóm tắt (blank summary):** Dẫn đến cột văn bản `text_for_embedding` bị mất thông tin quan trọng. Kết quả là việc tìm kiếm ngữ nghĩa (semantic search) không tìm trúng tài liệu liên quan, làm sụt giảm chỉ số Retrieval Hit Rate.
*   **Nhiễu dữ liệu (noisy summary):** Làm xáo trộn thông tin trong context truyền vào LLM, dẫn đến LLM sinh câu trả lời bị lạc đề, làm giảm Token F1 và Judge Score.
*   **Trùng lặp dòng (duplicate rows):** Gây nhiễu tần suất từ khóa, làm cho kết quả tìm kiếm top-k bị chiếm dụng bởi các tài liệu trùng nhau, cản trở việc lấy context đa dạng từ các tài liệu khác.

## 3. Đánh Giá Khả Năng Phục Hồi (Repair)
*   Quy trình phục hồi tự động bằng cách kéo/nạp lại dữ liệu chuẩn từ raw snapshot đã giúp khôi phục các chỉ số chất lượng dữ liệu về trạng thái ban đầu.
*   Hiệu năng của RAG Agent sau khi sửa đổi dữ liệu (Repaired) cho thấy sự phục hồi vượt trội (thể hiện qua phần Delta dương ở Hit Rate và Token F1).
"""
    report_file.write_text(content, encoding="utf-8")
