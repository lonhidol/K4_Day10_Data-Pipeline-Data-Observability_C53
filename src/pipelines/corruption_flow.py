from __future__ import annotations


def main() -> None:
    """Xay dung corruption -> evaluate -> repair -> compare flow."""
    from datetime import datetime, UTC
    from pathlib import Path
    import pandas as pd
    
    from core.config import load_settings, require_llm_credentials
    from core.utils import read_json, ensure_parent
    from ingestion.crossref import load_raw_records
    from ingestion.cleaning import build_clean_dataframe
    from ingestion.corruption import corrupt_clean_dataframe
    from retrieval.index import LocalEmbeddingIndex
    from evaluation.metrics import evaluate_pipeline
    from observability.quality import run_data_quality_checks, build_freshness_report
    from observability.reporting import generate_corruption_report
    
    print("--- 🚀 KHỞI ĐỘNG CORRUPTION & REPAIR FLOW (PHA 2) ---")
    
    # 1. Load settings va clean dataset
    settings = load_settings()
    require_llm_credentials(settings)
    
    clean_csv_path = Path(settings.paths.clean_csv)
    if not clean_csv_path.exists():
        raise RuntimeError("Baseline clean CSV does not exist. Please run Phase 1 first.")
        
    df_clean = pd.read_csv(clean_csv_path)
    print(f"[1] Loaded baseline clean dataset: {len(df_clean)} rows.")
    
    baseline_metrics_path = Path(settings.paths.baseline_metrics)
    if not baseline_metrics_path.exists():
        raise RuntimeError("Baseline metrics JSON does not exist. Please run Phase 1 first.")
    baseline_metrics = read_json(baseline_metrics_path)
    
    # 2. Tao corrupted dataframe
    print("[2] Creating corrupted dataset...")
    df_corrupted = corrupt_clean_dataframe(df_clean, settings.paths.corruption_log)
    
    # 3. Save corrupted artifacts
    print("[3] Saving corrupted artifacts...")
    ensure_parent(settings.paths.corrupted_clean_csv)
    df_corrupted.to_csv(settings.paths.corrupted_clean_csv, index=False)
    ensure_parent(settings.paths.corrupted_clean_json)
    df_corrupted.to_json(settings.paths.corrupted_clean_json, orient="records", indent=2)
    
    # 4. Rebuild index va evaluate (Chroma collection papers-corrupted)
    print("[4] Rebuilding Vector Index (corrupted)...")
    index_corrupted = LocalEmbeddingIndex.build(df_corrupted, settings, settings.paths.corrupted_embeddings_json)
    
    print("[5] Evaluating RAG on corrupted data...")
    corrupted_metrics = evaluate_pipeline(
        settings=settings,
        index=index_corrupted,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.corrupted_metrics,
        answers_output_path=settings.paths.corrupted_answers
    )
    print(f"    Corrupted Hit Rate: {corrupted_metrics.summary['retrieval_hit_rate'] * 100:.2f}%")
    print(f"    Corrupted Token F1: {corrupted_metrics.summary['mean_token_f1'] * 100:.2f}%")
    print(f"    Corrupted Judge Accuracy: {corrupted_metrics.summary['judge_accuracy'] * 100:.2f}%")
    
    # 5. Run quality checks/freshness tren corrupted data
    print("[6] Running data quality & freshness checks on corrupted data...")
    corrupted_quality = run_data_quality_checks(df_corrupted, settings, "corrupted_quality")
    corrupted_freshness_report_path = settings.paths.quality_dir / "corrupted_freshness.json"
    corrupted_freshness = build_freshness_report(df_corrupted, settings, corrupted_freshness_report_path)
    
    # 6. Repair lai tu raw records (Khôi phục)
    print("[7] Repairing dataset from raw source snapshot...")
    raw_records_path = Path(settings.paths.raw_records_json)
    if not raw_records_path.exists():
        raise RuntimeError(f"Raw source snapshot not found at {raw_records_path}")
    raw_records = load_raw_records(raw_records_path)
    
    # Run cleaning again on raw records with same logic
    run_date = datetime.now(UTC)
    df_repaired = build_clean_dataframe(raw_records, run_date)
    print(f"    Repaired records count: {len(df_repaired)}")
    
    print("[8] Saving repaired artifacts...")
    ensure_parent(settings.paths.repaired_clean_csv)
    df_repaired.to_csv(settings.paths.repaired_clean_csv, index=False)
    ensure_parent(settings.paths.repaired_clean_json)
    df_repaired.to_json(settings.paths.repaired_clean_json, orient="records", indent=2)
    
    # 7. Rebuild index va evaluate (Chroma collection papers-repaired)
    print("[9] Rebuilding Vector Index (repaired)...")
    index_repaired = LocalEmbeddingIndex.build(df_repaired, settings, settings.paths.repaired_embeddings_json)
    
    print("[10] Evaluating RAG on repaired data...")
    repaired_metrics = evaluate_pipeline(
        settings=settings,
        index=index_repaired,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.repaired_metrics,
        answers_output_path=settings.paths.repaired_answers
    )
    print(f"    Repaired Hit Rate: {repaired_metrics.summary['retrieval_hit_rate'] * 100:.2f}%")
    print(f"    Repaired Token F1: {repaired_metrics.summary['mean_token_f1'] * 100:.2f}%")
    print(f"    Repaired Judge Accuracy: {repaired_metrics.summary['judge_accuracy'] * 100:.2f}%")
    
    print("[11] Running data quality & freshness checks on repaired data...")
    repaired_quality = run_data_quality_checks(df_repaired, settings, "repaired_quality")
    repaired_freshness_report_path = settings.paths.quality_dir / "repaired_freshness.json"
    repaired_freshness = build_freshness_report(df_repaired, settings, repaired_freshness_report_path)
    
    # 8. Tao comparison report
    print("[12] Generating Comparison Markdown Report...")
    generate_corruption_report(
        report_path=settings.paths.comparison_report,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted_metrics.summary,
        repaired_metrics=repaired_metrics.summary,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness
    )
    print(f"✅ Pha 2 hoàn thành thành công!")
    print(f"    Báo cáo so sánh lưu tại: {settings.paths.comparison_report}")


if __name__ == "__main__":
    main()

