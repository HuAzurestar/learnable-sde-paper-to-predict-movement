"""Bounded frozen comparison figures, called only inside the shared worker.

Display arithmetic does not recalculate scores, intervals or adjudication.
The settlement receipt resolves the reference after the job has stopped.
"""

import hashlib
import json
import math
from xml.etree import ElementTree as ET

from .aggregate import fingerprint

NS = "http://www.w3.org/2000/svg"
MAX_FIGURE_BYTES = 2 * 1024 * 1024
ET.register_namespace("", NS)


def _encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def comparison_figures(aggregate, *, maximum_figures=257, maximum_operations=20_000_000):
    arms = aggregate["arms"]
    horizons = sorted({str(arm["comparison_dimensions"]["horizon"]) for arm in arms
                       if "horizon" in arm["comparison_dimensions"]})
    selections = [None, *horizons]
    operations = len(selections) * (256 + sum(8 + 8 * len(arm["metrics"]) for arm in arms))
    if (type(maximum_figures) is not int or not 0 < maximum_figures <= 257 or
            len(selections) > maximum_figures or type(maximum_operations) is not int or
            not 0 < maximum_operations <= 20_000_000 or operations > maximum_operations):
        raise ValueError("RESOURCE_PLAN_REJECTED comparison figure allocation")
    decision = aggregate.get("adjudication")
    figures, entries = {}, []
    for horizon in selections:
        selected = [arm for arm in arms if horizon is None or
                    str(arm["comparison_dimensions"].get("horizon")) == horizon]
        metadata = {"schema_version": "pirc25-figure-provenance-v1", "kind": "comparison",
            "aggregate_hash": aggregate["aggregate_hash"], "spec_hash": aggregate["spec_hash"],
            "protocol_hash": aggregate["protocol_hash"], "horizon": horizon,
            "adjudication": decision, "computation_ref": aggregate.get("computation_ref"),
            "cost_source": "resolve-computation-ref-after-settlement",
            "strata": [{"stratum_id": arm["stratum_id"], "dimensions": arm["comparison_dimensions"],
                        "units": arm["metric_units"], "cost": arm["cost"]} for arm in selected]}
        svg = ET.Element(f"{{{NS}}}svg", {"role": "img", "aria-label": "Frozen comparison values and provenance"})
        ET.SubElement(svg, f"{{{NS}}}metadata").text = _encoded(metadata)
        y = 25

        def label(line, x=12, at=None):
            nonlocal y
            ET.SubElement(svg, f"{{{NS}}}text", {"x": str(x), "y": str(y if at is None else at),
                                                "font-size": "13"}).text = str(line)
            if at is None:
                y += 25

        label("Frozen comparison · " + aggregate["aggregate_hash"])
        label(f"Horizon: {horizon or 'all'} · independent unit: block · {aggregate['qualification']}")
        groups = {}
        for arm in selected:
            dimensions = _encoded(arm["comparison_dimensions"])
            label(f"{arm['arm_id']} · {dimensions} · n={arm['independent_n']} · {arm['status']}")
            if not arm["metrics"]:
                label("No complete metric; missing/failed cells retained")
            for metric, value in sorted(arm["metrics"].items()):
                if not isinstance(value, (int, float)) or not math.isfinite(value):
                    raise ValueError("CONTRACT_MISMATCH nonfinite frozen figure metric")
                unit = arm["metric_units"][metric]
                label(f"{metric}: {value} {unit} · cells {arm['successful_cells']}/{arm['expected_cells']}")
                groups.setdefault((metric, unit), []).append((arm, value))
            label("Frozen cost (all attempts): " + _encoded(arm["cost"]))
        if decision:
            label(f"Adjudication: {decision['status']} · {decision['qualification']} · {decision['compare_hash']}")
            label("Full fixed comparison family; horizon selection never recalculates decisions. NO_GAIN is not equivalence.")
            label("Frozen policy: " + _encoded(decision.get("adjudication_spec")))
            if not decision["records"]:
                label("No preregistered decision · " + _encoded(decision["diagnostics"]))
            for record in decision["records"]:
                label(f"{record['comparison_id']} · {record['verdict']} · benefit {record['effect']} {record['unit']}"
                      f" · interval {_encoded(record['interval'])} · paired blocks {record['independent_n']}")
        label("Shared job cost: resolve computation_ref in the settled receipt; not repeated per contrast.")
        label("Fixture verdicts are engineering tests, not scientific qualification.")
        for (metric, unit), values in sorted(groups.items()):
            label(f"{metric} ({unit}) · separate metric/unit scale; no pooled horizons")
            low, high = min(0, *(v for _, v in values)), max(0, *(v for _, v in values))
            # Normalize first, so even finite extreme values cannot overflow high-low.
            scale = max(abs(low), abs(high), 1)
            low, high = low / scale, high / scale
            def x(value):
                return 440 + ((value / scale - low) / (high - low or 1)) * 470
            for arm, value in values:
                label(arm["arm_id"] + " " + _encoded(arm["comparison_dimensions"]), at=y + 12)
                ET.SubElement(svg, f"{{{NS}}}rect", {"x": str(min(x(0), x(value))), "y": str(y),
                    "width": str(max(1, abs(x(value) - x(0)))), "height": "14", "fill": "#287c9c"})
                label(value, x=930, at=y + 12)
                y += 25
            y += 20
        svg.set("viewBox", f"0 0 1100 {y + 15}")
        content = ET.tostring(svg, encoding="unicode")
        raw = content.encode("utf-8")
        if len(raw) > MAX_FIGURE_BYTES:
            raise ValueError("RESOURCE_PLAN_REJECTED comparison figure bytes")
        sha = hashlib.sha256(raw).hexdigest()
        name = "figure-" + sha + ".svg"
        figures[name] = content
        entries.append({"filename": name, "sha256": sha, "kind": "comparison", "horizon": horizon,
                        "size_bytes": len(raw), "media_type": "image/svg+xml"})
    index = {"schema_version": "pirc25-figure-index-v1", "aggregate_hash": aggregate["aggregate_hash"],
             "compare_hash": decision["compare_hash"] if decision else None,
             "computation_ref": aggregate.get("computation_ref"), "figures": entries}
    return {"figure_index": index, "figures": figures}
