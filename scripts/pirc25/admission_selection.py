"""Independent stdlib-only verification of complete per-cell package selection.

Inputs are frozen transport metadata, not permission to read data or run work.
No runtime import, package lookup, fallback, grant creation or qualification.
"""

import hashlib
import json
import re


MODEL_FIELDS = frozenset({"model_authorization_id", "model_authorization_version", "model_protocol_id"})


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def fingerprint(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def require(condition, detail):
    if not condition:
        raise ValueError("invalid admission evidence: cell package selection " + detail)


def hash_ref(value):
    return type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def executable(cell):
    if "execution_disposition" not in cell:
        return True
    marker = cell["execution_disposition"]
    require(type(marker) is dict and set(marker) == {"schema_version", "status", "reason"}
        and marker["schema_version"] == "pirc25-execution-disposition-v1"
        and type(marker["status"]) is str
        and marker["status"] in {"NOT_IMPLEMENTED", "INELIGIBLE", "MISSING_INPUT", "UNQUALIFIED"}
        and type(marker["reason"]) is str and 0 < len(marker["reason"]) <= 512
        and not any(ord(char) < 32 for char in marker["reason"]) and "execution" not in cell,
        "malformed non-executable declaration")
    return False


def selected_settings(spec, cell, receipt):
    """Verify entry/table/receipt hashes and return detached effective settings."""
    settings = spec.get("admission") or {}
    require(type(settings) is dict, "settings must be an object")
    if "cell_packages" not in settings:
        require(receipt.get("admission_selection") is None, "legacy input has unexpected selection")
        return json.loads(canonical(settings))
    require(type(cell) is dict and type(receipt) is dict, "selected cell/receipt must be objects")
    require("package_hash" not in settings and not set(settings) & MODEL_FIELDS, "ambiguous default binding")
    table = settings["cell_packages"]
    require(type(table) is dict and set(table) == {"schema_version", "bindings"}
        and table["schema_version"] == "pirc25-cell-packages-v1"
        and type(table["bindings"]) is list and len(table["bindings"]) <= 10000
        and type(spec.get("cells")) is list and 0 < len(spec["cells"]) <= 10000
        and all(type(row) is dict for row in spec["cells"]), "invalid bounded table/matrix")
    cells = {fingerprint(row): row for row in spec["cells"]}
    require(len(cells) == len(spec["cells"]), "duplicate registered cell")
    expected = {key for key, row in cells.items() if executable(row)}
    key = fingerprint(cell)
    require(key in expected and cells[key] == cell, "selected cell is not executable registered input")
    bindings = {}
    for entry in table["bindings"]:
        require(type(entry) is dict and {"cell_hash", "package_hash"} <= set(entry)
            and not set(entry) - {"cell_hash", "package_hash"} - MODEL_FIELDS
            and hash_ref(entry["cell_hash"]) and hash_ref(entry["package_hash"])
            and entry["cell_hash"] not in bindings, "invalid or duplicate entry")
        for field in MODEL_FIELDS & set(entry):
            require(type(entry[field]) is str and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", entry[field]),
                    "invalid model-source identity")
        require("model_authorization_version" not in entry or "model_authorization_id" in entry,
                "model-source version without identity")
        bindings[entry["cell_hash"]] = entry
    require(set(bindings) == expected, "table must cover exactly all executable cells")
    require(len(canonical(table)) <= 4*1024*1024, "table metadata quota exceeded")
    entry = bindings[key]
    selection = {"schema_version": "pirc25-cell-package-selection-v1", "cell_hash": key,
        "package_hash": entry["package_hash"], "binding_hash": fingerprint(entry), "table_hash": fingerprint(table)}
    require(receipt.get("admission_selection") == selection, "receipt differs from complete frozen table")
    documents = receipt.get("documents")
    require(type(documents) is dict and type(documents.get("package")) is dict
        and fingerprint(documents["package"]) == entry["package_hash"]
        and receipt.get("mode") == settings.get("mode"), "package or mode differs from selected input")
    common = {name: value for name, value in settings.items() if name != "cell_packages"}
    common.update({name: value for name, value in entry.items() if name != "cell_hash"})
    return json.loads(canonical(common))
