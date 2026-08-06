from __future__ import annotations

import pandas as pd


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path) -> pd.DataFrame:
    """Simulate nhieu dang data corruption."""
    from pathlib import Path
    from core.utils import write_json
    
    df_corrupt = df.copy()
    initial_count = len(df)
    
    # 1. Drop mot so latest records (Drop 3 dong dau tien)
    dropped_ids = df_corrupt.iloc[:3]["paper_id"].tolist() if len(df_corrupt) >= 3 else []
    df_corrupt = df_corrupt.iloc[len(dropped_ids):].copy()
    
    # 2. Blank summary o mot so dong (Đặt rỗng summary ở 2 dòng đầu tiên của DF mới)
    blank_ids = df_corrupt.iloc[:2]["paper_id"].tolist() if len(df_corrupt) >= 2 else []
    if blank_ids:
        df_corrupt.iloc[:len(blank_ids), df_corrupt.columns.get_loc("summary")] = ""
        
    # 3. Inject noise vao text (Thêm rác vào tóm tắt ở 2 dòng tiếp theo)
    noise_ids = df_corrupt.iloc[2:4]["paper_id"].tolist() if len(df_corrupt) >= 4 else []
    if noise_ids:
        df_corrupt.iloc[2:4, df_corrupt.columns.get_loc("summary")] = df_corrupt.iloc[2:4]["summary"].apply(
            lambda s: "### CORRUPT_NOISE_123 ### " + str(s)
        )
        
    # 4. Lam title bi truncate (Cắt ngắn tiêu đề ở 2 dòng tiếp theo)
    truncate_ids = df_corrupt.iloc[4:6]["paper_id"].tolist() if len(df_corrupt) >= 6 else []
    if truncate_ids:
        df_corrupt.iloc[4:6, df_corrupt.columns.get_loc("title")] = df_corrupt.iloc[4:6]["title"].apply(
            lambda t: " ".join(str(t).split()[:3])
        )
    # 5. Lam published date cu di (Trừ ngày đi 730 ngày ở 2 dòng tiếp theo)
    stale_ids = df_corrupt.iloc[6:8]["paper_id"].tolist() if len(df_corrupt) >= 8 else []
    if stale_ids:
        new_dates = (pd.to_datetime(df_corrupt.iloc[6:8]["published"]) - pd.Timedelta(days=730)).dt.strftime("%Y-%m-%d")
        df_corrupt.iloc[6:8, df_corrupt.columns.get_loc("published")] = new_dates
        df_corrupt.iloc[6:8, df_corrupt.columns.get_loc("age_days")] = df_corrupt.iloc[6:8]["age_days"] + 730

    # 6. Add duplicate rows (Nhân bản 3 dòng cuối cùng)
    dup_rows = df_corrupt.iloc[-3:].copy() if len(df_corrupt) >= 3 else pd.DataFrame()
    dup_ids = dup_rows["paper_id"].tolist() if not dup_rows.empty else []
    if not dup_rows.empty:
        df_corrupt = pd.concat([df_corrupt, dup_rows], ignore_index=True)
        
    # 7. Rebuild `text_for_embedding`
    df_corrupt["summary_chars"] = df_corrupt["summary"].astype(str).str.len()
    df_corrupt["text_for_embedding"] = df_corrupt.apply(
        lambda row: f"Title: {row['title']}\nAbstract: {row['summary']}\nAuthors: {row['authors_joined']}\nCategories: {row['categories_joined'] if pd.notna(row['categories_joined']) else ''}",
        axis=1
    )
    
    # 8. Ghi corruption log vao output_log_path
    log_payload = {
        "initial_count": initial_count,
        "final_count": len(df_corrupt),
        "latest_drop": {
            "count": len(dropped_ids),
            "paper_ids": dropped_ids
        },
        "blank_summary": {
            "count": len(blank_ids),
            "paper_ids": blank_ids
        },
        "noise_injection": {
            "count": len(noise_ids),
            "paper_ids": noise_ids
        },
        "title_truncation": {
            "count": len(truncate_ids),
            "paper_ids": truncate_ids
        },
        "stale_date": {
            "count": len(stale_ids),
            "paper_ids": stale_ids
        },
        "duplicate_rows": {
            "count": len(dup_ids),
            "paper_ids": dup_ids
        }
    }
    
    write_json(Path(output_log_path), log_payload)
    
    # In ra log
    print(f"[Corruption Log] Khởi động gây lỗi dữ liệu:")
    print(f"    * Drop {len(dropped_ids)} dòng mới nhất.")
    print(f"    * Xóa tóm tắt của {len(blank_ids)} dòng.")
    print(f"    * Bơm nhiễu vào tóm tắt {len(noise_ids)} dòng.")
    print(f"    * Cắt ngắn tiêu đề {len(truncate_ids)} dòng.")
    print(f"    * Cũ hóa ngày xuất bản {len(stale_ids)} dòng.")
    print(f"    * Nhân bản {len(dup_ids)} dòng.")
    print(f"    * Số lượng bản ghi thô: {initial_count} -> Lỗi: {len(df_corrupt)}")
    
    return df_corrupt
