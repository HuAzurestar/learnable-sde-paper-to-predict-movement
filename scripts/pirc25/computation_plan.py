"""Conservative whole-package work bound before statistical computation."""

from .aggregate import comparison_dimensions


def comparison_package_plan(bundle, maximum_operations):
    try:
        rows = bundle["cells"]
        if (type(maximum_operations) is not int or not 0 < maximum_operations <= 20_000_000 or
                not isinstance(rows, list) or not 1 <= len(rows) <= 100_000 or
                any(not isinstance(row, dict) or not isinstance(row.get("block_id"), str) or
                    (row.get("metrics") is not None and not isinstance(row["metrics"], dict)) for row in rows)):
            raise ValueError("cell/operation allocation")
        frozen = bundle.get("comparison_plan") or {}
        policy = frozen.get("adjudication_spec") or {}
        contrasts = policy.get("contrasts", [])
        interval = policy.get("interval") or {}
        repetitions = interval.get("replicates", 0)
        metrics = max(len(row.get("metrics") or {}) for row in rows)
        horizons = {str(comparison_dimensions(row)["horizon"]) for row in rows
                    if "horizon" in comparison_dimensions(row)}
        if (not isinstance(contrasts, list) or len(contrasts) > 256 or metrics > 256 or len(horizons) > 256 or
                type(repetitions) is not int or not 0 <= repetitions <= 10_000):
            raise ValueError("metric/family/horizon allocation")
        descriptive = len(rows) * (4 + 4 * metrics)
        preparation = descriptive
        for contrast in contrasts:
            weights = contrast.get("stratum_weights", [])
            if not isinstance(weights, list) or len(weights) > 256:
                raise ValueError("stratum allocation")
            preparation += len(rows) * (1 + 2 * len(weights))
        bootstrap = repetitions * len({row["block_id"] for row in rows}) * len(contrasts)
        graphs = (1 + len(horizons)) * (256 + len(rows) * (8 + 8 * metrics))
        if preparation + bootstrap + graphs > maximum_operations:
            raise ValueError("joint package operation quota")
        return {"planned_operation_bound": preparation + bootstrap + graphs,
                "graph_operation_bound": graphs, "descriptive_operation_bound": descriptive,
                "maximum_analysis_operations": maximum_operations - graphs - descriptive}
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise ValueError("RESOURCE_PLAN_REJECTED whole statistical/graph package") from exc
