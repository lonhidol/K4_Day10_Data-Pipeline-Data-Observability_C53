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
    df = df.drop_duplicates(subset=["paper_id"], keep="first")
    df = df[df["paper_id"].notna() & (df["paper_id"].str.strip() != "")]
    df = df[df["title"].notna() & (df["title"].str.strip() != "")]
    df = df[df["summary"].notna() & (df["summary_chars"] >= 30)]
    
    # 6. Sort dataframe va return
    df = df.sort_values(by="published", ascending=False)
    
    return df
