# Learnable SDE paper to predict movement

TeX manuscript sources for the learnable stochastic differential equation
research on movement prediction.

## Layout

```text
paper/
  en/main.tex       English source of record
  en/main.pdf       Checked preview of the English draft
  zh/main.tex       Chinese translation, aligned section by section
  zh/main.pdf       Checked preview of the Chinese draft
  figures/          Approved source figures only
  tables/           Aggregate, reviewed tables only
```

The English source is authoritative; the Chinese manuscript is a translation
draft and must remain aligned with it. Add `references.bib` only after each
bibliographic record has been verified.

## Build

```powershell
Set-Location paper/en
pdflatex -interaction=nonstopmode -halt-on-error main.tex

Set-Location ../zh
xelatex -interaction=nonstopmode -halt-on-error main.tex
```

The repository must not contain raw or transformed trajectories, coordinates,
timestamps, identifiers, checkpoints, row-level predictions, or unreviewed
empirical results. Public builds use only the included manuscript sources and
approved aggregate material.

## NEX326 aggregation

`scripts/aggregate_nex326.py` validates and summarizes the frozen 22-arm,
36-execution RunRecord matrix. `scripts/aggregate_nex326_replicates.py` then combines
its independently validated per-seed summaries without issuing an inferential verdict.
For the approved PIRC-20 core scope, pass `--scope-policy` to the single-seed
aggregator. It then requires exactly the 28 executions remaining after Arms 13, 17,
and 22, verifies the scoped PSDE manifest and policy SHA-256, and records both in the
summary. Cross-replicate aggregation accepts 28 executions only when the batch and
every per-seed summary bind that same scope hash; the unscoped path still requires all
36 executions. The cross-seed calibration field is candidate-minus-reference absolute
HDR90 error from the 90% target; raw coverage direction is never treated as an
improvement signal.
Arm 17 terrain is compared with its registered Full reference only when both records
provide the same evaluation segment-ID fingerprint; otherwise it remains
`requires_coverage_matched_reference`. Prediction artifacts are still checked for
identical segment IDs and targets before paired bootstrap intervals are produced.

The supplemental four-dimensional benchmark stays outside that frozen arm matrix.
Aggregate its compact PSDE receipts and paired contrasts with:

```console
python scripts/aggregate_nex326_phase_space.py \
  --receipts /path/to/phase_space_*_receipt.json \
  --contrasts /path/to/phase_space_*_contrast.json \
  --uncertainties /path/to/phase_space_*_segment_bootstrap.json \
  --output .local/nex326-phase-space-aggregate
```

The phase-space aggregator rejects mixed cohorts or protocols, missing receipt
coverage, tampered manifest bindings, and inconsistent paired summaries. It writes
model and contrast CSVs plus a hash-bound summary. The output remains
`exploratory_only/not_assessed`; sampling-seed repeats over one fitted cohort and one
evaluation set are not treated as independent scientific replications.
When supplied, paired-segment uncertainty files are checked against both receipt
manifest hashes and the exact contrast-file hash before their intervals are emitted.

## Shared research evidence

`scripts/pirc25/aggregate.py` consumes the authorized, hash-bound shared-runtime
bundle. Missing/failed cells stay in the expected denominator; seed repeats are
averaged within independent blocks. Mixed units/protocols are rejected. Paired
intervals are unavailable with fewer than two complete independent blocks.
Formal comparisons require a frozen comparison plan and qualified inputs.
Comparison summaries are keyed by `(arm_id, stratum_id)`. Exact
`comparison_dimensions` (including horizon/region/scenario and explicitly
registered extension axes) are preserved in aggregate rows, CSV, and evidence
claims. Seeds are averaged only within a block and stratum; paired comparisons
never pool different horizons. Absent arms and incomplete blocks produce explicit
no-pair dispositions. Evidence claim sources contain only contributing complete
blocks. Legacy dimensionless bundles use one empty stratum; re-export from the
runtime to recover dimensions lost by an older exporter. Budget arm IDs do not
change. New runtime exports additionally bind dimensions to the hashed registered
cell, and formal validation checks them against the admission receipt.

New runtime bundles also freeze all-attempt reservation/settlement sources.
The aggregator validates source hashes, identities and charge policy, rejects
duplicate sources, and retains failed/retried resource use in each stratum's
cost summary. Quality can exclude incomplete blocks without erasing their costs.
CSV and evidence claims carry the same `slot-ms` charged/reserved/measured values;
unknown measured cost remains null and legacy absent costs remain unavailable.
These are frozen export costs, not a query of the runtime's current arm balance.

`--formal` also validates each successful cell's `pirc25-admission-v1` receipt:
spec/cell/attempt identity, protocol and execution grant, actual input exposure
events, frozen preregistration/history, package/upstream/command bindings, and
the referenced qualification checks. A `qualified` string alone is rejected.
Foreign frozen models carry their own source protocol and consumer authorization.
The trusted expected bundle hash remains required; internal hashes do not prove
the truth of arbitrary operator-imported scientific attestations. Runtime inputs
and registration APIs are documented in PSDE's `docs/pirc-38-shared-engineering.md`.
Restricted attachments remain restricted when imported back into the runtime,
even when their parent cells are synthetic. Do not publish these local bundles
as public paper data merely because their aggregation succeeds.

```console
python scripts/pirc25/aggregate.py /absolute/runtime/bundle.json --expected-hash BUNDLE_HASH --output /absolute/runtime/evidence-v1
python -m pytest tests/test_shared_evidence.py -q
```

Output must stay outside Git. The immutable package contains `aggregate.json`,
`metrics.csv`, `PaperEvidenceIndex.json` and a file-hash manifest. PSDE's read-only
UI imports these exact bytes. This adds no scientific manuscript claim, executes
no experiment and reads no trajectory data.

## CI/CD and releases

Pull requests to `main` run validation only. When one is merged, GitHub pushes
the merge commit to `main`; that push automatically compiles both manuscripts
and creates a new immutable GitHub Release. It never publishes from a
`pull_request` event. Each Release contains only the English PDF, Chinese PDF,
and `SHA256SUMS`; the workflow refuses to replace an existing tag or Release.
For the full trigger and verification details, see [CI_CD.md](CI_CD.md).
