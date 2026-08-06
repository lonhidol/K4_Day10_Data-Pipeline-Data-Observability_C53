from __future__ import annotations

import json
import io
import sys
from pathlib import Path

# Force UTF-8 output encoding for Windows compatibility
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# Thêm src vào sys.path để chạy trực tiếp không bị lỗi import nếu chưa cài editable
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))

from core.config import load_settings


def print_section(title: str):
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "#"))
    print("=" * 60)


def analyze_corrupted_observability():
    print_section("AUDIT & VERIFICATION FOR ROLE 3 - CHECKPOINT 5")
    
    # 1. Load settings
    try:
        settings = load_settings()
        print("✅ Load settings thành công.")
    except Exception as e:
        print(f"❌ Lỗi khi load settings: {e}")
        return

    # 2. Paths
    baseline_quality_path = Path(settings.paths.quality_dir) / "baseline_quality.json"
    corrupted_quality_path = Path(settings.paths.quality_dir) / "corrupted_quality.json"
    
    baseline_metrics_path = Path(settings.paths.baseline_metrics)
    corrupted_metrics_path = Path(settings.paths.corrupted_metrics)
    
    # 3. Check if all required files exist
    missing_files = []
    for p, name in [
        (baseline_quality_path, "baseline_quality.json"),
        (corrupted_quality_path, "corrupted_quality.json"),
        (baseline_metrics_path, "baseline_metrics.json"),
        (corrupted_metrics_path, "corrupted_metrics.json")
    ]:
        if not p.exists():
            missing_files.append(name)
    
    if missing_files:
        print("\n⚠️ CHƯA ĐẦY ĐỦ PHÂN TÍCH: Một số file kết quả corrupted chưa tồn tại!")
        print(f"   Các file còn thiếu: {missing_files}")
        print("   Hãy chạy 'python script/run_corruption_flow.py' sau khi Vai trò 1 & 2 hoàn thành.")
        print("   Dưới đây là cấu trúc đối chiếu dự phòng sử dụng dữ liệu mẫu nếu có...")
        
    print("\n--- BẢNG ĐỐI CHIẾU THAY ĐỔI TÍN HIỆU (BASELINE VS CORRUPTED) ---")
    
    # Load baseline
    try:
        with open(baseline_quality_path, "r", encoding="utf-8") as f:
            b_qual = json.load(f)
        with open(baseline_metrics_path, "r", encoding="utf-8") as f:
            b_met = json.load(f)
    except Exception as e:
        print(f"❌ Lỗi khi đọc kết quả baseline: {e}")
        return
        
    # Load corrupted or use dummy/none
    c_qual = {}
    c_met = {}
    if corrupted_quality_path.exists():
        try:
            with open(corrupted_quality_path, "r", encoding="utf-8") as f:
                c_qual = json.load(f)
        except Exception as e:
            print(f"❌ Lỗi khi đọc corrupted quality: {e}")
    if corrupted_metrics_path.exists():
        try:
            with open(corrupted_metrics_path, "r", encoding="utf-8") as f:
                c_met = json.load(f)
        except Exception as e:
            print(f"❌ Lỗi khi đọc corrupted metrics: {e}")

    # Helper format values
    def fmt_val(d, key, is_pct=False, default="N/A"):
        val = d.get(key)
        if val is None:
            return default
        if is_pct:
            return f"{val * 100:.2f}%"
        if isinstance(val, float):
            return f"{val:.2f}"
        return str(val)

    def print_row(title, key, is_pct=False, d_type=int):
        b_val = b_qual.get(key) if key in b_qual else b_met.get(key)
        c_val = c_qual.get(key) if key in c_qual else c_met.get(key)
        
        b_str = fmt_val(b_qual if key in b_qual else b_met, key, is_pct)
        c_str = fmt_val(c_qual if key in c_qual else c_met, key, is_pct)
        
        delta_str = "N/A"
        if b_val is not None and c_val is not None:
            delta = c_val - b_val
            if is_pct:
                delta_str = f"{delta * 100:+.2f}%"
            elif isinstance(delta, float):
                delta_str = f"{delta:+.2f}"
            else:
                delta_str = f"{delta:+d}"
                
        print(f"{title:<35} | {b_str:>10} | {c_str:>10} | {delta_str:>12}")

    print(f"{'Chỉ số':<35} | {'Baseline':>10} | {'Corrupted':>10} | {'Thay đổi':>12}")
    print("-" * 75)
    print_row("Số lượng dòng (Row Count)", "total_records")
    print_row("Mã paper_id thiếu (Null)", "null_paper_ids")
    print_row("Mã paper_id lặp (Duplicate)", "duplicate_paper_ids")
    print_row("Tiêu đề bị thiếu (Null Title)", "missing_titles")
    print_row("Tóm tắt bị thiếu (Null Summary)", "missing_summaries")
    print_row("Tóm tắt quá ngắn (<50 ký tự)", "short_summaries")
    print_row("Bản ghi quá hạn (Stale Records)", "stale_records")
    
    print("-" * 75)
    print_row("Retrieval Hit Rate", "retrieval_hit_rate", is_pct=True)
    print_row("Mean Token F1", "mean_token_f1", is_pct=True)
    print_row("LLM Judge Accuracy", "judge_accuracy", is_pct=True)
    print_row("Mean Judge Score", "mean_judge_score")
    
    print("-" * 75)
    
    if c_qual and c_met:
        print("\n📈 PHÂN TÍCH TÁC ĐỘNG TỪ BẰNG CHỨNG THỰC TẾ:")
        
        # 1. Check for blank summary impact
        b_sum_missing = b_qual.get("missing_summaries", 0)
        c_sum_missing = c_qual.get("missing_summaries", 0)
        if c_sum_missing > b_sum_missing:
            print(f"👉 Phát hiện {c_sum_missing} tóm tắt bị thiếu (blank summary).")
            hit_delta = c_met.get("retrieval_hit_rate", 0.0) - b_met.get("retrieval_hit_rate", 0.0)
            print(f"   -> Ảnh hưởng RAG: Retrieval Hit Rate thay đổi {hit_delta*100:+.2f}%")
            
        # 2. Check for duplicate rows impact
        b_dup = b_qual.get("duplicate_paper_ids", 0)
        c_dup = c_qual.get("duplicate_paper_ids", 0)
        if c_dup > b_dup:
            print(f"👉 Phát hiện {c_dup} paper_id bị trùng lặp (duplicate paper_id).")
            print("   -> Ảnh hưởng RAG: Các tài liệu trùng lặp làm giảm đa dạng hóa context trong top-k.")
            
        # 3. Check for stale records impact
        b_stale = b_qual.get("stale_records", 0)
        c_stale = c_qual.get("stale_records", 0)
        if c_stale > b_stale:
            print(f"👉 Phát hiện {c_stale} bài báo cũ/quá hạn (stale publication).")
            print("   -> Ảnh hưởng RAG: LLM Agent không thể trả lời chính xác các câu hỏi mới nhất.")
            
        # 4. Signials that did not change
        unchanged = []
        for k in ["null_paper_ids", "missing_titles"]:
            if b_qual.get(k, 0) == c_qual.get(k, 0) == 0:
                unchanged.append(k)
        if unchanged:
            print(f"ℹ️ Tín hiệu chất lượng không đổi (luôn là 0): {unchanged}")
            
    print_section("KẾT THÚC PHÂN TÍCH CHECKPOINT 5")


if __name__ == "__main__":
    analyze_corrupted_observability()
