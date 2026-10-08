"""Bind design diagnostics to original saved inputs, without new experiments."""
import hashlib
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1] / "paper" / "pirc17"
PATH = ROOT / "feature-design-description-v1.json"
EVIDENCE = json.loads(PATH.read_text(encoding="utf-8"))


def test_projection_binding_and_narrow_read_only_scope():
    ledger = json.loads((ROOT / "claim-ledger.json").read_text(encoding="utf-8"))
    bound = ledger["original_feature_design_description"]
    assert hashlib.sha256(PATH.read_bytes()).hexdigest() == bound["projection_sha256"]
    assert EVIDENCE["original_input_identity_sha256"] == bound["original_input_identity_sha256"]
    assert EVIDENCE["selected_feature_files"] == 397
    scope = EVIDENCE["scope"]
    for name in ("new_fits", "new_forecasts", "new_particle_scores", "map_queries", "final_eval_numeric_reads"):
        assert scope[name] == 0
    assert not scope["whole_snapshot_revalidated"]
    assert not scope["independent_saved_forecast_audit"]
    assert not scope["private_origins_rows_paths_or_ids_exported"]
    # The new reconstruction does not change what old saved fit records contain.
    fits = json.loads((ROOT / "fit-diagnostics-v1.json").read_text(encoding="utf-8"))
    assert not fits["scope"]["raw_feature_rank_available"]


@pytest.mark.parametrize("role,count", [("train", 404), ("validation", 81)])
def test_original_full_grid_rank_and_masks(role, count):
    configs = EVIDENCE["roles"][role]
    assert len(configs) == 10
    for row in configs.values():
        k = row["numeric_feature_columns"]
        assert row["rows"] == count
        assert row["raw_columns_with_masks_and_intercept"] == 2*k+1
        assert row["constant_one_mask_columns"] == k
        assert row["constant_zero_mask_columns"] == 0
        assert row["raw_design_rank"] < 2*k+1
        assert row["raw_design_condition_number"] is None
        for column in row["columns"]:
            assert column["valid_count"] == count
            assert column["valid_fraction"] == 1
    assert configs["all-terrain"]["raw_design_rank"] == (27 if role == "train" else 25)


@pytest.mark.parametrize("language", ["en", "zh"])
def test_bilingual_raw_design_table_and_penalty_caveat(language):
    tex = (ROOT / language / "main.tex").read_text(encoding="utf-8")
    for name, train in EVIDENCE["roles"]["train"].items():
        validation = EVIDENCE["roles"]["validation"][name]
        expected = (f"{name} & {train['numeric_feature_columns']} & "
                    f"{train['raw_columns_with_masks_and_intercept']} & "
                    f"{train['raw_design_rank']} & {validation['raw_design_rank']} & "
                    f"{train['nonzero_spectrum_condition_number']:.1f}")
        assert expected in tex
    assert r"\label{tab:raw-terrain-design}" in tex
    assert r"\label{eq:constant-mask-penalty}" in tex
    assert r"\frac{c^2}{K+1}" in tex
    assert r"s_{\rm smallest\ retained}" in tex
    assert "feature-design-description-v1.json" in tex
