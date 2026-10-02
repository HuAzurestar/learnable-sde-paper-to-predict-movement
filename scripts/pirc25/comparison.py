"""Paper-side frozen outputs for a runtime-supervised statistical worker.

No CLI here: the shared runtime owns deadlines, reservations and settlement.
The reference resolves to a receipt published after the entire job stops;
this avoids circular hashes between the measured cost and worker output.
"""

from .adjudication import adjudicate
from .aggregate import aggregate, fingerprint, csv_bytes, evidence_index


def compare_package(bundle, computation_ref, *, formal=False, max_operations=20_000_000):
    decision = adjudicate(bundle, formal=formal, max_operations=max_operations)
    descriptive = aggregate(bundle, formal=formal, descriptive_intervals=False)
    body = {key: value for key, value in descriptive.items() if key != "aggregate_hash"}
    body.update(adjudication=decision, computation_ref=computation_ref)
    value = {**body, "aggregate_hash": fingerprint(body)}
    table = csv_bytes(value)
    return {"aggregate": value, "metrics_csv": table.decode("utf-8"),
            "paper_index": evidence_index(value, table)}
