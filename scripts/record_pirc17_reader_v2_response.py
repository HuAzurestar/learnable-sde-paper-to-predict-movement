"""Create an additive review response; preserve original criteria and evidence.

Only anonymous build/check metadata is projected from the private receipt.
This command does not assert remote delivery or human/scientific acceptance.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper/pirc17"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record(public_build, public_inspection, local_build):
    destination = PAPER / "revision46-response-v3.json"
    if destination.exists():
        raise ValueError("A response version is immutable; choose a new version")
    previous = PAPER / "revision46-response-v2.json"
    old = read(previous)
    value = deepcopy(old)
    build = read(public_build / "build-manifest.json")
    inspection = read(public_inspection / "inspection.json")
    local_check = read(local_build / "reader-v2-case-check.json")
    assert local_check["passed"] and len(build["manuscripts"]) == 6
    assert all(r["strict_log_passed"] for r in build["manuscripts"])
    assert all(not r["text_outside_page"] for r in inspection["documents"])
    assert len(old["tasks"]) == 46 and sum(len(t["checklist"]) for t in old["tasks"]) == 305
    changes = {
        "G01": "Correct built/vegetation/water-wetland/valid-other groups; nodata is missing. Projection diagram does not depict slope magnitude.",
        "G02": "Put the ten-by-nine design and K/2K/(2K+1) dimensions in the body; preserve LOO/LIO roles and signs.",
        "G05": "Put all 21 contrasts (42 coordinates) in the body, preserving each control and the ES/FDE distinction.",
        "G06": "Add three seed-versus-block examples to the body; five seeds are not independent people.",
        "G08": "Explain the saved 404/81 training/validation diagnostic and why improved fit is not terrain generalization.",
        "G10": "Pale heatmaps with black text, linear size scale and signed coverage deviation normalized symmetrically to [-90,90] pp.",
        "G12": "Local-only six maps re-laid out with shared outside legends, origin star, hindsight-only truth and purple dashed disks. Same cases, fixed seed, arrays, targets and annotations; no new score.",
        "O06": "Expanded bilingual main bodies; separately versioned public six-document package and local map-containing bodies. Preserve historical v1 sources and PDFs.",
        "O08": "Explain score/location trade-offs, undercoverage versus area, particle containment versus target calibration and low-density ensemble means. External-reader feedback remains pending.",
        "R05": "Explain proxy/label mismatch and long-horizon undercoverage; do not claim recalibration has been performed.",
        "R06": "Explain penalty/representation confounding; do not promote disclosure to an isolated terrain-effect estimate.",
        "R10": "Existing per-horizon means are presented; an external task-matched probabilistic baseline remains absent.",
        "R13": "Date historical pending captions and distinguish completed saved-output audit/scalar replay from absent second-stream bootstrap endpoints.",
        "R16": "Equal positive and negative deviations from nominal 90% have equal color distance; no asymmetric 90/10 normalization.",
        "X05": "Correct ES only after binding execution, runtime and public replay to the original scorer; retain original scientific scores and audit limitations.",
        "X07": "Check strict bilingual PDFs, page boundaries, new figure layouts, six maps and embedded map-label sizes; no independent-reader acceptance inferred.",
        "X08": "Preserve the original 305 criterion texts, original42 mapping and historical response; explicitly supersede the erroneous ES criterion.",
    }
    gaps = {
        "R05": ("N03", "The validation proxy does not evaluate the actual multi-mode multi-step distribution, and validation mode labels do not resolve GMM residual-group correspondence. No development-only recalibration with independent evaluation has been run."),
        "R06": ("N04", "Terrain information remains confounded with representation dimension, redundant constant masks, feature scaling and effective ridge penalty. No matched-penalty/representation experiment has isolated the information increment."),
        "R10": ("N01", "No task-matched external probabilistic constant-velocity/state-space baseline has been fitted and evaluated with the same prefix, clocks, targets and block aggregation. The deterministic inertia reference and existing per-horizon means do not fill this gap."),
    }
    superseded = 0
    for task in value["tasks"]:
        task["reader_v2_review"] = {
            "changed": task["id"] in changes,
            "scope": changes.get(task["id"], "Historical document review retained; no new scientific execution or independent acceptance in this revision."),
            "human_accepted": False,
        }
        if task["id"] in gaps:
            design, gap = gaps[task["id"]]
            task["remaining_scientific_gaps"] = [gap]
            task["follow_up_design"] = {"id": design, "location": "paper/pirc17/en/supplement.tex", "executed": False}
        for criterion in task["checklist"]:
            if "N²" in criterion["criterion"] and "N(N−1)" in criterion["criterion"]:
                criterion["historical_status"] = criterion["status"]
                criterion["status"] = "superseded_erroneous_criterion"
                criterion["corrected_criterion"] = "Use the execution-bound ordered-pair U statistic with denominator 2N(N-1), excluding diagonal pairs; use direct distance for the point-mass reference. Do not rescore research outputs."
                criterion["correction_evidence"] = ["paper/pirc17/reader-v2-score-binding.json", "tests/test_pirc17_reader_v2.py", "paper/pirc17/en/reader-v2-errata.tex"]
                superseded += 1
        future_indices = {"R05": [7], "R06": [6], "R10": [0, 1, 2, 6]}.get(task["id"], [])
        for index in future_indices:
            row = task["checklist"][index]
            row["historical_status"] = row["status"]
            row["status"] = "future_design_documented_not_executed"
    assert superseded == 1
    assert [[c["criterion"] for c in t["checklist"]] for t in old["tasks"]] == [[c["criterion"] for c in t["checklist"]] for t in value["tasks"]]
    value.update(schema_version="pirc17-revision46-response-v3", review_date="2026-10-13",
                 prior_response_sha256=digest(previous), public_build_manifest="paper/pirc17/revision46-review-v2/build-manifest.json",
                 source_checkpoint=build["repository_head"],
                 local_build_manifest_sha256=digest(local_build / "local-build-manifest.json"),
                 local_case_check_sha256=digest(local_build / "reader-v2-case-check.json"),
                 public_pages={r["language"]+"/"+r["entry"]: r["pages"] for r in inspection["documents"]},
                 local_main_pages={r["language"]: r["pages"] for r in local_check["documents"]},
                 minimum_checked_embedded_map_label_pt=min(r["minimum_checked_map_font_pt"] for r in local_check["documents"]),
                 verification_definition="Historical checklist reviews are preserved, not newly certified. Reader-v2 changes have targeted numeric/source guards, strict build, links and scoped visual inspection; external-reader/authorship/human acceptance remain pending.")
    value["layout_review"] = {"all_public_pages_automatic_boundary_check": True, "text_outside_page": 0,
                              "visual_scope": "Both public main-body contact sheets; changed supplementary/audit pages and figure assets; all six local map assets and bilingual main map pages.",
                              "all_pages_full_text_independently_reviewed": False,
                              "remaining_layout_limits": ["Some figures occupy float-only pages; fonts and margins were not reduced to meet a page cap.", "English main ends with a one-reference page."]}
    value.pop("paper_pr_delivered", None)
    value.pop("MPA_master_merged", None)
    value["delivery_tracking"] = "Remote PR head and local project-state commits are verified separately after this package is prepared."
    value["original_criterion_count"] = 305
    value["erroneous_criteria_explicitly_superseded"] = 1
    value["new_research_scores"] = 0
    destination.write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print("Created additive v3 response:46 cards,305 original criteria,one explicit ES correction;no acceptance.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("public-build", "public-inspection", "local-build"):
        parser.add_argument("--"+arg, type=Path, required=True)
    record(**vars(parser.parse_args()))
