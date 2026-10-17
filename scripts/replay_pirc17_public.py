"""Replay the original public paired arithmetic without importing production backends.

The selected definitions are compiled unchanged from externally hash-pinned PSDE
source, not a rewritten statistical engine. This is a closed source projection,
NOT a generic module loader, an OS sandbox, fresh science or acceptance.
Requires NumPy 1.26.4 and the fixed public PSDE files listed below.
"""
from __future__ import annotations

import argparse
import ast
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType

import numpy as np

SOURCE_PINS = {
    "experiments/pirc17/inference.py": "d25def4bec006173f5c0f005ab3eda0eab2c3a35ec39c842e6622ea446e1a1b2",
    "experiments/pirc17/inference_guard.py": "ac4419a1be4ccd79067df0b05272c5094ec9d0072b5cc6cddfdfdec8c654c416",
    "experiments/pirc17/method_comparisons.py": "0715fc1c995fb1419f8606a1ad52d9ef0273132fd919c1dc0d4bedc01939db40",
    "experiments/pirc17/comparison_registry.py": "889f914385c4329d24c4909f3821ea588e8888d05817768521eb17fde39d4da4",
    "experiments/pirc17/qualification_record.py": "f83fe0bfcdaddab26c50ee52c1bb9e1715e1b40f657d0f72389dd6179c964e91",
    "experiments/pirc17/decision_policy.py": "a063e05f09ee45a3a63d002ab870b9c205dc41eaba8a3711975fe2c6ac7b9dd5",
    "experiments/pirc17/formal_paired.py": "8d23bbcf01f740042fb6fd3ad24aa5b8e471c0da392be79ead4e89f26628ece6",
    "experiments/pirc17/method_mechanisms.py": "30fda1e79a038bfaf88f38ce635fa155bdbac9e972074ee8099b182bced80033",
    "experiments/pirc17/workload.py": "04f3c003626fc88e3ab16cc239695166cbd6c134bd2767ecbea520616ca354fe",
    "experiments/pirc17/formal_analysis.py": "8c2cdbbb9197e51272cdff912ad786c2887c6675b7e7682cddb64c5c8dcaf6d1",
    "experiments/pirc17/final_eval_guard.py": "11aee0fb783347d83bc520de520d5696a40110c85cb3f2fe797070d9ab244234",
    "experiments/pirc17/formal_export.py": "305ea2f685422f31e65ca2f7aa67b2d71aeb8d62fc22beefcfc0dee2bfe196ab",
    "experiments/pirc17/protocol_core.py": "687e0df257a5a8c10eba5cbbd5ce65ba65ec67b5ede2e7b924f076067c60f2e1",
    "experiments/pirc17/metrics.py": "c00059e40421d5267deb35b73096048f22fd439dc9914801ccaf4fd609885570",
    "experiments/pirc17/delivery_policy.py": "b4e5648d8b0b21b676e32ae9b63d70ecd24743e5ab93bffdbb3aee77c57f0b1d",
    "experiments/nex326/specification.py": "31e7d6c496c63bdcfd76c666810bc4851ae5e5e5fd86e1d842442314abecfdd2",
    "experiments/nex326/experiment.json": "f12dc97a20667212b206e46dd274706b8bf799ee54871729727938d2a7d9e54a",
    "experiments/nex326/pirc19_scope_policy.json": "74c5f331fcb9ee11c2dd055b227095026f17c717e83df09d7c5f04bffc0868c6",
    "experiments/pirc17/plans/pre-evaluation-decision-policy-v1.json": "ae81d2fd72d80253ee40bf22b4e9cc7b584b7f879231930712ef04b55cfa405f",
    "experiments/pirc17/evidence/closed-qualification-v1.json": "780432b174cf59f4e6a2e243b00f6a33e831c9f546ad73c52242b4db0cbf81f0",
    "experiments/pirc17/method_rollout.py": "076e3964d8f2f18ea45c93c964962be01a74eff62c380cc8719b5e3af4ac3560",
    "experiments/nex326/model.py": "8863e936419a55d95b4fe31ddb8790fcbb0a923b57cbc3f77cde3e095dea9aa2",
    "experiments/pirc17/plans/full-delivery-policy-v1.json": "0eeb276f4659f7d4f0e242caaa2567ffe17ae51999503d093c863ca6d99cdb9e"
}
POLICY_CONTENT = "d78238790bbf4486fc26946574640f819afbf8b6dcbdeb65d6215266a8d36177"
EXPORT_CONTENT = "29cb892f47301365b3d7b9a2871f3f71d85fe297f7720d0c6489648f8a4d0c50"
PACKAGE_READER_SHA256 = "98fdcbbf6d04c41571de008bf613e748e3f133ccc98c2b47be539f2a4dda4fb0"
NUMPY_VERSION = "1.26.4"
ALLOWED_IMPORTS = {
    "__future__", "collections", "copy", "dataclasses", "hashlib", "itertools",
    "json", "math", "numbers", "numpy", "os", "pathlib", "statistics", "sys", "typing",
}


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def verify_sources(root):
    """Verify the COMPLETE closed dependency set before executing any source."""
    root = Path(root).resolve()
    files = {}
    for relative, expected in SOURCE_PINS.items():
        path = (root / relative).resolve()
        if not path.is_relative_to(root):
            raise ValueError("source escapes the explicitly supplied public repository")
        raw = path.read_bytes()
        if _sha(raw) != expected:
            raise ValueError("frozen public source differs: " + relative)
        files[relative] = raw
    return root, files


def _project(root, files, name, names=None, dependencies=None):
    """Keep pinned function/class/constant AST nodes, unchanged and in source order.

    Backend imports, production consumers and module-level CLI execution are
    excluded. All external names used by the retained definitions are explicitly
    supplied from other verified projections. Nothing is patched into production
    packages or their import names.
    """
    relative = ("experiments/nex326/specification.py" if name == "specification"
                else "experiments/pirc17/" + name + ".py")
    tree = ast.parse(files[relative], filename=relative)
    nodes, found = [], set()
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            modules = ([a.name for a in node.names] if isinstance(node, ast.Import)
                       else [node.module or ""])
            if not getattr(node, "level", 0) and all(
                    m.split(".")[0] in ALLOWED_IMPORTS for m in modules):
                nodes.append(node)
            continue
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            declared = {node.name}
        elif isinstance(node, ast.Assign):
            declared = {t.id for t in node.targets if isinstance(t, ast.Name)}
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            declared = {node.target.id}
        else:
            continue
        if names is None or declared & set(names):
            nodes.append(node)
            found.update(declared)
    if names is not None and found != set(names):
        raise ValueError("closed source selection differs: " + name)
    module_name = "_pirc17_public_" + name
    module = ModuleType(module_name)
    module.__file__ = str(root / relative)
    if dependencies:
        module.__dict__.update(dependencies)
    # dataclasses resolves its defining module while decorating the original class.
    sys.modules[module_name] = module
    try:
        exec(compile(ast.Module(body=nodes, type_ignores=[]), relative, "exec"),
             module.__dict__)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise
    return module


def _take(module, names):
    return {name: getattr(module, name) for name in names.split()}


def load_engine(root):
    root, files = verify_sources(root)
    if np.__version__ != NUMPY_VERSION:
        raise ValueError("exact saved arithmetic requires NumPy " + NUMPY_VERSION)
    inference = _project(root, files, "inference")
    core = _project(root, files, "protocol_core", {"canonical", "digest", "sha256", "unpack"})
    guard = _project(root, files, "inference_guard",
        {"INFERENCE_VERSION", "ROUNDOFF_MULTIPLIER", "infer_guarded"},
        {**_take(inference, "PRIMARY_FAMILY InferenceConfig infer"),
         "BASE_VERSION": inference.INFERENCE_VERSION})
    methods = _project(root, files, "method_comparisons", {"DELTA_M", "FAMILY_DEFINITIONS"})
    comparison = _project(root, files, "comparison_registry", {"GROUPS", "ORIGIN_MODES"})
    qualifier = _project(root, files, "qualification_record",
        {"ROOT", "OUTPUT", "BINDINGS", "digest", "read_bound"})
    delivery = _project(root, files, "delivery_policy", {"BLOCK_LIMIT"})
    # This is the fixed published policy, not a re-created candidate using altered
    # backend/source hashes. Its content AND original file bytes are independently pinned.
    policy = json.loads(files["experiments/pirc17/plans/pre-evaluation-decision-policy-v1.json"])
    if policy["sha256"] != POLICY_CONTENT or core.digest(
            {k: v for k, v in policy.items() if k != "sha256"}) != POLICY_CONTENT:
        raise ValueError("frozen decision policy content differs")
    decision = _project(root, files, "decision_policy", {
        "VERSION", "ROOT", "EVIDENCE_SHA256", "CONFIG", "POWER_TARGET", "PREDICTIVE_SCOPE",
        "qualification_evidence", "registered_contrasts", "planning_gate",
        "numerical_applicability", "infer_qualified_family", "terrain_factor_conclusion",
    }, {**_take(inference, "InferenceConfig PRIMARY_FAMILY SEEDS factor_verdict planning_power"),
        **_take(guard, "ROUNDOFF_MULTIPLIER infer_guarded"),
        **_take(methods, "DELTA_M FAMILY_DEFINITIONS"),
        **_take(comparison, "GROUPS ORIGIN_MODES"),
        **_take(qualifier, "BINDINGS digest read_bound"),
        "EVIDENCE_PATH": qualifier.OUTPUT, "BLOCK_LIMIT": delivery.BLOCK_LIMIT})
    paired = _project(root, files, "formal_paired", None, {
        **_take(comparison, "GROUPS ORIGIN_MODES"),
        **_take(decision, "CONFIG PREDICTIVE_SCOPE infer_qualified_family numerical_applicability planning_gate registered_contrasts terrain_factor_conclusion"),
        **_take(inference, "SEEDS paired_blocks"),
        **_take(methods, "FAMILY_DEFINITIONS"), "unpack": core.unpack})
    spec = _project(root, files, "specification")
    workload = _project(root, files, "workload", {"ROOT", "_digest", "method_inventory"},
                        {"load_experiment_spec": spec.load_experiment_spec})
    mechanisms = _project(root, files, "method_mechanisms", {
        "VERSION", "ROOT", "SCORE_DRAWS", "QUADRATURE_ORDER", "NUMERICAL_SLOTS",
        "SCORE_SLOTS", "VARIANCE_SLOTS", "EXACT_REFERENCE", "STREAM_GROUPS",
        "DIRECT_UNITS", "_digest", "mechanism_registry",
    }, {**_take(inference, "SEEDS"), "load_experiment_spec": spec.load_experiment_spec,
        "method_inventory": workload.method_inventory})
    analysis = _project(root, files, "formal_analysis", {"_comparison_gates"},
                       {"registered_contrasts": decision.registered_contrasts})
    fields = _project(root, files, "final_eval_guard", {"_fields"})
    metrics = _project(root, files, "metrics", {"COVERAGE_LEVELS"})
    engine = _project(root, files, "formal_export", {
        "VERSION", "SCORE_SCALARS", "_fields", "_verify_numeric_witnesses",
        "_replay_gates", "public_tables", "replay_public",
    }, {"guard": fields, "decision_policy": lambda: deepcopy(policy),
        **_take(comparison, "ORIGIN_MODES"),
        **_take(decision, "registered_contrasts"),
        **_take(analysis, "_comparison_gates"),
        **_take(paired, "FAMILIES paired_family terrain_conclusions"),
        **_take(inference, "SEEDS"),
        **_take(mechanisms, "EXACT_REFERENCE NUMERICAL_SLOTS SCORE_SLOTS VARIANCE_SLOTS mechanism_registry"),
        **_take(metrics, "COVERAGE_LEVELS"),
        **_take(core, "canonical digest sha256 unpack")})
    return engine, core


def read_input(directory):
    path = Path(__file__).with_name("pirc17_replay_input.py")
    if _sha(path.read_bytes()) != PACKAGE_READER_SHA256:
        raise ValueError("frozen anonymous package reader differs")
    spec = importlib.util.spec_from_file_location("_pirc17_original_input", path)
    reader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reader)
    raw, _ = reader.read_package(directory)
    return json.loads(raw)


def replay(psde_root, input_directory, output_directory):
    output = Path(output_directory)
    if output.exists():
        raise ValueError("new output directory required; never overwrite existing evidence")
    engine, core = load_engine(psde_root)
    source = read_input(input_directory)
    value = core.unpack(source, expected_sha256=EXPORT_CONTENT)
    result = engine.replay_public(value["inputs"])
    if core.canonical(result) != core.canonical(value["recomputed"]):
        raise ValueError("recomputed complete public result differs from the original")
    output.mkdir(parents=True)
    result_raw = core.canonical(result) + b"\n"
    (output / "recomputed.json").write_bytes(result_raw)
    receipt = {
        "schema_version": "pirc17-clean-public-paired-replay-v1",
        "export_content_sha256": EXPORT_CONTENT,
        "result_content_sha256": core.digest(result),
        "result_file_sha256": _sha(result_raw),
        "recomputed_matches_original": True,
        "source_file_sha256": SOURCE_PINS,
        "projection_loader_sha256": _sha(Path(__file__).read_bytes()),
        "numpy_version": np.__version__,
        "score_rows": len(value["inputs"]["score_rows"]),
        "metric_views": len(result["metric_tables"]),
        "comparisons": sum(len(f["results"]) for m in result["modes"].values()
                           for f in m["families"].values()),
        "fixed_statistical_rng_streams_replayed": True,
        "new_forecasts": 0, "new_fits": 0, "new_particle_scores": 0,
        "raw_trajectory_or_map_inputs_read": False,
        "production_modules_imported": False,
        "policy_generation_rerun": False,
        "human_accepted": False, "scientific_claim_authorized": False,
        "full_table_figure_pdf_rebuild_verified": False,
    }
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n",
                                        encoding="utf-8")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--psde-root", type=Path, required=True)
    parser.add_argument("--input-directory", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    args = parser.parse_args()
    receipt = replay(args.psde_root, args.input_directory, args.output_directory)
    print(json.dumps({k: receipt[k] for k in (
        "recomputed_matches_original", "score_rows", "metric_views", "comparisons",
        "result_content_sha256", "human_accepted")}))


if __name__ == "__main__":
    main()
