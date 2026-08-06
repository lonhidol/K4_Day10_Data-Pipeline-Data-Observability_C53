import sys
from pathlib import Path

# Add src to sys.path so we can run this directly if needed
sys.path.append(str(Path(__file__).resolve().parents[1]))

from core.config import load_settings
from retrieval.index import LocalEmbeddingIndex

def run_smoke_test():
    print("--- 🚀 Khởi chạy Smoke Test cho Retrieval ---")
    settings = load_settings()
    
    print("\n[1] Đang tải LocalEmbeddingIndex...")
    try:
        index = LocalEmbeddingIndex.load(settings)
        print(f"✅ Tải thành công. Collection hiện tại: '{index.collection_name}'")
        print(f"✅ Số lượng documents trong bộ nhớ: {len(index.documents)}")
    except Exception as e:
        print(f"❌ Lỗi khi tải index (Có thể chưa chạy pipeline ingest?): {e}")
        return

    print("\n" + "="*50)
    print("[2] SMOKE TEST 1: Semantic Search")
    print("="*50)
    
    test_query = "agentic retrieval augmented generation"
    print(f"🔍 Câu truy vấn: '{test_query}'")
    
    results = index.search(test_query, top_k=2)
    
    if not results:
        print("❌ Không tìm thấy kết quả nào.")
    else:
        for i, res in enumerate(results, 1):
            print(f"\nKết quả #{i}:")
            print(f"  - Title:    {res.title}")
            print(f"  - Paper ID: {res.paper_id}")
            print(f"  - Score:    {res.score:.4f}")
            print(f"  - Content:  {res.content[:150]}...")
            
        print("\n" + "="*50)
        print("[3] SMOKE TEST 2: Exact Lookup (Theo ID)")
        print("="*50)
        
        test_id = results[0].paper_id
        print(f"🔍 Đang lookup Paper ID: '{test_id}'")
        
        record = index.lookup(test_id)
        if record:
            print("✅ Lookup thành công!")
            print(f"  - Title retrieved: {record['title']}")
            print(f"  - PDF URL:         {record['metadata'].get('pdf_url', 'N/A')}")
        else:
            print("❌ Lookup thất bại! Không tìm thấy ID này trong dict.")

if __name__ == "__main__":
    run_smoke_test()
