"""Rhetorical structure and naming guards; no scientific re-execution."""
import json
from pathlib import Path
import pytest

PAPER = Path(__file__).resolve().parents[1] / "paper/pirc17"


@pytest.mark.parametrize("language", ["en", "zh"])
def test_new_names_preserve_saved_identity_and_descriptive_scope(language):
    body = (PAPER / language / "main.tex").read_text(encoding="utf-8")
    assert all(name in body for name in ("HSM-SDE", "RDM-SDE", "CV", "Full01", "Full11", "GMM", "RQ1", "RQ2"))
    assert "expectation--maximisation" in body if language == "en" else "不是通过EM拟合" in body
    assert "not a direct statistical" in body if language == "en" else "不是两类设计的直接统计检验" in body
    assert "not evidence that learning itself" in body if language == "en" else "不意味着学习本身没有必要" in body


@pytest.mark.parametrize("language", ["en", "zh"])
def test_horizon_design_reliability_reading_order(language):
    body = (PAPER / language / "main.tex").read_text(encoding="utf-8")
    labels = ["sec:horizon-utility", "sec:design-choices", "sec:region-reliability", "sec:terrain-results"]
    locations = [body.index(r"\label{"+label+"}") for label in labels]
    assert locations == sorted(locations)
    start, stop = locations[1:3]
    design = body[start:stop]
    assert all(value in design for value in ("2.83", "1299.11", "[-21.22,16.33]", "-11.56", "-23.40",
                                            "+2.60", "+2.19", "+0.50", "-0.04", "scratch", "Reptile", "drift-only", "two-step"))
    assert design.index("2.83") < design.index("-11.56") < design.index("scratch")


def test_argument_record_has_four_bounded_conclusions_and_no_new_evidence():
    record = json.loads((PAPER / "reader-v5-argument.json").read_text(encoding="utf-8"))
    assert [claim["id"] for claim in record["conclusions"]] == ["C1", "C2", "C3", "C4"]
    assert all(claim["evidence"] and claim["qualification"] for claim in record["conclusions"])
    assert record["main_figures"] == 4 and record["main_tables"] == 2
    assert record["supplementary_tables"] == 50
    assert record["new_fits_forecasts_scores_map_queries_or_resampling"] == 0
    assert record["original_registered_questions_or_inference_changed"] is False
