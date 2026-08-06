from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from core.utils import write_json, first_sentence


def build_test_set(df: pd.DataFrame, output_path: Path) -> list[dict[str, Any]]:
    """Xây dựng bộ evaluation set từ cleaned dataframe dựa trên dữ liệu thật."""
    
    # 1. Kiểm tra số lượng document tối thiểu
    if len(df) == 0:
        return []

    # 2. Chọn một số paper đại diện (lấy 5 paper đầu tiên làm mẫu)
    sampled_df = df.head(5)
    
    test_set = []
    question_counter = 1
    
    # 3. Tạo nhiều loại câu hỏi cho từng paper
    for _, row in sampled_df.iterrows():
        paper_id = str(row["paper_id"])
        title = str(row["title"])
        authors = str(row["authors_joined"])
        date = str(row["published"])
        categories = str(row["categories_joined"])
        summary = str(row["summary"])
        
        # Câu hỏi về summary (trích xuất câu đầu tiên để khớp với logic qa.py)
        test_set.append({
            "id": f"q{question_counter}",
            "question_type": "summary",
            "question": f"What is the summary of the paper '{title}'?",
            "ground_truth": first_sentence(summary),
            "ground_truth_doc_ids": [paper_id]
        })
        question_counter += 1
        
        # Câu hỏi về authors (dùng keyword "who authored")
        test_set.append({
            "id": f"q{question_counter}",
            "question_type": "authors",
            "question": f"Who authored the paper '{title}'?",
            "ground_truth": authors,
            "ground_truth_doc_ids": [paper_id]
        })
        question_counter += 1
        
        # Câu hỏi về date (dùng keyword "publication date")
        test_set.append({
            "id": f"q{question_counter}",
            "question_type": "date",
            "question": f"When was the publication date of the paper '{title}'?",
            "ground_truth": date,
            "ground_truth_doc_ids": [paper_id]
        })
        question_counter += 1
        
        # Câu hỏi về categories (dùng keyword "what categories")
        test_set.append({
            "id": f"q{question_counter}",
            "question_type": "categories",
            "question": f"What categories does the paper '{title}' belong to?",
            "ground_truth": categories,
            "ground_truth_doc_ids": [paper_id]
        })
        question_counter += 1
        
    # 5. Ghi file JSON vào output_path
    write_json(output_path, test_set)
    return test_set
