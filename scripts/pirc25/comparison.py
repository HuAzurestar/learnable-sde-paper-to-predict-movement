"""Paper-side frozen outputs for a runtime-supervised statistical worker.

No CLI here: the shared runtime owns deadlines, reservations and settlement.
The reference resolves to a receipt published after the entire job stops;
this avoids circular hashes between the measured cost and worker output.
"""

from .adjudication import adjudicate
from .aggregate import aggregate, fingerprint, csv_bytes, evidence_index
from .figures import comparison_figures
from .computation_plan import comparison_package_plan


def compare_package(bundle, computation_ref, *, formal=False, max_operations=20_000_000):
    plan = comparison_package_plan(bundle, max_operations)
    decision = adjudicate(bundle, formal=formal, max_operations=plan["maximum_analysis_operations"])
    descriptive = aggregate(bundle, formal=formal, descriptive_intervals=False)
    body = {key: value for key, value in descriptive.items() if key != "aggregate_hash"}
    body.update(adjudication=decision, computation_ref=computation_ref,
                qualification="formal" if formal else "engineering-fixture")
    value = {**body, "aggregate_hash": fingerprint(body)}
    table = csv_bytes(value)
    figures = comparison_figures(value, maximum_operations=plan["graph_operation_bound"])
    return {"aggregate": value, "metrics_csv": table.decode("utf-8"),
            "paper_index": {**evidence_index(value, table), "figure_index_hash": fingerprint(figures["figure_index"])},
            **figures}
