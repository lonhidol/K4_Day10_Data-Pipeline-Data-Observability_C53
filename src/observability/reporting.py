from __future__ import annotations

from typing import Any


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """TODO(student): viet markdown report cho baseline phase.

    Cấu trúc báo cáo Phase 1 (Thiết kế Checkpoint 0):
    1. Thông tin Nguồn dữ liệu (source_summary: API, Query, Raw count, Clean count).
    2. Chỉ số đo lường Chất lượng & Freshness (quality, freshness: null/duplicate errors, stale_rows).
    3. Kết quả Hiệu năng RAG Baseline (metrics: retrieval_hit_rate, mean_token_f1, accuracy).

    Pseudo-code:
    1. Gom source summary.
    2. In metrics retrieval/evaluation.
    3. In data quality va freshness.
    4. Ghi markdown vao report_path.
    """
    raise NotImplementedError("Student task: implement phase 1 report.")


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
    """TODO(student): viet markdown report so sanh baseline/corrupted/repaired.

    Cấu trúc báo cáo so sánh (Thiết kế Checkpoint 0):
    1. Bảng so sánh 3 trạng thái (Baseline vs Corrupted vs Repaired) của Row Count, Null/Missing, Duplicate, Stale Rows, Retrieval Hit Rate, Token F1, và Judge Accuracy.
    2. Phân tích cụ thể tác động của dữ liệu lỗi (blank/noisy summary) đối với hiệu năng RAG.
    3. Minh chứng thực tế qua các case study cụ thể (Hits & Misses của Agent).
    """
    raise NotImplementedError("Student task: implement corruption comparison report.")
