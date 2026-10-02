"""Frozen worker figures are evidence, not a consumer-side recalculation."""

import hashlib
import json
from xml.etree import ElementTree as ET

import pytest

from scripts.pirc25.aggregate import fingerprint
from scripts.pirc25.comparison import compare_package
from test_shared_adjudication import evidence


def test_comparison_worker_freezes_figures_and_index_with_same_decision():
    package = compare_package(evidence(), {"manifest_id": "synthetic-receipt"})
    index = package["figure_index"]
    aggregate = package["aggregate"]
    assert index["aggregate_hash"] == aggregate["aggregate_hash"]
    assert index["compare_hash"] == aggregate["adjudication"]["compare_hash"]
    assert index["computation_ref"] == aggregate["computation_ref"]
    assert package["paper_index"]["figure_index_hash"] == fingerprint(index)
    assert set(package["figures"]) == {entry["filename"] for entry in index["figures"]}
    assert len(index["figures"]) == 1
    entry = index["figures"][0]
    assert entry["horizon"] is None and entry["kind"] == "comparison"
    svg = package["figures"][entry["filename"]]
    assert hashlib.sha256(svg.encode()).hexdigest() == entry["sha256"]
    metadata = json.loads(ET.fromstring(svg).find("{http://www.w3.org/2000/svg}metadata").text)
    assert metadata["aggregate_hash"] == aggregate["aggregate_hash"]
    assert metadata["adjudication"] == aggregate["adjudication"]
    assert metadata["computation_ref"] == aggregate["computation_ref"]
    assert "GAIN" in svg and "engineering-fixture" in svg


def test_missing_policy_figure_keeps_explicit_unavailability():
    value = evidence()
    value["comparison_plan"].pop("adjudication_spec")
    value["comparison_plan"].pop("adjudication_hash")
    value["bundle_hash"] = fingerprint({k: v for k, v in value.items() if k != "bundle_hash"})
    package = compare_package(value, {"manifest_id": "synthetic-receipt"})
    svg = next(iter(package["figures"].values()))
    assert "NEEDS_PREREGISTRATION" in svg
    assert "No preregistered decision" in svg


def test_figure_renderer_escapes_labels_and_rejects_quota_before_drawing():
    from scripts.pirc25.figures import comparison_figures
    package = compare_package(evidence(), {"manifest_id": "synthetic-receipt"})
    aggregate = package["aggregate"]
    aggregate["arms"][0]["arm_id"] = '<script>alert("bad")</script>'
    with pytest.raises(ValueError, match="RESOURCE_PLAN_REJECTED"):
        comparison_figures(aggregate, maximum_figures=0)
    result = comparison_figures(aggregate)
    svg = next(iter(result["figures"].values()))
    tree = ET.fromstring(svg)
    assert all(node.tag != "{http://www.w3.org/2000/svg}script" for node in tree.iter())
    assert '<script>' not in svg and '&lt;script&gt;' in svg
