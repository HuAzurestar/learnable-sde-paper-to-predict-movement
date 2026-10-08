# Public PIRC-17 review projection — not the complete local manuscript

Read the public copies: [English](en/public-review.pdf) and
[中文](zh/public-review.pdf). `public-review-build.json` binds the strict build-source revision,
source hashes and exact published PDF hashes. Its original relative build
paths are mapped to published filenames in `published_pdf_files`.
The manifest records the actual inspected pages and route-input check. This is compilation
and public-copy checking, not full manuscript/scientific acceptance.

Local manuscript source revision:
`54d8a08b9adbdf8f125dd4857ad9e295e64291eb`.
Current complete local PDFs were delivered at
`9440f746b4e90e5b9a3cb976732f26ee7a0102d7` (English 88 pages,
Chinese 85 pages); the public copies are English 81 / Chinese 78 pages.
The previous analysis-stage delivery `090de63459a95ffb966701f597cf2b0cb5de9767`
is historical; its public build proof is retained separately in
`public-review-analysis-stage-build-v1.json`.
The preceding host-interruption delivery `fb859f81c50bd2b60c492740285571af6b1a8829`
is also historical; its public proof remains in
`public-review-runtime-interruption-build-v1.json`.
The earlier `42906141d41174ecb0ba43d3c47e31e6b65777b4` delivery
(English 85 / Chinese 82 pages) is historical, not the current revision.
The complete local PDFs are **not** uploaded because they embed
local-only real-route illustrations.

The current main manuscripts disclose a confirmed host-interrupted original
cold-runtime trial (English page56 / 中文52页). The exact original2315.9963217s
elapsed record, original cost and five-trial denominator remain unchanged.
The host-event gap is30min43s, not a value to subtract for a corrected latency.
`runtime-interruption-disclosure-v1.json` contains anonymous bound scalars,
not maps, raw routes, a replacement trial or a speedup/accuracy certification.
The affected trial and summaries cannot establish uninterrupted latency;
other trials are not thereby certified interruption-free. This update does
not perform a new fit, forecast, score, resampling or map query.

The additional bound partial census `runtime-interruption-census-v1.json`
covers153 of the original165 timing records, with all153 source digests and
15 subject/condition denominators retained. It additionally flags the
original all-terrain cold repetition3 record (3000.4638613s) under the same
later-clock mapping. Host clock-change events exist, so mappings do not
certify original endpoint UTC or unflagged trials. Both affected cold
subjects and cost summaries retain this caveat; no record is subtracted,
excluded or replaced. Only scalar metadata was read; predictions/maps were
not loaded. This partial census is not the complete final runtime audit.

This branch is a public-base-parent snapshot, not an upload of private
implementation history. The running science branch and experimental parameters
are unchanged. The paper branch includes the saved-score comparison below.
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

Both PDF jobs retain their historical `paper/en` and `paper/zh` builds and
also compile the current `paper/pirc17/{en,zh}/main.tex` manuscripts.
The added steps use the original strict `build_pirc17.check_log` checker:
unresolved references/citations, missing characters and overfull boxes fail.
Current PIRC-17 CI PDF artifacts are named `pirc17-en-<sha>` and
`pirc17-zh-<sha>`; historical `paper-en-<sha>`/`paper-zh-<sha>` artifacts
remain distinct. A passing PDF job is not a scientific audit or permission
to release the withheld routes, and does not make the complete evidence gate
pass. The committed public-review PDFs remain bound by their original exact
source/build manifest; workflow changes alone do not rebuild that evidence.

Public pre-existing aggregate statistics and non-route diagrams are retained.
No raw GPX, positions, fitted checkpoints, private maps or unpublished
route illustrations are uploaded. No new fit, forecast, particle scoring or map
query is run for this projection. Saved-center/target distance arithmetic is
explicitly identified below; it is not another particle-score computation.

## Pending experiment delivery

At 2026-10-08 19:21 Hong Kong time: original science 11,015 successful,
5 failed and 0 runnable out of 11,020; common scores 11,368 rows/58 groups;
original auxiliary work 235/261 successful, 26 remaining. These are workload
dispositions, not 11,020 independent participants or final accepted effects.
The single independent saved-output audit, final aggregate export, original
16 tables/16 figure groups and final numeric manuscript integration remain
pending. Audited aggregate results will be added to this PR when available.

The opening now explicitly distinguishes terminal scientific predictions,
closed scoring and completed original paired/mechanism analysis from pending
auxiliary trials and independent output audit. The inventory table in
Appendix A.18 reconciles all 11,368 score slots:
8,120 method forecasts plus 2,900 terrain forecasts, 290 same-grid references
and 58 inertial paths. Five failed scientific forecasts remain failed slots,
not zero errors. The 11,368 slots are not independent observed participants.
`terminal-score-inventory-v1.json` binds this count-only derivative to the
complete hash-checked common-score index; it does not certify raw outputs.

## New saved-score manuscript comparison

Both manuscripts now include two tables comparing the original deterministic
inertial reference with Full on all 46 prespecified primary blocks. The 46
reference paths are not replicated: five Full seeds are averaged within each
block before equal-weight averaging across blocks (230 Full forecasts).
The aggregate projection and read-only rendering scripts are included.

Weighted ES is 824.73 m for inertial and 477.85 m for Full; lower is better.
Inertial has lower mean ES at 1 and 5 minutes; Full has lower mean ES at 15 and
30 minutes. The text distinguishes distributional ES from mean-path ADE/FDE.
These are existing-score descriptive means, not a new confidence interval,
significance test, independently audited superiority claim or evidence against
unexecuted external models. Original target tolerance and validation-based
delta remain unchanged. No new experiment was run.

Opening this review does not authorize merge, paper release, route publication,
new large experiments or scientific acceptance. The historical release
entrypoints are intentionally unchanged; they are not this manuscript.

## Saved mean-position error at each target slot

A new table distinguishes distributional ES from the mean-position error at
the four original target slots. It uses all 690 existing Full/GMM/dt300
primary forecasts and 46 deterministic reference paths on the same 184 saved
target positions. Every row reproduces original ADE/FDE within roundoff.
The published description contains anonymous aggregate values and hash
bindings, not targets, centers, coordinates, clocks, raw routes or paths.
The reader opens only closed saved-score JSON and the original bound input
context, never particle arrays, fitted models, raw GPX or maps.

Full's mean-position errors are 73.77/332.31/812.26/1326.09 m at the nominal
1/5/15/30-minute slots; inertial errors are 31.17/237.93/934.03/2095.78 m.
The short/long-horizon reversal is retained. GMM's descriptive point errors
are slightly lower than Full's; dt300's are higher at every slot despite
its lower aggregate ES. These are not new per-horizon significance tests,
a ranking of all28 methods, independent output audit or deployment claims.
Original saved scores, target tolerance, parameters and failures are unchanged.

## Current terrain completeness versus the historical census

Section 6 now explains the closed primary terrain status, rather than treating
the earlier 160/131 missing-row snapshot as current: overall/LOO has 1380
required rows, 1379 successes, one failure and none missing; LIO has 1150
required rows, 1148 successes, two failures and none missing. Their 230
baseline rows are shared, giving 2300 distinct primary forecasts, not 2530
independent observations. The anonymous count-only projection and exact
original family/failure bindings are included.

Both entire primary terrain families remain unavailable under the unchanged
complete-pair policy. No successful-subset effect or interval is substituted;
unavailability does not establish benefit, harm, zero effect or equivalence.
Auxiliary completion and audit do not themselves replace failed forecasts.
The historical census tables, scientific tables/figures/equations and every
previous claim-ledger root are preserved. No forecast arrays or private routes
were opened for this count-only correction; it is not the original independent
saved-output audit, evidence-card acceptance or full completion.

## Completed original analysis, pending independent audit

Section 5.4 (English 38 / Chinese 35) adds one analysis-state table alongside
all unchanged historical scientific tables. The original once-only registered
analysis returned an immutable result, not independent audit approval.
`analysis-stage-summary-v1.json` is a hash-bound anonymous scalar projection
covering all three modes and 21 family dispositions, including the four whole
unavailable families. Private case IDs, routes and output arrays are absent.

The 21 primary method contrasts retain their original exact estimates,
simultaneous intervals and Holm values: 14 practical-equivalence states and
7 inconclusive states, with no practical-benefit or harm state. Equivalence
requires the original strict interval/decision conditions, not merely a
non-significant zero test. GMM's interval lies inside the fixed
plus/minus 41.100259 m band; dt300's interval excludes zero but crosses its
practical boundary. The two identical d2 aliases remain inconclusive because
zero development SD is not planning-power evidence; dt600 likewise retains
insufficient planning power.

All 28 original mechanism gates per mode were computed/passed. Weak
Euler/EM nonnegative-error checks do not bound accuracy, and every primary
resolution-invariant verdict remains inconclusive. These are pending-audit
algorithm-recorded states, not independent verification, a ranking of all
models, final human acceptance or justification for new large experiments.
