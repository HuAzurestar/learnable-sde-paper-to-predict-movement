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

## CI/CD and releases

Pull requests to `main` run validation only. When one is merged, GitHub pushes
the merge commit to `main`; that push automatically compiles both manuscripts
and creates a new immutable GitHub Release. It never publishes from a
`pull_request` event. Each Release contains only the English PDF, Chinese PDF,
and `SHA256SUMS`; the workflow refuses to replace an existing tag or Release.
For the full trigger and verification details, see [CI_CD.md](CI_CD.md).
