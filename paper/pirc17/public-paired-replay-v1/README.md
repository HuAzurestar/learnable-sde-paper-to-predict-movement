# Clean public replay of all original paired and metric views

This delivers arithmetic reproducibility, not fresh experiments, independent
raw-output auditing, numerical convergence or human acceptance. The actual
clean run used Python 3.10.13 / NumPy 1.26.4 on Windows, with no Torch, PyArrow,
DuckDB, Pandas, Rasterio or GeoPandas installed.

All 11,368 original score rows are used: 11,363 successes and five retained
failures, three origin modes, all 90 registered comparisons and 120 metric
views. The complete recomputed object is canonically identical to the fixed
original `recomputed` object. Result content SHA-256:
`17202930fbcbb18c735ae8ef41dcd6030b2f26b04ac9debd1c274c2716f510f4`.
No failures are replaced, zeros imputed, population subsets selected, seeds
added, numerical thresholds changed or fits/forecasts/particle scores rerun.

## Why there is a closed source projection

The original PSDE `formal_export` import chain includes raw fitting and
geospatial backends. Altering sealed production source would change its
source bindings. The new TSDE `scripts/replay_pirc17_public.py` instead reads
23 explicitly pinned public PSDE files, verifies every byte hash **before**
executing any selected code, and compiles the unchanged original arithmetic
function/class/constant AST definitions with explicit dependencies. It omits
backend imports, production consumer classes, calibration/forecast functions
and module-level CLI execution. It does not monkeypatch production packages
or duplicate/rewrite the inference kernel. The published frozen decision
policy is verified by both file and content hashes, not regenerated from a
different source revision. Any differing required source is a hard failure.

This is a closed projection of this specific code version, **not a general
module loader, OS sandbox or the original heavyweight CLI import**. The
original heavyweight CLI is still separate; do not claim that it works in
a NumPy-only environment. The original two fixed B=2000 statistical RNG
streams and variance bootstrap are replayed unchanged to reproduce intervals
and verdicts. These are repeated fixed statistical calculations, not new
forecast seeds, experimental draws, tuning or another convergence study.

## Reproduce from a public checkout

From the TSDE repository root, create a new environment and public PSDE checkout:

```powershell
python -m venv .tmp/pirc17-replay-env
.tmp/pirc17-replay-env/Scripts/python.exe -m pip --isolated install numpy==1.26.4
git clone https://github.com/HuAzurestar/learnable-sde-for-movement-prediction.git .tmp/pirc17-public-psde
git -C .tmp/pirc17-public-psde checkout --detach 12ff040e1559d4f92b1e95641448f69d6cc8c94d
.tmp/pirc17-replay-env/Scripts/python.exe -I scripts/replay_pirc17_public.py --psde-root .tmp/pirc17-public-psde --input-directory paper/pirc17/replay-input-v1 --output-directory .tmp/pirc17-paired-rebuilt
```

Expected printed counters: score_rows11368, metric_views120, comparisons90,
recomputed_matches_original=true, human_accepted=false, and the result content
hash above. `recomputed.json` preserves the entire result; `receipt.json`
records input, every PSDE source hash, the thin-loader hash and explicit
non-acceptance flags. Only a new output directory is allowed. Repeated runs
must use new directories; no original evidence is overwritten or locked.

The bundled [actual clean-run receipt](receipt.json) is evidence of the
reported run, not a substitute for rerunning these commands. The input
transport and file/content pins remain in [the original input package](../replay-input-v1/README.md).
The current clean run's canonical JSON file hash is
`f0825dd4d32ea71979497c2b591f127f1c0567dc3ebe50916efbdda280f6e363`.

## Still not closed

This independently demonstrates complete public **paired/metric arithmetic**,
not the private raw-trajectory audit, geographic/participant independence,
physical clock certification, accepted evidence cards or scientific approval.
A clean end-to-end reproduction of all sixteen CSV tables, sixteen figure
groups and bilingual PDF build remains to be verified. Public/private case
test boundaries, remaining manuscript evidence gaps, verified authorship,
privacy/map publication decisions and real human acceptance remain required.
