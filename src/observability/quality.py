from __future__ import annotations

from typing import Any

import pandas as pd

from core.config import Settings


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """TODO(student): tao bo data quality checks.

    Tín hiệu đo lường chất lượng dữ liệu (Định nghĩa Checkpoint 0):
    1. total_records: Số lượng dòng của dataframe (Row Count)
    2. missing_titles: Số dòng bị thiếu tiêu đề (Null check)
    3. missing_summaries: Số dòng bị thiếu tóm tắt (Null check)
    4. duplicate_paper_ids: Số bản ghi bị lặp paper_id (Duplicate check)
    5. source_timestamp: Thời điểm dữ liệu được fetch hoặc nạp (UTC ISO format)

    Pseudo-code:
    1. Check row count.
    2. Check `paper_id` not null va unique.
    3. Check `title` not null.
    4. Check do dai `summary`.
    5. Check freshness bang `age_days`.
    6. Ghi ket qua vao `data/quality/`.
    """
    raise NotImplementedError("Student task: implement quality checks.")


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    """TODO(student): tong hop freshness report.

    Tín hiệu đo lường độ tươi mới dữ liệu (Định nghĩa Checkpoint 0):
    1. latest_published: Ngày xuất bản mới nhất trong dữ liệu
    2. oldest_published: Ngày xuất bản cũ nhất trong dữ liệu
    3. stale_rows: Số dòng bị quá hạn (age_days > freshness_threshold_days)
    4. total_rows: Tổng số dòng dữ liệu
    5. is_fresh: Trạng thái tươi mới tổng thể (True nếu stale_rows == 0)

    Pseudo-code:
    1. Tim latest va oldest published date.
    2. Dem so dong stale.
    3. Tao payload:
       - latest_published
       - oldest_published
       - stale_rows
       - total_rows
       - is_fresh
    4. Ghi JSON report.
    """
    raise NotImplementedError("Student task: implement freshness reporting.")
