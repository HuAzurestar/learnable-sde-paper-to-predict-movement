# Public PIRC-17 review projection — not the complete local manuscript

Read the public copies: [English (78 pages)](en/public-review.pdf) and
[中文（75页）](zh/public-review.pdf). Both passed the existing strict bilingual
build checks. `public-review-build.json` binds the build-source revision,
source hashes and exact published PDF hashes. Its original relative build
paths are mapped to published filenames in `published_pdf_files`.
Four actual pages were inspected: English 1/51 and Chinese 1/48.
No route-map input appears in the TeX recorder inputs. This is compilation
and public-copy checking, not full manuscript/scientific acceptance.

Local source and full evidence revision:
`378d5088a9a19e23458a54fe7ed66e9b89eb847a`.
Existing complete local PDFs were delivered at
`42906141d41174ecb0ba43d3c47e31e6b65777b4` (English 85 pages,
Chinese 82 pages). Those PDFs are **not** uploaded because they embed
local-only real-route illustrations.

This branch is a public-base-parent snapshot, not an upload of private
implementation history. The local science/paper branches are unchanged.
The original 42-item HTML review has SHA-256
`457688e8ba81c88b6c9f71f22da8f457fa2245809e1b1368c5e0aef5b824b65d`.
`review-response-v1.json` and `claim-ledger.json` describe the **original
local revision**, not newly verified evidence for this public projection.
Their statuses remain 20 draft checked, 14 partial, 7 awaiting original
results, 1 permission unverified and **0 finally accepted**.

## Withheld material

This projection omits the twelve route-map PNG/PDF files, their
`figures/case-horizons.json` case-level diagnostics and the two original
bilingual PDFs. The real-map subsection is replaced by an explicit
withholding notice. No synthetic case is invented. Figure-level and
case-level review bindings cannot be verified from this public branch.
The original map-dependent tests remain visible for reviewer context and
cannot pass without their withheld local inputs; do not interpret that as
loss of local experiment results or weaken the tests to manufacture a pass.

CI installs `requirements-test.txt` for the existing numerical, PDF and image
test imports. The complete original pytest command remains unchanged; missing
local route inputs remain explicit failures, not exclusions or acceptance.

Public pre-existing aggregate statistics and non-route diagrams are retained.
No raw GPX, positions, fitted checkpoints, private maps or unpublished
route illustrations are uploaded. No new fit, forecast, scoring or map
query is run for this projection.

## Pending experiment delivery

At 2026-10-08 10:22 Hong Kong time: original science 11,015 successful,
5 failed and 0 runnable out of 11,020; common scores 11,368 rows/58 groups;
original auxiliary work 169/261 successful, 92 remaining. These are workload
dispositions, not 11,020 independent participants or final accepted effects.
The single independent saved-output audit, final aggregate export, original
16 tables/16 figure groups and final numeric manuscript integration remain
pending. Audited aggregate results will be added to this PR when available.

Opening this review does not authorize merge, paper release, route publication,
new large experiments or scientific acceptance. The historical release
entrypoints are intentionally unchanged; they are not this manuscript.
