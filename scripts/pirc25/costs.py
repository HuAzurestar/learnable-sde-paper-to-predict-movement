"""Offline cost evidence validation and all-attempt resource summaries."""

import hashlib
import json


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def validate_cost(row, bundle, seen):
    try:
        _validate_cost(row, bundle, seen)
    except (KeyError, TypeError, AttributeError) as exc:
        raise ValueError("malformed cost evidence") from exc


def _validate_cost(row, bundle, seen):
    if "cost" not in row:
        return  # Legacy evidence has unavailable costs, not zero cost.
    cost = row["cost"]
    attempts = {item["attempt_id"] for item in row["history"]}
    if row.get("attempt_id") is not None and row["attempt_id"] not in attempts:
        raise ValueError("cost history omits selected attempt")
    entries = []
    for event in cost["sources"]:
        entry = event["payload"]
        if (event["event_kind"] not in {"RESERVE", "SETTLE"} or
                fingerprint({k: v for k, v in event.items() if k != "hash"}) != event["hash"] or
                entry["attempt_id"] not in attempts or entry["run_id"] != row["run_id"] or
                entry["study_id"] != bundle["study_id"] or entry["arm_id"] != row["arm_id"] or
                entry["reservation_id"] in seen):
            raise ValueError("invalid or duplicated cost source identity")
        seen.add(entry["reservation_id"])
        if (not isinstance(entry["settled"], bool) or entry["settled"] != (event["event_kind"] == "SETTLE") or
                any(type(entry[k]) is not int or entry[k] < 0 for k in ("reserved_ms", "charged_ms")) or
                (entry["monotonic_elapsed_ms"] is not None and
                 (type(entry["monotonic_elapsed_ms"]) is not int or entry["monotonic_elapsed_ms"] < 0))):
            raise ValueError("invalid cost measurement")
        expected_charge = (entry["reserved_ms"] if entry["monotonic_elapsed_ms"] is None else entry["monotonic_elapsed_ms"]) if entry["settled"] else 0
        if entry["charged_ms"] != expected_charge or (not entry["settled"] and entry["monotonic_elapsed_ms"] is not None):
            raise ValueError("cost charge differs from measurement policy")
        entries.append(entry)
    if len({e["attempt_id"] for e in entries}) != len(entries):
        raise ValueError("duplicate cost attempt")
    missing = sorted(attempts - {e["attempt_id"] for e in entries})
    unknown = sorted(e["attempt_id"] for e in entries if e["settled"] and e["monotonic_elapsed_ms"] is None)
    pending = sorted(e["attempt_id"] for e in entries if not e["settled"])
    expected = {"unit": "slot-ms", "scope": "all-cell-attempts-including-failures",
                "charged_ms": None if missing else sum(e["charged_ms"] for e in entries if e["settled"]),
                "reserved_ms": sum(e["reserved_ms"] for e in entries if not e["settled"]),
                "measured_ms": None if missing or unknown or pending else sum(e["monotonic_elapsed_ms"] for e in entries),
                "missing_attempt_ids": missing, "unknown_attempt_ids": unknown, "pending_attempt_ids": pending,
                "sources": cost["sources"]}
    if fingerprint(cost) != fingerprint(expected):
        raise ValueError("cost summary differs from frozen sources")


def summarize_cost(cells):
    costs = [cell.get("cost") for cell in cells]
    def total(key):
        return None if any(cost is None or cost[key] is None for cost in costs) else sum(cost[key] for cost in costs)
    return {"unit": "slot-ms", "scope": "all-attempts-in-stratum-not-only-scored-blocks",
            "charged_ms": total("charged_ms"), "reserved_ms": total("reserved_ms"), "measured_ms": total("measured_ms"),
            "unavailable_cells": sum(cost is None or bool(cost["missing_attempt_ids"]) for cost in costs),
            "unknown_attempt_ids": [a for cost in costs if cost for a in cost["unknown_attempt_ids"]],
            "pending_attempt_ids": [a for cost in costs if cost for a in cost["pending_attempt_ids"]],
            "source_event_hashes": [source["hash"] for cost in costs if cost for source in cost["sources"]]}
