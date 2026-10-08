"""Bind reader-facing fitting tables to saved aggregate evidence, not new runs."""
import hashlib
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1] / "paper" / "pirc17"
EVIDENCE = json.loads((ROOT / "fit-diagnostics-v1.json").read_text(encoding="utf-8"))


def test_ledger_and_saved_fit_population():
    ledger = json.loads((ROOT / "claim-ledger.json").read_text(encoding="utf-8"))
    assert hashlib.sha256((ROOT / "fit-diagnostics-v1.json").read_bytes()).hexdigest() == ledger["saved_fit_diagnostics"]["projection_sha256"]
    assert len(EVIDENCE["methods"]) == 16
    assert len(EVIDENCE["terrain"]) == 10
    assert sum(len(m["prediction_slots"]) for m in EVIDENCE["methods"]) == 28
    assert EVIDENCE["terrain_baseline_identical_across_all_fits"]
    assert not EVIDENCE["scope"]["raw_feature_rank_available"]
    assert not EVIDENCE["scope"]["independent_forecast_audit_performed"]
    assert EVIDENCE["scope"]["new_fits"] == EVIDENCE["scope"]["new_predictions"] == 0


@pytest.mark.parametrize("language", ["en", "zh"])
def test_bilingual_terrain_table_exact_rounding(language):
    tex = (ROOT / language / "main.tex").read_text(encoding="utf-8")
    for row in EVIDENCE["terrain"]:
        low, high = row["diffusion_eigenvalues_m2_per_s"]
        expected = (f"{row['configuration']} & {row['conditioner_input_columns']} & "
                    f"{row['train_fitted_mse_m2_per_s2']:.6f} & "
                    f"{row['validation_fitted_mse_m2_per_s2']:.6f} & "
                    f"{row['augmented_ridge_condition']:.1f} & {low:.4f} / {high:.4f}")
        assert expected in tex
        assert row["train_transitions"] == 404
        assert row["validation_transitions"] == 81


@pytest.mark.parametrize("language", ["en", "zh"])
def test_bilingual_interval_table_exact_counts(language):
    tex = (ROOT / language / "main.tex").read_text(encoding="utf-8")
    for row in EVIDENCE["methods"]:
        counts = row["transitions"]
        expected = (f"{int(row['reference_interval_seconds'])} & {counts['train']:,} & "
                    f"{counts['adapt']:,} & {counts['validation']:,}")
        assert expected in tex
        assert row["windows"] == {"train": 328, "adapt": 76, "validation": 81}
