# Paper sources and review manuscripts

## Current PIRC-17 manuscript: reader-v4

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
six documents to clean source checkpointc71d0e77 and exact input/PDF hashes.
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
