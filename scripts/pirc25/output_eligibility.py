"""Separate execution completion from path target numeric eligibility.

Formal callers must also validate admission. This does not authenticate a row
or alter its recorded status, metrics, cost, identity or denominator.
"""


def path_output_status(row):
    def mapping(value):
        return value if type(value) is dict else {}
    registered = mapping(row.get("registered_cell"))
    admitted = mapping(mapping(row.get("admission")).get("cell"))
    forecast = mapping(mapping(row.get("result")).get("forecast"))
    if (registered.get("plugin_id") != "affine-path-production-chunk"
            and admitted.get("plugin_id") != "affine-path-production-chunk"
            and "path_output_analysis" not in forecast):
        return None
    status = forecast.get("current_output_qualification")
    return status if type(status) is str and status in {"PASSED", "FAILED"} else "UNRESOLVED"


def comparison_eligible(row):
    return row["status"] == "SUCCEEDED" and path_output_status(row) in {None, "PASSED"}


def path_output_counts(cells):
    counts = {}
    for cell in cells:
        status = path_output_status(cell)
        if status is not None:
            counts[status] = counts.get(status, 0)+1
    return dict(sorted(counts.items()))
