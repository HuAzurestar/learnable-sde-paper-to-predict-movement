"""Conservative whole-package work bound before statistical computation."""

from .aggregate import comparison_dimensions


def _resource_work(rows):
    observed_rows = attempts = 0
    for row in rows:
        if "resource_usage" not in row:
            continue
        usage = row["resource_usage"]
        if type(usage) is not dict or type(usage.get("attempts")) is not list:
            raise ValueError("resource history allocation")
        observed_rows += 1
        attempts += len(usage["attempts"])
        if attempts > 100_000:
            raise ValueError("resource attempt allocation")
    # Sorting sources/unavailable IDs is bounded over all groups by N log2 N.
    # At most one summary per observed row, four source-ID arrays per attempt.
    summaries = 64*observed_rows + attempts*(128 + 8*attempts.bit_length())
    graph_sources = 64*observed_rows + 16*attempts
    return summaries, graph_sources


def comparison_package_plan(bundle, maximum_operations, *, include_resource_summaries=False):
    if type(include_resource_summaries) is not bool:
        raise ValueError("resource summary opt-in must be an explicit boolean")
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
        summary_work, graph_sources = _resource_work(rows) if include_resource_summaries else (0, 0)
        descriptive = len(rows) * (4 + 4 * metrics) + summary_work
        preparation = descriptive
        for contrast in contrasts:
            weights = contrast.get("stratum_weights", [])
            if not isinstance(weights, list) or len(weights) > 256:
                raise ValueError("stratum allocation")
            preparation += len(rows) * (1 + 2 * len(weights))
        bootstrap = repetitions * len({row["block_id"] for row in rows}) * len(contrasts)
        graphs = (1 + len(horizons)) * (256 + len(rows) * (8 + 8 * metrics) + graph_sources)
        if preparation + bootstrap + graphs > maximum_operations:
            raise ValueError("joint package operation quota")
        return {"planned_operation_bound": preparation + bootstrap + graphs,
                "graph_operation_bound": graphs, "descriptive_operation_bound": descriptive,
                "maximum_analysis_operations": maximum_operations - graphs - descriptive}
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise ValueError("RESOURCE_PLAN_REJECTED whole statistical/graph package") from exc
