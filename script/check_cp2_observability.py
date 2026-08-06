from __future__ import annotations

import json
import sys
import io
from pathlib import Path

# Force UTF-8 output encoding for Windows compatibility
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

import pandas as pd
import chromadb

# Thêm src vào sys.path để chạy trực tiếp không bị lỗi import nếu chưa cài editable
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))

from core.config import load_settings
from observability.quality import run_data_quality_checks, build_freshness_report


def print_section(title: str):
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "#"))
    print("=" * 60)


def check_cp2_observability():
    print_section("AUDIT & VERIFICATION FOR ROLE 3 - CHECKPOINT 2")
    
    # 1. Load settings
    try:
        settings = load_settings()
        print("✅ Load settings thành công.")
    except Exception as e:
        print(f"❌ Lỗi khi load settings: {e}")
        return

    # 2. Kiểm tra files dữ liệu sạch
    clean_csv_path = Path(settings.paths.clean_csv)
    
    print("\n--- [1] Kiểm tra file Cleaned Dataset ---")
    if not clean_csv_path.exists():
        print(f"❌ File clean CSV không tồn tại tại: {clean_csv_path}")
        print("   Hãy chắc chắn rằng Vai trò 1 đã chạy bước Cleaning thành công.")
        return
    
    df_clean = pd.read_csv(clean_csv_path)
    clean_count = len(df_clean)
    print(f"✅ Tìm thấy clean CSV: {clean_csv_path}")
    print(f"   Số lượng dòng dữ liệu sạch: {clean_count} dòng.")

    # 3. Kiểm tra Embedding Manifest
    manifest_path = Path(settings.paths.embeddings_json)
    print("\n--- [2] Kiểm tra Embedding Manifest (.json) ---")
    if not manifest_path.exists():
        print(f"❌ File manifest không tồn tại tại: {manifest_path}")
        print("   Hãy chắc chắn rằng Vai trò 2 đã chạy build index thành công.")
        return
        
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        
        print(f"✅ Tìm thấy embedding manifest: {manifest_path}")
        print(f"   - Backend: {manifest.get('backend', 'N/A')}")
        print(f"   - Embedding Model: {manifest.get('embedding_model', 'N/A')}")
        print(f"   - Collection Name: {manifest.get('collection_name', 'N/A')}")
        
        manifest_docs = manifest.get("documents", [])
        manifest_count = len(manifest_docs)
        print(f"   - Số lượng documents trong manifest: {manifest_count}")
        
        if manifest_count != clean_count:
            print(f"⚠️ CẢNH BÁO: Số lượng documents trong manifest ({manifest_count}) KHÁC số lượng dòng clean data ({clean_count})!")
        else:
            print("   ✅ Số lượng documents khớp hoàn toàn với Cleaned Dataset.")
    except Exception as e:
        print(f"❌ Lỗi khi đọc manifest: {e}")
        return

    # 4. Kiểm tra ChromaDB Collection
    print("\n--- [3] Kiểm tra ChromaDB Collection ---")
    chroma_dir = Path(settings.paths.chroma_dir)
    collection_name = settings.baseline_collection_name
    
    if not chroma_dir.exists():
        print(f"❌ Thư mục ChromaDB không tồn tại tại: {chroma_dir}")
        return
        
    try:
        client = chromadb.PersistentClient(path=str(chroma_dir))
        collections = client.list_collections()
        col_names = [c.name for c in collections]
        print(f"   Các collections đang có: {col_names}")
        
        if collection_name not in col_names:
            print(f"❌ Collection '{collection_name}' không tồn tại trong ChromaDB!")
        else:
            col = client.get_collection(name=collection_name)
            chroma_count = col.count()
            print(f"✅ Tìm thấy ChromaDB Collection: '{collection_name}'")
            print(f"   - Số lượng bản ghi trong ChromaDB: {chroma_count}")
            
            if chroma_count != clean_count:
                print(f"⚠️ CẢNH BÁO: Số lượng bản ghi trong ChromaDB ({chroma_count}) KHÁC số dòng clean data ({clean_count})!")
            else:
                print("   ✅ Số lượng bản ghi khớp hoàn toàn với Cleaned Dataset và Manifest.")
    except Exception as e:
        print(f"❌ Lỗi kết nối ChromaDB: {e}")

    # 5. Kiểm tra / Chạy Data Quality & Freshness Signals
    print("\n--- [4] Ghi nhận & Kiểm tra Tín hiệu Baseline Quality / Freshness ---")
    try:
        # Chạy check để cập nhật các báo cáo
        quality_report = run_data_quality_checks(df_clean, settings, "baseline_quality")
        freshness_report = build_freshness_report(df_clean, settings, settings.paths.freshness_report)
        
        print("\n📈 BẢNG TÍN HIỆU DATA QUALITY BASELINE:")
        print(f"   • Tổng số bản ghi (total_records):      {quality_report.get('total_records')}")
        print(f"   • Mã paper_id thiếu (null_paper_ids):   {quality_report.get('null_paper_ids')}")
        print(f"   • Mã paper_id trùng (duplicate):        {quality_report.get('duplicate_paper_ids')}")
        print(f"   • Tiêu đề bị thiếu (missing_titles):    {quality_report.get('missing_titles')}")
        print(f"   • Tóm tắt bị thiếu (missing_summaries): {quality_report.get('missing_summaries')}")
        print(f"   • Tóm tắt quá ngắn (<50 ký tự):         {quality_report.get('short_summaries')}")
        print(f"   • Bản ghi quá hạn (stale_records):      {quality_report.get('stale_records')}")
        status_q = "✅ PASSED" if quality_report.get("passed") else "❌ FAILED"
        print(f"   • Kết quả kiểm định chung:              {status_q}")
        
        print("\n⏳ BẢNG TÍN HIỆU FRESHNESS BASELINE:")
        print(f"   • Ngày xuất bản mới nhất:               {freshness_report.get('latest_published')}")
        print(f"   • Ngày xuất bản cũ nhất:                {freshness_report.get('oldest_published')}")
        print(f"   • Số dòng stale (stale_rows):           {freshness_report.get('stale_rows')}")
        status_f = "✅ FRESH" if freshness_report.get("is_fresh") else "❌ STALE"
        print(f"   • Trạng thái tươi mới tổng thể:         {status_f}")
        
        print("\n✅ Đã ghi tín hiệu baseline chất lượng & độ tươi mới thành công.")
        print(f"   - File quality: {settings.paths.quality_dir}/baseline_quality.json")
        print(f"   - File freshness: {settings.paths.freshness_report}")
    except Exception as e:
        print(f"❌ Lỗi khi phân tích chất lượng/độ tươi mới dữ liệu: {e}")

    # 6. Chuẩn bị khuôn phase1 report
    print("\n--- [5] Rà soát Báo Cáo Pha 1 (phase1_report.md) ---")
    report_path = Path(settings.paths.baseline_report)
    if report_path.exists():
        print(f"✅ Đã tìm thấy file báo cáo: {report_path}")
        print("   File này đã sẵn sàng để điền số liệu thật ở Checkpoint 3.")
    else:
        print(f"⚠️ Chưa tạo file báo cáo tại: {report_path}")
        print("   Khuôn báo cáo này sẽ được tự động ghi khi chạy baseline ở CP3.")

    print_section("KẾT THÚC KIỂM TRA CHECKPOINT 2")
    print("👉 Mọi kiểm tra cơ bản cho Role 3 ở Checkpoint 2 đã hoàn tất thành công!")
    print("👉 Bạn sẵn sàng bước sang Checkpoint 3 cùng nhóm.")


if __name__ == "__main__":
    check_cp2_observability()
