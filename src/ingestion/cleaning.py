from __future__ import annotations

from datetime import datetime

import pandas as pd

from ingestion.crossref import PaperRecord


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Clean raw records thanh dataframe san sang de embed."""
    from core.utils import normalize_whitespace
    
    # Định nghĩa cấu trúc cột mặc định
    columns = [
        "paper_id", "title", "summary", "authors", "categories", "primary_category",
        "published", "updated", "abs_url", "pdf_url", "comment", "age_days",
        "authors_joined", "categories_joined", "summary_chars", "text_for_embedding"
    ]
    
    if not records:
        return pd.DataFrame(columns=columns)
        
    data = []
    for r in records:
        data.append({
            "paper_id": r.paper_id,
            "title": r.title,
            "summary": r.summary,
            "authors": r.authors,
            "categories": r.categories,
            "primary_category": r.primary_category,
            "published": r.published,
            "updated": r.updated,
            "abs_url": r.abs_url,
            "pdf_url": r.pdf_url,
            "comment": r.comment
        })
        
    df = pd.DataFrame(data)
    
    # 1. Normalize title, summary
    df["title"] = df["title"].apply(lambda x: normalize_whitespace(str(x)))
    df["summary"] = df["summary"].apply(lambda x: normalize_whitespace(str(x)))
    
    # 2. Parse published/updated date
    df["published"] = pd.to_datetime(df["published"], errors="coerce")
    df["updated"] = pd.to_datetime(df["updated"], errors="coerce")
    
    # 3. Tinh age_days
    # Convert run_date sang timezone-naive de so sanh
    run_date_naive = run_date.replace(tzinfo=None)
    df["age_days"] = (run_date_naive - df["published"]).dt.days
    
    # 4. Tao cot helper
    df["authors_joined"] = df["authors"].apply(lambda x: ", ".join(x) if isinstance(x, list) else str(x))
    df["categories_joined"] = df["categories"].apply(lambda x: ", ".join(x) if isinstance(x, list) else str(x))
    df["summary_chars"] = df["summary"].str.len()
    df["text_for_embedding"] = df.apply(
        lambda row: f"Title: {row['title']}\nAbstract: {row['summary']}\nAuthors: {row['authors_joined']}\nCategories: {row['categories_joined']}",
        axis=1
    )
    
    # 5. Drop duplicates va filter row xau
    initial_count = len(df)
    
    # Lọc trùng lặp paper_id
    df_dedup = df.drop_duplicates(subset=["paper_id"], keep="first")
    dedup_removed = initial_count - len(df_dedup)
    
    # Lọc paper_id rỗng
    df_valid_id = df_dedup[df_dedup["paper_id"].notna() & (df_dedup["paper_id"].str.strip() != "")]
    id_removed = len(df_dedup) - len(df_valid_id)
    
    # Lọc tiêu đề rỗng
    df_valid_title = df_valid_id[df_valid_id["title"].notna() & (df_valid_id["title"].str.strip() != "")]
    title_removed = len(df_valid_id) - len(df_valid_title)
    
    # Lọc tóm tắt rỗng hoặc ngắn hơn 30 ký tự
    df_clean = df_valid_title[df_valid_title["summary"].notna() & (df_valid_title["summary_chars"] >= 30)]
    summary_removed = len(df_valid_title) - len(df_clean)
    
    # Ghi nhận logs
    print(f"[Cleaning Log] Bắt đầu làm sạch với {initial_count} bản ghi thô.")
    if dedup_removed > 0:
        print(f"[Cleaning Log] Đã lọc bỏ {dedup_removed} bản ghi trùng lặp paper_id.")
    if id_removed > 0:
        print(f"[Cleaning Log] Đã lọc bỏ {id_removed} bản ghi do thiếu paper_id.")
    if title_removed > 0:
        print(f"[Cleaning Log] Đã lọc bỏ {title_removed} bản ghi do tiêu đề rỗng.")
    if summary_removed > 0:
        print(f"[Cleaning Log] Đã lọc bỏ {summary_removed} bản ghi do tóm tắt rỗng hoặc quá ngắn (< 30 ký tự).")
    print(f"[Cleaning Log] Hoàn thành làm sạch, còn lại {len(df_clean)} bản ghi đạt chuẩn.")
    
    df = df_clean
    
    # 6. Sort dataframe va return
    df = df.sort_values(by="published", ascending=False)
    
    return df
