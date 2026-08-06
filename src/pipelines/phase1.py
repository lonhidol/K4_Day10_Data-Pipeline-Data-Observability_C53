from __future__ import annotations


def main() -> None:
    """Xay dung baseline pipeline end-to-end."""
    from datetime import datetime, UTC
    from pathlib import Path
    
    from core.config import load_settings, require_llm_credentials
    from core.utils import read_json, ensure_parent
    from ingestion.crossref import fetch_source_records, load_raw_records
    from ingestion.cleaning import build_clean_dataframe
    from retrieval.index import LocalEmbeddingIndex
    from evaluation.testset import build_test_set
    from evaluation.metrics import evaluate_pipeline
    from observability.quality import run_data_quality_checks, build_freshness_report
    from observability.reporting import generate_phase1_report
    
    print("--- 🚀 KHỞI ĐỘNG BASELINE PIPELINE (PHA 1) ---")
    
    # 1. Load settings & verify credentials
    print("[1] Loading settings & credentials...")
    settings = load_settings()
    require_llm_credentials(settings)
    
    # 2. Load hoac fetch raw records
    raw_records_path = Path(settings.paths.raw_records_json)
    if settings.refresh_source or not raw_records_path.exists():
        print(f"[2] Fetching fresh records from Crossref API (refresh_source={settings.refresh_source})...")
        records = fetch_source_records(settings)
    else:
        print(f"[2] Loading raw records from snapshot: {raw_records_path}...")
        records = load_raw_records(raw_records_path)
    print(f"    Raw records count: {len(records)}")
        
    # 3. Clean data
    print("[3] Cleaning data...")
    run_date = datetime.now(UTC)
    df = build_clean_dataframe(records, run_date)
    print(f"    Cleaned records count: {len(df)}")
    
    # 4. Save clean CSV/JSON
    print("[4] Saving clean artifacts...")
    ensure_parent(settings.paths.clean_csv)
    df.to_csv(settings.paths.clean_csv, index=False)
    ensure_parent(settings.paths.clean_json)
    df.to_json(settings.paths.clean_json, orient="records", indent=2)
    
    # 5. Build Chroma index
    print("[5] Building Chroma Vector Index (baseline)...")
    index = LocalEmbeddingIndex.build(df, settings, settings.paths.embeddings_json)
    
    # 6. Tao hoac load evaluation set
    testset_path = Path(settings.paths.eval_testset)
    if settings.refresh_test_set or not testset_path.exists():
        print(f"[6] Generating new evaluation test set (refresh_test_set={settings.refresh_test_set})...")
        test_set = build_test_set(df, testset_path)
    else:
        print(f"[6] Loading existing test set from: {testset_path}...")
        test_set = read_json(testset_path)
    print(f"    Test set size: {len(test_set)} samples")
    
    # 7. Evaluate
    print("[7] Running RAG evaluation pass...")
    eval_bundle = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=testset_path,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers
    )
    print(f"    Hit Rate: {eval_bundle.summary['retrieval_hit_rate'] * 100:.2f}%")
    print(f"    Token F1: {eval_bundle.summary['mean_token_f1'] * 100:.2f}%")
    print(f"    LLM Judge Accuracy: {eval_bundle.summary['judge_accuracy'] * 100:.2f}%")
    
    # 8. Run quality checks va freshness report
    print("[8] Running data quality & freshness checks...")
    quality_report = run_data_quality_checks(df, settings, "baseline_quality")
    freshness_report = build_freshness_report(df, settings, settings.paths.freshness_report)
    
    # 9. Tao markdown report
    print("[9] Generating Markdown Report...")
    source_summary = {
        "source_api": settings.source_api,
        "source_query": settings.source_query,
        "raw_count": len(records),
        "clean_count": len(df)
    }
    generate_phase1_report(
        report_path=settings.paths.baseline_report,
        source_summary=source_summary,
        metrics=eval_bundle.summary,
        quality=quality_report,
        freshness=freshness_report
    )
    print(f"✅ Baseline pipeline Pha 1 hoàn thành thành công!")
    print(f"    Báo cáo lưu tại: {settings.paths.baseline_report}")


if __name__ == "__main__":
    main()
