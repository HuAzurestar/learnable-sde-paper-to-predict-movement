"""Metadata and text bindings only; no map sampling or forecast runs."""
import hashlib
import json
from pathlib import Path

import pytest

PAPER = Path(__file__).resolve().parents[1] / "paper/pirc17"


def evidence():
    return json.loads((PAPER / "map-provider-description-v1.json").read_text(encoding="utf-8"))


def test_pinned_original_catalog_and_complete_union_counts():
    r = evidence()
    entry = json.loads((PAPER / "claim-ledger.json").read_text(encoding="utf-8"))["saved_map_provider_description"]
    assert hashlib.sha256((PAPER / "map-provider-description-v1.json").read_bytes()).hexdigest() == entry["projection_sha256"]
    for key in ("receipt_assets", "snapshot_parent_assets", "snapshot_parents_already_in_receipts",
                "additional_snapshot_parent_assets", "retained_catalog_assets"):
        assert r[key] == entry[key]
    assert r["receipt_assets"]+r["additional_snapshot_parent_assets"] == r["retained_catalog_assets"] == 1405
    assert r["snapshot_parents_already_in_receipts"]+r["additional_snapshot_parent_assets"] == r["snapshot_parent_assets"] == 1283
    assert sum(x["retained_catalog_assets"] for x in r["families"]) == 1405
    assert sum(x["parent_references"] for x in r["families"]) == 1283
    assert len(r["source_sha256"]) == 10 and len(r["receipt_sha256"]) == 5


@pytest.mark.parametrize("family,receipt,extra,version,resolution", [
    ("srtm", 833, 41, "SRTM GL1 / Mapzen Skadi public snapshot", {"value":1,"unit":"arc_second"}),
    ("copernicus_dem", 44, 0, "Copernicus DEM GLO-30 2021 release", {"value":30,"unit":"metre"}),
    ("worldcover", 396, 10, "WorldCover 2021 v200", {"value":10,"unit":"metre"}),
    ("overture", 76, 0, "2026-08-19.0", None),
    ("hydrorivers", 5, 0, "HydroRIVERS v1.0", None)])
def test_receipt_specs_remain_declarations_not_extra_parent_or_measured_use(family, receipt, extra, version, resolution):
    row = next(x for x in evidence()["families"] if x["family"] == family)
    assert row["receipt_assets"] == receipt and row["additional_snapshot_parent_assets"] == extra
    assert row["retained_catalog_assets"] == receipt+extra
    assert row["receipt_metadata_only"]["version"]["recorded_values"] == [{"value":version,"records":receipt}]
    if resolution is not None:
        assert row["receipt_metadata_only"]["resolution"]["recorded_values"] == [{"value":resolution,"records":receipt}]
    else:
        assert row["receipt_metadata_only"]["resolution"]["recorded_values"][0]["value"]["unit"] == "not_applicable"


@pytest.mark.parametrize("language", ["en", "zh"])
def test_main_table_reports_each_admitted_family_once_not_case_or_use_counts(language):
    main = (PAPER / language / "main.tex").read_text(encoding="utf-8").split(r"\appendix", 1)[0]
    label = r"\label{tab:model-map-catalog}"
    assert main.count(label) == 1
    start = main.index(label)
    table = main[start:main.index(r"\end{tabular}", start)]
    for family, display in [("srtm", "SRTM / Skadi"), ("copernicus_dem", "Copernicus DEM"),
                            ("worldcover", "ESA WorldCover"), ("overture", "Overture roads"),
                            ("hydrorivers", "HydroRIVERS")]:
        row = next(x for x in evidence()["families"] if x["family"] == family)
        assert table.count(f"{display} & {row['receipt_assets']}+{row['additional_snapshot_parent_assets']} &") == 1
    for count in ("1354", "1283", "1232", "1405"):
        assert count in main
    assert r"\ref{sec:map-query-details}" in main


@pytest.mark.parametrize("language", ["en", "zh"])
def test_source_bound_math_and_non_global_query_scope_are_in_appendix(language):
    tex = (PAPER / language / "main.tex").read_text(encoding="utf-8")
    appendix = tex.split(r"\appendix", 1)[1]
    for label in ("eq:map-frames", "eq:dem-metric-spacing", "eq:dem-stencil"):
        assert appendix.count(r"\label{"+label+"}") == 1
    for literal in ("6371008.8", "500000", "111132.92", "111412.84", "-30000",
                    r"\cos(\pi\varphi_0/180)", r"\psi=\pi\varphi/180", r"2h_E", r"2h_N",
                    "bridleway", "cycleway", "footway", "pedestrian", "steps", "track"):
        assert literal in appendix
    assert r"\path{paper/pirc17/map-provider-description-v1.json}" in appendix
    if language == "en":
        assert "no neighbouring-cell expansion" in appendix
        assert "not a guarantee of a globally closest feature" in appendix
        assert "not measured deployment missingness rates" in appendix
    else:
        assert "不扩张邻接单元" in appendix and "不是已测部署缺失率" in appendix


def test_no_use_counts_clock_accuracy_or_final_qualification_inferred():
    r = evidence()
    assert all(not v for v in r["scope"].values())
    assert r["query_version"] == "pirc17-multicell-cached-query-v1"
    serialized = json.dumps(r)
    for key in ("registered_parent_witnesses", "spatial_extent", "source_url", "verified_assets"):
        assert key not in serialized
    entry = json.loads((PAPER / "claim-ledger.json").read_text(encoding="utf-8"))["saved_map_provider_description"]
    assert not entry["first_containing_raster_NoData_triggers_other_product_fallback"]
    assert not entry["all_review_items_or_paper_complete"]
