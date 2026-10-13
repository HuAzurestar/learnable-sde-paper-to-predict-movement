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
Affine analytic receipts additionally require the managed qualification worker's
actual result, admission, resource contract, start/native-stop/settlement and
completion events, same cumulative arm, explicit source-consumer/export grant,
and preregistered request/model/source-bound numerical policy. The independent
stdlib reader checks bounded saved dyadic intervals and recomputes their widths,
signed grid bias, scaled transition growth, current scalar roundoff and absolute
error upper. Target artifact bytes and metric/forecast provenance are bound;
model error remains unknown. It does not replay matrix exponentials/CDFs or
authenticate arbitrary self-rehashed journals: the authorized export's expected
bundle hash remains the trusted transport boundary.

For a single analytic cell, run `python scripts/pirc25/validate_analytic.py
bundle.json --expected-hash <authorized-bundle-hash>` to verify admission only.
This does not produce a comparison, statistical adjudication or model approval.
The existing `aggregate.py --formal` comparison-plan requirements are unchanged.
Missing numeric proof or target bytes cannot fall back to generic operator
checks; other propagation methods cannot borrow an affine analytic proof.

For a settled affine mixture target, use `python scripts/pirc25/validate_mixture.py
bundle.json --expected-hash <authorized-bundle-hash>`. Its separate stdlib reader
checks actual pilot settlement/native-stop order before protected reads, source
consumer/export permission, full frozen mixture/request/model/policy identity,
and the current retained functional and lineage. It recomputes direct retained
error against the saved Euler law and total error against the saved continuous
law, along with reference width, signed time bias, scaled growth and operation
caps. It never borrows Gaussian approval or replays a numerical engine. Closure,
implementation roundoff and model error remain unknown/inseparable, not zero.
This verifies recorded admission of one functional only, not a full-distribution
claim, statistical comparison, scientific model approval or arbitrary journal
authenticity. Failed rows remain in the expected-cell denominator; the existing
formal comparison-plan requirements are unchanged. Missing mixture proof cannot
fall back to a generic operator pass.

For a settled affine eight-point cubature target, use
`python scripts/pirc25/validate_cubature.py bundle.json --expected-hash
<authorized-bundle-hash>`. Its dedicated stdlib reader validates the actual
cubature pilot's policy, own source/worker/cost/read order and saved continuous
and Euler certificates, then checks the current target scalar and method
diagnostics. Missing cubature proof or an analytic substitute cannot fall through
generic admission. Mathematical finite-grid Gaussian closure is identified
only for the declared affine law; floating implementation error and continuous
grid bias remain separately bounded, model error unknown. This is recorded
admission verification, not nonlinear or scientific model qualification,
independent-block inference or statistical adjudication. Failed/missing rows
stay in the expected-cell denominator; comparison-plan requirements are unchanged.

For owner-admitted independent path Monte Carlo or unnormalized IS targets, use
`python scripts/pirc25/validate_paths.py bundle.json --expected-hash
<authorized-bundle-hash>`. The separate stdlib reader checks the settled own-path
pilot, source-consumer/export permission and frozen original-arm policies. Source
and target must share the same physical law, grid and functional but have distinct
request, seed and coupling identities (not an independence theorem). Saved final
statistics reconstruct the actual target output and its sampling/ESS checks;
bounded same-law reference intervals are reused without sampler or matrix/CDF
replay. Source PASSED cannot promote a current FAILED output. The CLI reports
current passed and failed counts separately, retaining completed numerical
failures and noncompleted rows in the expected-cell denominator. Outputs with
FAILED or unresolved current classification are excluded from
complete paired-block aggregation and adjudication, without erasing their
computational SUCCEEDED status or cost; CSV records both counts separately.
Observed scalar distance is not a stochastic coverage or predictive-distribution bound; sampler
roundoff and model error remain unknown. This is admission verification only,
not a full study, statistical comparison or scientific model approval. Missing
path proof cannot fall back to generic operator or Gaussian approval.

New formal evidence also requires an immutable upstream snapshot and operator
acceptance catalog bound to the package and pre-read per-study cutover. The
stdlib-only independent `scripts/pirc25/upstream.py` checks complete cell scope,
exact selected accepted metadata/schema/hash/size/license declarations, recorded
physical size/time, explicit PIRC-22 cutover/zero-final-eval selection, consumer
identity and original publication/validation events before input exposure.
A ready flag or recomputed enclosing checksum cannot replace those bindings.
No runtime/provider is imported and original metadata/data roots are not opened.
Missing new evidence is rejected for formal claims, not backfilled after reads;
legacy nonformal bundles remain readable. Explicit old public recipe bindings
are optional additional checks, never a substitute for the mandatory snapshot.
Foreign frozen models carry their own source protocol and consumer authorization.
For heterogeneous adapters, `admission.cell_packages` freezes an explicit
`pirc25-cell-packages-v1` table with exactly one `cell_hash`/`package_hash`
binding for each executable registered cell. Optional model-source grant/version
and protocol references belong to that same entry, not another cell or a default.
`scripts/pirc25/admission_selection.py` independently checks exact coverage,
unique identities, unavailable declarations, the receipt's entry/table hashes,
selected package content and common mode. Tables cannot coexist with default
package/model references or override common protocol, execution grant or upstream
authority. Matrix/table counts are bounded to10,000 and table metadata to4 MiB;
there is no lookup or fallback. Explicit legacy single-package admission remains
readable. These checks verify recorded bindings, not scientific eligibility or
new authority. Standalone aggregation remains descriptive even with `--formal`.
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

Standalone packages carry `qualification: descriptive`, including when `--formal`
validates qualified source admission. They are inputs to the runtime's budgeted
`compare` command, not formal statistical evidence. Formal outputs require the
managed adjudication and its settled `ComputationReceipt.json`; removing their
proof fields cannot turn a rehashed descriptive package into formal evidence.

## CI/CD and releases

Pull requests to `main` run validation only. When one is merged, GitHub pushes
the merge commit to `main`; that push automatically compiles both manuscripts
and creates a new immutable GitHub Release. It never publishes from a
`pull_request` event. Each Release contains only the English PDF, Chinese PDF,
and `SHA256SUMS`; the workflow refuses to replace an existing tag or Release.
For the full trigger and verification details, see [CI_CD.md](CI_CD.md).
