"""Independent conservative preparation lineage and attachment permissions."""

if __package__:
    from .analytic_qualification import fingerprint, timestamp
    from .probability_calibration import same
else:
    from analytic_qualification import fingerprint, timestamp
    from probability_calibration import same


def require(condition, detail):
    if not condition:
        raise ValueError("invalid calibration disclosure lineage: " + detail)


def combine(labels):
    values = set(labels)
    return "restricted" if not values or values - {"synthetic", "public"} else "public" if "public" in values else "synthetic"


def upstream(snapshot, catalog):
    require(type(snapshot.get("inputs")) is list and type(catalog.get("entries")) is list, "upstream metadata lists")
    labels = [snapshot.get("visibility", "restricted"), catalog.get("visibility", "restricted")]
    labels.extend(item.get("visibility", labels[0]) for item in snapshot["inputs"])
    labels.extend(item["input"].get("visibility", labels[1]) for item in catalog["entries"])
    return combine([label if type(label) is str else "restricted" for label in labels])


def validate_lineage(record, target, exported_at):
    lineage, visited = record["lineage"], set()
    require(type(lineage) is dict and len(lineage) <= 10000, "bounded complete metadata")
    def manifest(object_id):
        value = lineage[object_id]
        visited.add(object_id)
        if object_id.startswith("study-"):
            require(value["spec_hash"] == fingerprint(value["spec"])
                and value["spec"]["study_id"] == object_id[6:], "secondary authority owner study")
        elif not object_id.startswith("artifact-"):
            require(fingerprint(value) == object_id.rsplit("-", 1)[1], "metadata intrinsic identity")
        else:
            require(value["artifact_id"] == value["sha256"] == object_id[9:], "artifact metadata identity")
        return value
    source, receipt = record["source_spec"], record["source_admission"]
    labels = [cell.get("visibility", "restricted") for cell in source["cells"]]
    settings = source.get("admission") or {}
    if "upstream_snapshot_hash" in settings or "upstream_acceptance_hash" in settings:
        if not settings.get("upstream_snapshot_hash") or not settings.get("upstream_acceptance_hash"):
            labels.append("restricted")
        else:
            labels.append(upstream(manifest("upstream-snapshot-"+settings["upstream_snapshot_hash"]),
                manifest("upstream-acceptance-"+settings["upstream_acceptance_hash"])))
    references = sorted({b["package_hash"] for b in settings["cell_packages"]["bindings"]}) if "cell_packages" in settings else [settings["package_hash"]] if settings.get("package_hash") else []
    visits = 0
    for reference in references:
        seen = set()
        while reference:
            visits += 1
            require(reference not in seen and len(seen) < 32 and visits <= 10000, "bounded acyclic package lineage")
            seen.add(reference)
            package = manifest("package-"+reference)
            labels.append(package.get("visibility", "restricted"))
            pointer = package.get("payload", {}).get("managed_analytic_qualification")
            if pointer is not None:
                labels.append(manifest("artifact-"+pointer["source_artifact_id"])["visibility"])
            if package.get("qualification_hash"):
                report = manifest("qualification-"+package["qualification_hash"])
                labels.extend(manifest("artifact-"+check["artifact_id"])["visibility"] for check in report.get("checks", []))
            reference = package.get("model_hash") if package.get("requires_frozen_model") else None
    documents = receipt.get("documents", {}) if receipt is not None else {}
    require("probability_calibration" not in documents, "nested calibration source")
    if receipt is not None:
        labels.append(receipt["cell"].get("visibility", "restricted"))
    for name in ("package", "frozen_model"):
        if name in documents:
            labels.append(documents[name].get("visibility", "restricted"))
    for name in ("qualification_evidence", "model_qualification_evidence"):
        for item in documents.get(name, []):
            actual = manifest("artifact-"+item["artifact"]["artifact_id"])
            require(same(actual, item["artifact"]), "saved qualification attachment metadata")
            labels.extend([actual["visibility"], item["artifact"].get("visibility", "restricted")])
    if "upstream_snapshot" in documents:
        value = documents["upstream_snapshot"]
        labels.append(upstream(value["snapshot"], value["acceptance_catalog"]))
    groups = [(documents.get("qualification_evidence", []), record["authorization"])]
    if documents.get("model_qualification_evidence"):
        groups.append((documents["model_qualification_evidence"], documents["model_authorization"]))
    if documents.get("propagation_qualification"):
        evidence = documents["propagation_qualification"]
        actual = manifest("artifact-"+evidence["source_artifact"]["artifact_id"])
        require(same(actual, evidence["source_artifact"]), "saved analytic source metadata")
        labels.extend([actual["visibility"], evidence["source_artifact"].get("visibility", "restricted")])
        groups.append(([{"artifact": actual, "content": evidence["source_result"]}], evidence["authorization"]))
    if record["source_artifact"] is not None:
        labels.append(record["source_artifact"]["visibility"])
    visibility = combine(labels)
    require(visibility == record["visibility"], "conservative full source visibility")
    extra = {}
    for items, grant in groups:
        if not items:
            continue
        owner = manifest("study-"+grant["study_id"])["spec"]
        require(grant["protocol_hash"] == owner["protocol_hash"]
            and (target["study_id"] == grant["study_id"] or target["study_id"] in grant.get("consumer_study_ids", []))
            and {"evaluate", "export"} <= set(grant["purposes"])
            and visibility in grant["visibilities"] and timestamp(exported_at) < timestamp(grant["expires_at"]),
            "secondary attachment export consumer permission")
        extra[fingerprint(grant)] = grant
        for item in items:
            metadata = manifest("artifact-"+item["artifact"]["artifact_id"])
            require(same(metadata, item["artifact"]) and metadata["study_id"] == grant["study_id"]
                and metadata["visibility"] in grant["visibilities"] and set(metadata["block_ids"]) <= set(grant["block_ids"])
                and metadata["sha256"] == fingerprint(item["content"]), "secondary attachment bytes/scope")
    require(same(list(extra.values()), record["extra_authorizations"]) and visited == set(lineage),
        "complete selected authority/metadata set without substitutes")
    return visibility
