from __future__ import annotations

import json
from pathlib import Path
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
    from datetime import datetime, UTC

    # 1. Check row count
    row_count = len(df)

    # 2. Check paper_id not null and unique
    null_paper_ids = int(df["paper_id"].isna().sum()) if "paper_id" in df.columns else 0
    duplicate_paper_ids = int(df.duplicated(subset=["paper_id"]).sum()) if "paper_id" in df.columns else 0

    # 3. Check title not null/empty
    null_titles = int(df["title"].isna().sum() + (df["title"].astype(str).str.strip() == "").sum()) if "title" in df.columns else 0

    # 4. Check do dai summary
    null_summaries = int(df["summary"].isna().sum() + (df["summary"].astype(str).str.strip() == "").sum()) if "summary" in df.columns else 0
    short_summaries = int((df["summary"].astype(str).str.strip().str.len() < 50).sum()) if "summary" in df.columns else 0

    # 5. Check freshness bằng age_days
    stale_records = int((df["age_days"] > settings.freshness_threshold_days).sum()) if "age_days" in df.columns else 0

    passed = (
        null_paper_ids == 0 and 
        duplicate_paper_ids == 0 and 
        null_titles == 0 and 
        null_summaries == 0
    )

    report = {
        "report_name": report_name,
        "total_records": row_count,
        "null_paper_ids": null_paper_ids,
        "duplicate_paper_ids": duplicate_paper_ids,
        "missing_titles": null_titles,
        "missing_summaries": null_summaries,
        "short_summaries": short_summaries,
        "stale_records": stale_records,
        "passed": passed,
        "source_timestamp": datetime.now(UTC).isoformat()
    }

    # 6. Ghi ket qua vao data/quality/
    quality_dir = Path(settings.paths.quality_dir)
    quality_dir.mkdir(parents=True, exist_ok=True)
    report_file = quality_dir / f"{report_name}.json"
    
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4, ensure_ascii=False)

    return report


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
    if len(df) == 0:
        latest_pub = None
        oldest_pub = None
        stale_rows = 0
        total_rows = 0
        is_fresh = True
    else:
        # Convert published date to string format (since it is datetime object)
        latest_pub_val = df["published"].max()
        if pd.notna(latest_pub_val):
            # Check if it has strftime attribute (if it's pandas Timestamp/datetime)
            latest_pub = latest_pub_val.strftime("%Y-%m-%d") if hasattr(latest_pub_val, "strftime") else str(latest_pub_val)
        else:
            latest_pub = None

        oldest_pub_val = df["published"].min()
        if pd.notna(oldest_pub_val):
            oldest_pub = oldest_pub_val.strftime("%Y-%m-%d") if hasattr(oldest_pub_val, "strftime") else str(oldest_pub_val)
        else:
            oldest_pub = None

        # 2. Đếm số dòng stale
        stale_rows = int((df["age_days"] > settings.freshness_threshold_days).sum()) if "age_days" in df.columns else 0
        total_rows = len(df)
        is_fresh = bool(stale_rows == 0)

    # 3. Tạo payload
    report = {
        "latest_published": latest_pub,
        "oldest_published": oldest_pub,
        "stale_rows": stale_rows,
        "total_rows": total_rows,
        "is_fresh": is_fresh
    }

    # 4. Ghi JSON report
    report_file_path = Path(report_path)
    report_file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_file_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4, ensure_ascii=False)

    return report
