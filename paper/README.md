# Paper sources and review manuscripts

## Source organisation

Current PIRC-17 entry points are `pirc17/en/main.tex` and `pirc17/zh/main.tex`,
plus each language's `supplement.tex` and `audit-notes.tex`. Older complete
manuscripts and superseded layout fragments are now in the
[dated review archive](pirc17/archive/2026-10-16/README.md), with an exact
[original-path/SHA256 index](pirc17/tex-archive-index.tsv). They are retained
pending owner inspection, not deleted. Current templates and versioned
numerical evidence packages remain in place. Historical tests resolve
archived or pinned Git bytes rather than forcing old chapters into current
source directories. The manuscript/PDF content is unchanged by this move.

## Current PIRC-17 manuscript: reader-v10 conclusions and body layout

The main body uses plain numbered pages instead of repeated section running
heads, and finishes result floats before Discussion. Figure 5 is included
once. The sole ordered list in the main paper gives six experimental
conclusions: horizon-dependent CV/HSM ranking, RDM comparison, observation
interval, training/adaptation, region reliability and descriptive terrain
findings. Inference qualifications and declarations remain outside that list.

| Language | Main paper | Scientific supplement | Audit record |
| --- | --- | --- | --- |
| Chinese | [Current paper](pirc17/revision46-review-v10/zh/main.pdf) | [Scientific supplement](pirc17/revision46-review-v10/zh/supplement.pdf) | [Audit record](pirc17/revision46-review-v10/zh/audit-notes.pdf) |
| English | [Current paper](pirc17/revision46-review-v10/en/main.pdf) | [Scientific supplement](pirc17/revision46-review-v10/en/supplement.pdf) | [Audit record](pirc17/revision46-review-v10/en/audit-notes.pdf) |

[Build provenance](pirc17/revision46-review-v10/build-manifest.json) binds
clean source `67912a0c0295f3d6e751cc7aec35a44403014975` and all 76 actual
inputs. [Scoped review and verification](pirc17/reader-v10-editorial-record.md)
records fresh actual Astra High ACP review of public/local PDFs. No new fit,
forecast, score, graph or inference was introduced; the v9 figure assets
and all prior versions remain unchanged.

## Previous reader-v9 terrain factors and unified names (superseded)

Model design, fitting and forecasting now form one subsection with three
nested parts and the full HSM/RDM names. The separate map-factor subsection
defines selected road, river, land-cover and surface inputs, with two main
tables: actual expressions and the ten base/all/LOO/LIO configurations.
Road/river direction points towards the nearest feature, not along it;
river has no selected direct history-velocity product. Surface/history
projections and cover/road products, their dependencies, masks, dimensions
and refitting scope are explicit. The ordinary solar proxy is not terrain.

| Language | Main paper | Scientific supplement | Audit record |
| --- | --- | --- | --- |
| Chinese | [Current paper](pirc17/revision46-review-v9/zh/main.pdf) | [Scientific supplement](pirc17/revision46-review-v9/zh/supplement.pdf) | [Audit and identity crosswalk](pirc17/revision46-review-v9/zh/audit-notes.pdf) |
| English | [Current paper](pirc17/revision46-review-v9/en/main.pdf) | [Scientific supplement](pirc17/revision46-review-v9/en/supplement.pdf) | [Audit and identity crosswalk](pirc17/revision46-review-v9/en/audit-notes.pdf) |

The current scientific source graph uses 19 newly rendered versions of the
same original figures, not additional experiments or figures. Main papers
retain five figures and now have six tables (two added definition tables);
each scientific supplement retains 17 figures and all 50 tables.
HSM/RDM/CV and descriptive variant names are consistent across figures and
table display projections. Original saved IDs, data keys and archived assets
remain unchanged and are explained in the audit record, not used as current
model names. The owner-only assembly applies the same policy to case text;
its six original map files remain private and unchanged.

Rerender from the original plotting functions and unchanged public aggregates:

```console
python -m scripts.render_pirc17_reader_v9 --output-dir <fresh-external-directory>
```

The output contains 19 PDF/PNG pairs, two terrain tables, 20 supplementary
TeX display projections, four unchanged numeric rows with current labels,
and a [presentation manifest](pirc17/figures/reader-v9/manifest.json).
Repeated runs are byte-identical across all 62 outputs. Scientific line,
scatter and heatmap artist data are hashed before/after renaming and remain
identical; old renderers are preserved for provenance. The current
[name policy](../scripts/pirc17_display_names.py) is shared by plotted text,
tick formatters, table labels and owner-only case assembly. The
[terrain contract](pirc17/reader-v9-terrain-contract.json) binds definitions
to actual selected feature/code/configuration identities.

The [build manifest](pirc17/revision46-review-v9/build-manifest.json),
[review record](pirc17/reader-v9-editorial-record.json) and
[complete regression comparison](pirc17/reader-v9-regression-check.json)
record the actual checked source, PDFs, scope and outcomes. Rebuild all six
public documents with `scripts/build_pirc17_revision46.py --output-dir
<fresh-external-directory>`. No scientific fit, forecast, particle score,
inference rule, map query or private publication was added. Formal declarations
and human acceptance remain separate from this editorial revision.

## Previous reader-v8 code-verified methods (superseded)

The main paper now explicitly separates baselines and shared model structure,
training groups and parameter estimation, and forecasting/component updates.
Table 1 compares CV, HSM and RDM. HSM groups whole segments by net-heading
rank; RDM groups individual transitions by pooled-regression residual direction
and refits complete component regressions to the original rate targets.
HSM retains the initially drawn component for each path; RDM independently
redraws every 60 saved seconds, allowing repeats, not cyclic rotation or
redrawing at each 5-second integration step. The comparison changes both
grouping-based fitting and prediction-time persistence; it cannot isolate
the benefit of either mechanism. HSM/RDM are paper-specific names for two
complete procedures in one model family, not unrelated model architectures
or simply labels for two training algorithms. Full01 is not terrain base.

| Language | Main paper | Scientific supplement | Audit record |
| --- | --- | --- | --- |
| Chinese | [20-page paper](pirc17/revision46-review-v8/zh/main.pdf) | [78-page supplement](pirc17/revision46-review-v8/zh/supplement.pdf) | [15-page record](pirc17/revision46-review-v8/zh/audit-notes.pdf) |
| English | [21-page paper](pirc17/revision46-review-v8/en/main.pdf) | [80-page supplement](pirc17/revision46-review-v8/en/supplement.pdf) | [16-page record](pirc17/revision46-review-v8/en/audit-notes.pdf) |

Read Chinese pp4–6 or English pp4–7 for the clarified methods.
The [method contract](pirc17/reader-v8-methods.json) records exact code anchors;
the [build manifest](pirc17/revision46-review-v8/build-manifest.json) binds
clean source0ce2ecbf972e402607968aef956faf04e3c9fe5d and 73 actual source inputs.
The [review receipt](pirc17/reader-v8-editorial-record.json) records independent
code checks and the final bounded ACP review. Rebuild using the existing
`scripts/build_pirc17_revision46.py --output-dir <fresh-external-directory>`.
Twelve public/local documents strict-build with no text outside page bounds;
59 public companion links resolve. All 53 selected focused checks pass.
The [complete regression comparison](pirc17/reader-v8-regression-check.json)
records 1024 PASS/25 FAIL/2 ERROR with no new failure/error identities,
not a green whole suite. Five existing figures, all numeric evidence,
50 supplementary tables and inference rules remain unchanged. One new
non-empirical method-comparison table brings the main table count to four.
Local ZH28/EN29-page bodies retain the same six private map files, not published.
No new experiments, forecasts, scores, figures or inference were performed.
Formal declarations and human acceptance remain separate.

## Previous reader-v7 direct conclusions (superseded)

The active wording goal is implemented in both languages. C1 directly says
CV is better at 1/5 saved minutes and HSM-SDE at 15/30, with better defined as
lower average ES. C2 names the main HSM-SDE comparator instead of requiring a
reader to interpret Full01. Observation interval and training/adaptation
now have separate conclusions. C4 explains the nominal 90% circle from 512
simulated positions, empirical actual-target coverage, centre error and area,
including why city-sized circles and biased centres can be unhelpful.
C5 directly states the four current-terrain results and keeps suspected
terrain-handling problems as an unverified explanation, not a proven cause.
Inference qualification is labelled separately from empirical findings.

| Language | Main paper | Scientific supplement | Audit record |
| --- | --- | --- | --- |
| Chinese | [19-page paper](pirc17/revision46-review-v7/zh/main.pdf) | [78-page supplement](pirc17/revision46-review-v7/zh/supplement.pdf) | [15-page record](pirc17/revision46-review-v7/zh/audit-notes.pdf) |
| English | [20-page paper](pirc17/revision46-review-v7/en/main.pdf) | [80-page supplement](pirc17/revision46-review-v7/en/supplement.pdf) | [16-page record](pirc17/revision46-review-v7/en/audit-notes.pdf) |

See Chinese p7 for the metric explanation and p16 for the direct conclusion
paragraphs. Keep same-language PDFs together for companion links.
The [build manifest](pirc17/revision46-review-v7/build-manifest.json) binds
clean reviewed source307f96286cb196a455793949161155ea184286a9 and exact inputs/PDFs.
Rebuild with `scripts/build_pirc17_revision46.py --output-dir <fresh-external-directory>`.
The [claim contract](pirc17/reader-v7-claims.json) records every requested
statement and the [review receipt](pirc17/reader-v7-editorial-record.json)
records a fresh actual gpt-6-astra/high/read-only ACP 9-call review, with no
substantive P1/P2 omission against this wording goal. Actual EN/ZH metric,
results and conclusion pages were checked; this was not another scalar audit.

All 12 strict public/local builds and page bounds and 59 companion links pass;
53 focused checks pass. The [regression comparison](pirc17/reader-v7-regression-check.json)
reports 1017 PASS/25 FAIL/2 ERROR with no new failure/error identities, not a green
whole suite. Original five figures/three tables, all 50 supplement tables,
numeric evidence and inference rules are unchanged. Local ZH 27/EN 28-page
bodies retain six unchanged private maps, not published. Formal declarations
and human acceptance remain distinct from this completed wording objective.

## Previous reader-v6 terrain evidence (superseded)

The terrain branch now has substantive results, not only an unavailable-
inference statement. A new ten-configuration table and three-panel figure
describe existing saved ES, mean-position error, coverage and area. The
original grid has2297 successes/3 failures out of2300slots; the main fair
configuration comparison uses the same43 execution-complete blocks in all
ten configurations (five seeds each). This is post-hoc selected-subset
description, not the full46-block estimand or the registered family inference.
Larger45/46-block paired sensitivities and original failure counts remain.

| Language | Main paper | Scientific supplement | Audit record |
| --- | --- | --- | --- |
| Chinese | [18-page paper](pirc17/revision46-review-v6/zh/main.pdf) | [78-page supplement](pirc17/revision46-review-v6/zh/supplement.pdf) | [15-page record](pirc17/revision46-review-v6/zh/audit-notes.pdf) |
| English | [19-page paper](pirc17/revision46-review-v6/en/main.pdf) | [80-page supplement](pirc17/revision46-review-v6/en/supplement.pdf) | [16-page record](pirc17/revision46-review-v6/en/audit-notes.pdf) |

The [build manifest](pirc17/revision46-review-v6/build-manifest.json) binds
the six PDFs to clean reviewed source5a00b776fa98f8d18698b4605ed7bc3c342162f7.
Keep same-language PDFs together for companion links. Existing model/task
exposition, HSM-SDE/RDM-SDE/CV names and four method conclusion groups remain.
Terrain adds a separate RST-organised question/evidence/interpretation/limit
branch, documented in the [argument record](pirc17/reader-v6-argument.json).

On the common subset, all-terrain raises ES26.98m and FDE39.00m versus its
history-only base; road-group contrasts show score costs, river-only changes
direction across horizons, land-cover-only has a small favourable mean, and
30-minute90%coverage remains40.47–52.09%. These concern fitted configurations,
not causal factor effects or significant general terrain benefit/harm.

The anonymous [aggregate](pirc17/terrain-description-v1/summary.json),
[CSV table](pirc17/terrain-description-v1/configurations.csv) and
[figure](pirc17/figures/terrain-description-v1/terrain-evidence.pdf) are public.
Reproduce the new plot/table without private inputs:

```console
python -m scripts.plot_pirc17_terrain --source paper/pirc17/terrain-description-v1/summary.json --output-dir <fresh-external-directory>
```

Private-cache scalar aggregation is a separate explicit command documented
by `python -m scripts.describe_pirc17_terrain --help`; it never loads model
or forecast arrays. New descriptive summaries are not new particle scores.
The original full-family verdict remains unavailable. Rebuild manuscripts
with `scripts/build_pirc17_revision46.py --output-dir <fresh-external-directory>`.

A fresh actual gpt-6-astra/high/read-only ACP review completed11calls,
independently checked original saved-score scalar arithmetic and selected
actual EN/ZH terrain pages, and found no substantiveP1/P2 blockers. Host
verified exact model/effort through ACP options and persisted turn_context;
the reviewer could not query its model independently. The
[review receipt](pirc17/reader-v6-editorial-record.json) records that distinction.
All12 strict builds/page bounds and58links pass;45focusedchecks pass;
[full regression](pirc17/reader-v6-regression-check.json)1009PASS/25FAIL/2ERROR
introduces no failure/error identities, not a green full-suite claim.
Local bodiesZH26/EN27 retain six unchanged private maps and are not uploaded.
Five main figures/three tables now include one new terrain composite/table;
the original four figures/two tables and all50supplementtables remain.
No new fit, forecast, raw-array rescore, bootstrap or private publication.
Real declarations and human acceptance remain separate from editorial delivery.

## Previous reader-v5 delivery (superseded)

The bilingual paper now follows one reading line: research object and task,
model construction, evaluation criteria, horizon-dependent utility, grouped
design choices, region reliability, and four bounded conclusions. Mechanism-
based names replace generic prose labels: HSM-SDE is the heading-stratified
mixture reference (registered Full01), RDM-SDE is the residual-direction
mixture variant (registered GMM, not conventional EM), and CV is deterministic
constant-velocity extrapolation (registered Inertial/I). Original labels in
retained figures/tables and numbered comparison controls remain traceable.

| Language | Main paper | Scientific supplement | Audit record |
| --- | --- | --- | --- |
| Chinese | [15-page paper](pirc17/revision46-review-v5/zh/main.pdf) | [78-page supplement](pirc17/revision46-review-v5/zh/supplement.pdf) | [15-page record](pirc17/revision46-review-v5/zh/audit-notes.pdf) |
| English | [16-page paper](pirc17/revision46-review-v5/en/main.pdf) | [80-page supplement](pirc17/revision46-review-v5/en/supplement.pdf) | [16-page record](pirc17/revision46-review-v5/en/audit-notes.pdf) |

Keep each language's three PDFs together for companion links. The
[build manifest](pirc17/revision46-review-v5/build-manifest.json) binds the
six PDFs to clean reviewed source cb980cd8975f473c611a32048d9b111ffde4bfdb
and exact input/PDF hashes. Rebuild with
`scripts/build_pirc17_revision46.py --output-dir <fresh-external-directory>`.
The [argument record](pirc17/reader-v5-argument.json) maps sections and figures
to four conclusions and qualifications. This is a coarse RST-inspired
editorial check, not formal EDU annotation or an additional scientific method.

The conclusions concern conditional long-horizon utility relative to CV;
promising RDM means without confirmed superiority; larger observed interval
effects than examined training/adaptation mean changes against their own
controls, not a direct cross-class test; and unestablished reliable long-
horizon disks. Component construction, observation interval, training
initialisation and parameter adaptation are separate design categories.
Original RQ1/RQ2 and inference rules remain unchanged; terrain inference is
still unavailable. No new figure or scientific execution was performed.

A fresh actual read-only gpt-6-astra/high ACP review completed11 focused
calls and found no P1/P2 blockers to this editorial deliverable. The
[review receipt](pirc17/reader-v5-editorial-record.json) records its bounded
scope. Twelve strict public/local documents and page-boundary checks pass,
58 companion links resolve, and six local map hashes match the earlier
version. Local mains are ZH23/EN24 pages; those maps/PDFs are not published.
All38 focused guards pass. The
[full comparison](pirc17/reader-v5-regression-check.json) reports
1002PASS/25FAIL/2ERROR with no added failure/error identities, not a passing
whole suite. Four unchanged main figures, two tables, all50 supplement tables
and earlier delivery versions remain. Real declarations and human acceptance
are still required; editorial delivery is not submission certification.

## Previous reader-v4 delivery (superseded)

The body now defines its empirical object: timestamped historical GPX
position recordings with unverified carrier identities and transport modes.
It states the visible-prefix forecasting task and predictive distribution,
distinguishes windows/blocks/origins and coordinate frames, and explains
the fitted SDE drift, diffusion, latent components, parameter estimation,
actual Full split propagation and separate two-stage terrain model. The
discussion connects these mechanisms to the reported diagnostics while
keeping possible causes separate from demonstrated results. The conclusion
answers the diagnostic questions and the original RQ1/RQ2.

| Language | Main paper | Scientific supplement | Audit record |
| --- | --- | --- | --- |
| Chinese | [14-page paper](pirc17/revision46-review-v4/zh/main.pdf) | [78-page supplement](pirc17/revision46-review-v4/zh/supplement.pdf) | [15-page record](pirc17/revision46-review-v4/zh/audit-notes.pdf) |
| English | [15-page paper](pirc17/revision46-review-v4/en/main.pdf) | [80-page supplement](pirc17/revision46-review-v4/en/supplement.pdf) | [16-page record](pirc17/revision46-review-v4/en/audit-notes.pdf) |

Keep each language's three PDFs together for companion links. The
[build manifest](pirc17/revision46-review-v4/build-manifest.json) binds the
six documents to clean reviewed local sourcec71d0e77 and exact input/PDF hashes.
Its [public source equivalent01907d69](pirc17/reader-v4-public-source-binding.json)
has the identical Git tree: only unpublished commit identity metadata was
corrected for GitHub email privacy. All66 input hashes and original PDFs
are preserved; this does not infer manuscript authorship from Git identity.
Sources remain `pirc17/{en,zh}/{main,supplement,audit-notes}.tex`, with the
new `reader-v4-{task,full,propagation,terrain}.tex` body inputs. Rebuild using
the existing `scripts/build_pirc17_revision46.py --output-dir <fresh-external-directory>`.

Four original figures/two core tables and all50 supplementary tables remain.
No new figure, fit, forecast, scientific score, map query or bootstrap was
produced. The separate local build retains six unchanged maps in appendices:
Chinese22 pages and English23 pages. Those local PDFs/maps are not published.
Earlier v1/v2/v3 PDFs, numeric evidence and response records are preserved.

Two fresh read-only gpt-6-astra/high ACP sessions completed with21 and6
focused calls. The first found the research-object/model/argument objection
substantively addressed, with one coordinate-description P2. After repair,
the follow-up checked the actual final source/PDF/log hashes and confirmed
that P2 closed without another substantive inconsistency. The
[editorial/review receipt](pirc17/reader-v4-editorial-record.json) records
their exact scope and configuration. Twelve strict builds and page-boundary
checks pass,58 public companion links resolve, and six local map bytes/24
annotations match. The [full regression comparison](pirc17/reader-v4-regression-check.json)
reports997PASS/25FAIL/2ERROR with no new failure/error identities; all33
current-source guards pass. This is not a green whole-suite claim.

The paper's scientific conclusions remain bounded: horizon-dependent
ordering, score/location conflict and substantial undercoverage; terrain
inference remains unavailable under the required-failure rule. Actual
author/affiliation/contribution/conflict and ethics/consent/research-use
declarations still require confirmation before submission. The agent
reviews do not provide human or journal acceptance.

## Previous reader-v3 delivery (superseded)

The converged manuscript centres on horizon reversal, conflicting error
metrics and marginal undercoverage. It uses four existing figures and two
core tables; all 50 supplementary tables and historical figure/PDF versions
are retained. No new figure, fit, forecast, research score or bootstrap was
produced in this editorial round.

| Language | Main paper | Scientific supplement | Audit record |
| --- | --- | --- | --- |
| English | [11-page paper](pirc17/revision46-review-v3/en/main.pdf) | [80-page supplement](pirc17/revision46-review-v3/en/supplement.pdf) | [16-page record](pirc17/revision46-review-v3/en/audit-notes.pdf) |
| Chinese | [11-page paper](pirc17/revision46-review-v3/zh/main.pdf) | [78-page supplement](pirc17/revision46-review-v3/zh/supplement.pdf) | [15-page record](pirc17/revision46-review-v3/zh/audit-notes.pdf) |

Keep the three PDFs of each language together for companion links.
Current sources are `pirc17/{en,zh}/{main,supplement,audit-notes}.tex`.
The [build manifest](pirc17/revision46-review-v3/build-manifest.json) binds
all six PDFs to clean source checkpoint4269233 and exact input hashes;
the later PDF-delivery commit is a different revision. V1 and V2 review
packages, including the original77-page Chinese supplement, remain unchanged.

The four figures explain cohort selection, Full/inertia horizons, the21
named-control ES/FDE contrasts, and coverage versus region area. Geometry,
configuration detail, full heatmaps, seed uncertainty and execution history
remain in the companions. The body now defines the retained GPX task,
development/evaluation roles, last-three-point inertial secant and Full01,
and reports short-horizon ES values directly. Terrain RQ2 remains unavailable
under the original failed-family rule, not a positive or null terrain result.
The execution-bound ES U-statistic retains denominator `2N(N-1)`;
all original scientific outputs and prior corrections are preserved.

Two fresh read-only **gpt-6-astra / high / ACP** reviews used bounded contexts
(18 and8 focused tool calls). Runtime configuration and saved turn contexts
confirmed the actual model/effort/sandbox. The reviewer supported the
three-part diagnostic argument and existing-figure selection; editorial
findings were addressed, including task definition, self-contained public
evidence and exact supplement navigation. The last remaining Chinese setup
anchor was then repaired and all55 public companion links verified.
[Editorial and review receipt](pirc17/reader-v3-editorial-record.json)
separates review scope, host verification and unconfirmed author matters.

This is a complete bounded manuscript body, not certification of immediate
submission readiness. Real author identities/affiliations/contributions,
conflict declarations, applicable ethics/consent basis and trajectory
research-use permissions still require author confirmation. Missing
probabilistic baselines, uncertain physical clocks/recording independence,
prior evaluation exposure, label/calibration mismatch and terrain
confounding remain disclosed scientific limitations. No permission or
human acceptance is inferred from compilation or an agent review.

Rebuild from the repository root using a fresh external directory:

```text
python scripts/build_pirc17_revision46.py --output-dir <fresh-external-directory>
python scripts/check_pirc17_revision46_links.py --build-dir <fresh-external-directory>
```

The separate local build uses explicit `--private-manuscript`,
`--case-figures` and `--output-dir` arguments to
`scripts/build_pirc17_revision46_local.py`. Both local papers are19 pages:
the same core argument plus an appendix with the existing six maps/two case
tables. Hashes and24 error/radius/coverage annotations match their original
receipts; checked embedded map labels remain at least8.16pt. The builder
copies existing maps without rendering, querying layers or reading particle
arrays. Local PDFs, maps and case-level inputs must not be uploaded.

The original public regression baseline has25 failures and two private-input
collection errors. The [current full-run comparison](pirc17/reader-v3-regression-check.json)
reports actual failure identities without skips or private-data stand-ins;
it is not a claim of green CI. The current body has separate guards, while
the former V2 layout contract is checked against its exact historical Git
source, with all scientific assertions preserved.

The [46-card response](pirc17/revision46-response-v3.json) is retained as the
earlier correction record, including305 criteria, the42-item mapping,
the superseded ES criterion and unresolved R05/R06/R10 scientific gaps.
Reader-v3's separate editorial receipt does not relabel those criteria as
independently accepted. Five follow-up designs remain unexecuted.

PR #17 follows the repository's issue-first title rule:
`#16 paper(pirc17): ...` matches source branch `paper/16-pirc17-review`.
The traceability gate must pass independently of the document build;
an inherited evidence-test failure is not grounds to waive that gate.

Everything below describes earlier handoffs, not the current entrypoint.

## Historical handoff

This handoff contains parallel English and Chinese LaTeX sources for the
proposed paper repository.  The two files have matching section structure so
that a revision to one can be reviewed against the other.

## Proposed repository layout

```text
paper/
  en/main.tex       English source of record
  zh/main.tex       Chinese translation, kept section-for-section aligned
  figures/          source figures only; never trajectory images or samples
  tables/           aggregate, reviewed tables only
  references.bib    verified bibliographic records
```

`en/main.tex` is the source of record.  The Chinese document is a translation
draft, not an independent claim set.  Before submission, add only verified
references to `references.bib`, replace every marked placeholder with evidence
from a versioned run, and obtain data/privacy review for any aggregate result.

## PIRC-17 manuscript in progress

`pirc17/en/main.tex` is the working source for the current causal component and
terrain study. It uses the existing English article layout. Its methods are
bound to the frozen PIRC-17 protocol; its result estimates and final conclusions
are awaiting the complete audited public evidence cards. The review draft has
no asserted author identities. The existing `en/main.tex` and `zh/main.tex`
retain historical studies and must not be mistaken for the new PIRC-17 result.

Build the current review draft from `paper/pirc17/en`:

```text
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

The review PDFs are `pirc17/en/main.pdf` and `pirc17/zh/main.pdf`. The Chinese
review draft follows the English section structure and registered equations;
build it from `paper/pirc17/zh` with `latexmk -xelatex` and the same flags.
Before final delivery, integrate the
audited method and terrain result sections, all required tables and figures,
claim-to-card links, verified authorship, and aligned final Chinese numerical
results and claims.
This draft does not complete DEV-06 or final scientific acceptance.

For one declared bilingual review build from the repository root, use a new
empty output directory outside `paper/`:

```text
python scripts/build_pirc17.py --output-dir .local/pirc17-review-build
```

This checks the public boundary, builds the current English and Chinese sources,
rejects unresolved references/citations, missing glyphs and clipped boxes, and
records source/PDF/log hashes in `build-manifest.json`. It never overwrites the
committed PDFs or previous build evidence, publishes nothing, and explicitly
does not verify empirical claims or human acceptance. The recorded Git revision
and dirty-state flag distinguish an interim working build from a clean revision.

### PIRC-17 reproduction boundaries

The current draft was built locally with TeX Live 2024 and latexmk 4.83. English
uses pdfLaTeX; Chinese uses XeLaTeX/ctex. The observed Windows build uses its
available CJK fonts; Linux font fallback and cross-platform PDF byte identity
have not been verified. Use a separate output directory for temporary review
builds, inspect the final log for unresolved references/citations or missing
glyphs, and run `python scripts/check_public_release.py` from the repository
root. Compilation proves document buildability, not empirical correctness.

The three external trajectory/SDE papers cited in the current related-work
section are context, not newly added benchmark slots. No result against those
models is claimed and no additional model-fitting experiment is required.

Once qualified public cards exist, reproduce the original 16 tables and 16
PNG/PDF figures with the pinned commands in
`scripts/PIRC17_PUBLIC_ARTIFACTS.md`. Record the card content identity, export
and audit provenance, table and figure manifests, rendering environment, and
exact manuscript revision alongside the final review. Do not pass private
method previews as public evidence, repeat bootstrap arithmetic in a renderer,
or turn failed/missing rows into zero-valued effects.

The existing CI/release jobs build the historical `paper/en` and `paper/zh`
entrypoints, not the new `paper/pirc17` draft. A historical green build or
release therefore cannot close PIRC-17. Final entrypoint integration or a
separately declared PIRC-17 build/release must be reviewed with the completed
manuscript; no pending draft is published by this local preparation change.

No dataset, checkpoint, trajectory, example coordinate, or experimental metric
is included in this handoff.

## Publishing a paper release

The release workflow is intentionally simple: a pull request into `main` runs
validation only. Once it is merged, GitHub pushes the merge commit to protected
`main`; that push builds the English and Chinese documents and automatically
creates one immutable GitHub Release. It does not publish for a
`pull_request` event.

Each successful commit receives a new `paper-release-<12-character-sha>`
Release tag. The workflow refuses to reuse either an existing tag or an
existing Release, so it never overwrites a published version. The only
uploaded Release assets are:

- `learnable-sde-paper-en.pdf`
- `learnable-sde-paper-zh.pdf`
- `SHA256SUMS`

GitHub may separately display its built-in “Source code” archive links on a
Release page. They are generated by GitHub, not assets uploaded by this
workflow; this repository workflow uploads no source archive, data, or
checkpoint.

To publish, merge an approved pull request into `main`. No tag and no second
push are required: the resulting `main` push is the release trigger. Protect
`main` from force pushes and require the CI check before merge.

For an exceptional, direct release-ready commit (when repository policy allows
it), the equivalent trigger is:

```powershell
git switch main
git pull --ff-only origin main
# Make the reviewed release-ready commit, then:
git push origin main
```

The workflow's public-boundary check runs before either PDF build and before
the release job. Do not use this branch to carry datasets, trajectories,
checkpoints, logs, or private material.
The [claim contract](pirc17/reader-v7-claims.json) records every requested
