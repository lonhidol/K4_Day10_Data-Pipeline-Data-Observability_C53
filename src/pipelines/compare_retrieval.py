"""
compare_retrieval.py
--------------------
Chạy cùng 1 câu query baseline trên 3 môi trường (papers-baseline, papers-corrupted, papers-repaired)
để trực quan hóa việc Retrieval thay đổi như thế nào khi dữ liệu bị lỗi và khi đã khôi phục.

Chạy: python src/pipelines/compare_retrieval.py
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from core.config import load_settings
from retrieval.index import LocalEmbeddingIndex


def load_index_for_manifest(settings, manifest_path: Path, collection_name: str) -> LocalEmbeddingIndex | None:
    """Load LocalEmbeddingIndex cho một manifest cụ thể."""
    if not manifest_path.exists():
        print(f"  ❌ Không tìm thấy manifest: {manifest_path}")
        return None
    try:
        import json
        manifest = json.load(open(manifest_path))
        return LocalEmbeddingIndex(
            settings=settings,
            collection_name=collection_name,
            documents=manifest["documents"],
            persist_path=settings.paths.chroma_dir
        )
    except Exception as e:
        print(f"  ❌ Lỗi khi tải {collection_name}: {e}")
        return None


def main():
    print("\n" + "═"*75)
    print("   SO SÁNH KẾT QUẢ RETRIEVAL TRÊN 3 MÔI TRƯỜNG (BASELINE vs CORRUPTED vs REPAIRED)")
    print("═"*75)

    settings = load_settings()

    query = "agentic retrieval augmented generation"
    top_k = 3

    print(f"\n  🔍 Query baseline : \"{query}\"")
    print(f"  🔢 Top-K           : {top_k}\n")

    # 1. Baseline
    idx_baseline = load_index_for_manifest(
        settings, settings.paths.embeddings_json, settings.baseline_collection_name
    )

    # 2. Corrupted
    idx_corrupted = load_index_for_manifest(
        settings, settings.paths.corrupted_embeddings_json, settings.corrupted_collection_name
    )

    # 3. Repaired
    idx_repaired = load_index_for_manifest(
        settings, settings.paths.repaired_embeddings_json, settings.repaired_collection_name
    )

    environments = [
        ("🟢 BASELINE (papers-baseline)", idx_baseline),
        ("🔴 CORRUPTED (papers-corrupted)", idx_corrupted),
        ("🔵 REPAIRED (papers-repaired)", idx_repaired),
    ]

    for env_name, index in environments:
        print("─"*75)
        print(f"  {env_name}")
        print("─"*75)

        if not index:
            print("  (Không thể tải collection)\n")
            continue

        results = index.search(query, top_k=top_k)
        for i, r in enumerate(results, 1):
            title = r.title if len(r.title) <= 65 else r.title[:62] + "..."
            summary_len = len(r.metadata.get("summary", ""))
            print(f"  [{i}] Score: {r.score:.4f} | ID: {r.paper_id:<30}")
            print(f"      Title  : {title}")
            print(f"      Summary: {summary_len} chars | Text: {r.content[:70]}...")
        print()

    print("═"*75)
    print("   QUAN SÁT TÁC ĐỘNG")
    print("─"*75)
    print("  1. BASELINE  : Trả về các bài báo chuẩn xác, thông tin tóm tắt đầy đủ.")
    print("  2. CORRUPTED : Một số bài báo bị mất tóm tắt (0 chars), bị đổi tên hoặc bị drop")
    print("                 → Thứ tự xếp hạng bị xáo trộn, bài liên quan bị tụt điểm.")
    print("  3. REPAIRED  : Phục hồi lại kết quả chuẩn xác y như Baseline.")
    print("═"*75 + "\n")


if __name__ == "__main__":
    main()
