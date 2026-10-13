"""Offline independent schema controls, not real qualification or permission."""

from copy import deepcopy
import pytest

from scripts.pirc25.admission import validate_model_permission
from scripts.pirc25.admission_selection import fingerprint, selected_settings


def inputs():
    cells = [{"cell": "one"}, {"cell": "two"}, {"cell": "unavailable", "execution_disposition": {
        "schema_version": "pirc25-execution-disposition-v1", "status": "NOT_IMPLEMENTED", "reason": "frozen reason"}}]
    packages = [{"source": index} for index in range(2)]
    table = {"schema_version": "pirc25-cell-packages-v1", "bindings": [
        {"cell_hash": fingerprint(cell), "package_hash": fingerprint(package)}
        for cell, package in zip(cells, packages)]}
    spec = {"cells": cells, "admission": {"mode": "formal", "protocol_id": "common-inputs",
        "authorization_id": "common-execution", "upstream_root": "unchanged", "cell_packages": table}}
    receipts = [receipt(spec, cell, package) for cell, package in zip(cells, packages)]
    return spec, packages, receipts


def receipt(spec, cell, package):
    table = spec["admission"]["cell_packages"]
    entry = next(row for row in table["bindings"] if row["cell_hash"] == fingerprint(cell))
    return {"mode": spec["admission"]["mode"], "documents": {"package": package}, "admission_selection": {
        "schema_version": "pirc25-cell-package-selection-v1", "cell_hash": fingerprint(cell),
        "package_hash": entry["package_hash"], "binding_hash": fingerprint(entry), "table_hash": fingerprint(table)}}


def test_independent_selection_preserves_common_authority_and_returns_detached_data():
    spec, _, receipts = inputs()
    original = deepcopy(spec)
    for cell, received in zip(spec["cells"], receipts):
        settings = selected_settings(spec, cell, received)
        assert settings["authorization_id"] == "common-execution" and settings["mode"] == "formal"
        assert settings["protocol_id"] == "common-inputs" and settings["upstream_root"] == "unchanged"
        settings["mode"] = "forged"
    assert spec == original


@pytest.mark.parametrize("fault", ["missing", "duplicate", "foreign", "unavailable", "default", "model-default",
    "mode", "protocol", "grant", "upstream", "version-only", "bad-identifier", "bad-hash", "bad-schema",
    "extra-table-key", "duplicate-cell", "cell-cap", "binding-cap", "invalid-marker", "marker-execution"])
def test_independent_table_validation_refuses_without_fallback(fault):
    spec, _, receipts = inputs()
    settings = spec["admission"]
    table = settings["cell_packages"]
    entry = table["bindings"][0]
    if fault == "missing":
        table["bindings"].pop()
    elif fault == "duplicate":
        table["bindings"].append(deepcopy(entry))
    elif fault in {"foreign", "unavailable"}:
        entry["cell_hash"] = fingerprint("foreign") if fault == "foreign" else fingerprint(spec["cells"][2])
    elif fault in {"default", "model-default"}:
        settings["package_hash" if fault == "default" else "model_authorization_id"] = "ambiguous"
    elif fault in {"mode", "protocol", "grant", "upstream"}:
        entry[{"mode": "mode", "protocol": "protocol_id", "grant": "authorization_id", "upstream": "upstream_root"}[fault]] = "override"
    elif fault == "version-only":
        entry["model_authorization_version"] = "v1"
    elif fault == "bad-identifier":
        entry["model_protocol_id"] = "../outside"
    elif fault == "bad-hash":
        entry["package_hash"] = "not-a-hash"
    elif fault == "bad-schema":
        table["schema_version"] = "unknown"
    elif fault == "extra-table-key":
        table["fallback"] = "forbidden"
    elif fault == "duplicate-cell":
        spec["cells"].append(deepcopy(spec["cells"][0]))
    elif fault == "cell-cap":
        spec["cells"] *= 3334
    elif fault == "binding-cap":
        table["bindings"] = [entry]*10001
    elif fault == "invalid-marker":
        spec["cells"][2]["execution_disposition"]["status"] = []
    else:
        spec["cells"][2]["execution"] = {}
    with pytest.raises(ValueError, match="cell package selection"):
        selected_settings(spec, spec["cells"][0], receipts[0])


@pytest.mark.parametrize("fault", ["missing", "cell", "package", "binding", "table", "schema", "mode", "body", "other-receipt"])
def test_rehashed_transport_cannot_substitute_receipt_selection(fault):
    spec, _, receipts = inputs()
    received = receipts[0]
    if fault == "missing":
        received.pop("admission_selection")
    elif fault in {"cell", "package", "binding", "table"}:
        received["admission_selection"][fault + "_hash"] = fingerprint("substitution")
    elif fault == "schema":
        received["admission_selection"]["schema_version"] = "unknown"
    elif fault == "mode":
        received["mode"] = "fixture"
    elif fault == "body":
        received["documents"]["package"] = {"source": "another"}
    else:
        received = receipts[1]
    with pytest.raises(ValueError, match="cell package selection"):
        selected_settings(spec, spec["cells"][0], received)


def test_same_selected_package_cannot_hide_changes_elsewhere_in_the_table():
    spec, _, receipts = inputs()
    spec["admission"]["cell_packages"]["bindings"][1]["package_hash"] = fingerprint("changed-other-source")
    with pytest.raises(ValueError, match="complete frozen table"):
        selected_settings(spec, spec["cells"][0], receipts[0])


def test_table_byte_quota_is_separate_from_cardinality():
    cells = [{"cell": index} for index in range(10000)]
    settings = {"cell_packages": {"schema_version": "pirc25-cell-packages-v1", "bindings": [
        {"cell_hash": fingerprint(cell), "package_hash": fingerprint("source"),
         "model_authorization_id": "a"*120, "model_authorization_version": "v"*120,
         "model_protocol_id": "p"*120} for cell in cells]}}
    with pytest.raises(ValueError, match="quota"):
        selected_settings({"cells": cells, "admission": settings}, cells[0], {})


def test_legacy_single_package_compatibility_and_unexpected_selection_refusal():
    spec = {"admission": {"mode": "formal", "package_hash": fingerprint("legacy")}}
    assert selected_settings(spec, {}, {}) == spec["admission"]
    with pytest.raises(ValueError, match="legacy"):
        selected_settings(spec, {}, {"admission_selection": {"forged": True}})


@pytest.mark.parametrize("fault", [None, "wrong-grant", "wrong-version", "wrong-consumer", "wrong-purpose", "wrong-protocol"])
def test_model_source_permission_uses_selected_cell_not_another_cell(fault):
    spec, packages, _ = inputs()
    spec["study_id"] = "consumer"
    for index, entry in enumerate(spec["admission"]["cell_packages"]["bindings"]):
        entry.update(model_authorization_id="owner-"+str(index), model_authorization_version="v2",
                     model_protocol_id="model-inputs-"+str(index))
    cell = spec["cells"][1]
    received = receipt(spec, cell, packages[1])
    model = {"study_id": "owner", "protocol_hash": fingerprint("model-data"), "visibility": "restricted"}
    grant = {"authorization_id": "owner-1", "version": "v2", "study_id": "owner", "protocol_hash": model["protocol_hash"],
        "consumer_study_ids": ["consumer"], "purposes": ["evaluate"], "visibilities": ["restricted"],
        "expires_at": "2099-01-01T00:00:00+00:00"}
    if fault:
        field, value = {"wrong-grant": ("authorization_id", "owner-0"), "wrong-version": ("version", "v1"),
            "wrong-consumer": ("consumer_study_ids", []), "wrong-purpose": ("purposes", ["preview"]),
            "wrong-protocol": ("protocol_hash", fingerprint("unrelated"))}[fault]
        grant[field] = value
        with pytest.raises(ValueError, match="admission evidence"):
            validate_model_permission(model, grant, spec, "2026-10-07T00:00:00+00:00", cell=cell, receipt=received)
    else:
        validate_model_permission(model, grant, spec, "2026-10-07T00:00:00+00:00", cell=cell, receipt=received)
