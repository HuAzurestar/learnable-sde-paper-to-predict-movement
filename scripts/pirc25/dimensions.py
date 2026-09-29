"""Offline counterpart of the runtime's explicit comparison-stratum contract."""

import json

AXES = ("horizon", "horizons", "region", "scenario", "initialization",
        "prediction_origin", "context_profile", "time_grid")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def comparison_dimensions(cell):
    dimensions = cell.get("comparison_dimensions", {})
    if not isinstance(dimensions, dict) or any(not isinstance(k, str) or not k for k in dimensions):
        raise ValueError("comparison dimensions must be a named mapping")
    dimensions = dict(dimensions)
    if set(dimensions) & {"arm_id", "block_id", "seed"}:
        raise ValueError("sampling identity cannot be a comparison dimension")
    for key in AXES:
        if key in cell:
            if key in dimensions and canonical(dimensions[key]) != canonical(cell[key]):
                raise ValueError("conflicting comparison dimension")
            dimensions[key] = cell[key]
    canonical(dimensions)
    return dimensions
