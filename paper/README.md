# Paper sources and review manuscripts

## Current PIRC-17 manuscript revision

Start with the actual revised manuscript, not the historical monolithic PDFs:

| Language | Main paper | Scientific supplement | Audit record |
| --- | --- | --- | --- |
| English | [18-page paper](pirc17/revision46-review-v2/en/main.pdf) | [80-page supplement](pirc17/revision46-review-v2/en/supplement.pdf) | [16-page record](pirc17/revision46-review-v2/en/audit-notes.pdf) |
| Chinese | [17-page paper](pirc17/revision46-review-v2/zh/main.pdf) | [78-page supplement](pirc17/revision46-review-v2/zh/supplement.pdf) | [15-page record](pirc17/revision46-review-v2/zh/audit-notes.pdf) |

The six documents are a single review package: keep the three PDF files of
each language together so companion named-destination links resolve.
Current sources are `pirc17/{en,zh}/{main,supplement,audit-notes}.tex`.
The versioned [build manifest](pirc17/revision46-review-v2/build-manifest.json)
records actual source-file hashes, PDF hashes, strict logs and page counts.
The manifest distinguishes the source checkpoint from the later commit that
adds the review PDFs. Historical v1 PDFs, including the 77-page Chinese
supplement, and their source bindings remain unchanged.

The 13 October review correction binds ES to the scorer used by the execution:
the ordered-pair U statistic has denominator `2N(N-1)`, with a separate
direct-distance branch for the deterministic inertial reference. The old main
equation and its checklist sentence were wrong; no original scores are rerun.
The expanded body explains input geometry, the ten-configuration design,
all 21 ES/FDE contrasts, coverage versus disk size, and seed versus block
uncertainty. Versioned pale heatmaps use black text and symmetric signed
coverage deviation. Historical table status is dated rather than erased.

This revision implements G01–G13, O01–O08, R01–R17 and X01–X08 without new
fitting, forecasts or resampling. G12 is delivered in a separate local
map-containing manuscript, not these public PDFs. Authorship, independent
reader feedback, route publication permission and final human acceptance
remain unconfirmed. Document-level corrections do not remove missing mode
snapshots, unknown physical clock provenance, ablation confounding or failed
terrain comparisons. Five follow-up designs are explicitly not new results.

Rebuild and verify from the repository root, using a fresh external directory:

```text
python scripts/build_pirc17_revision46.py --output-dir <fresh-external-directory>
python scripts/check_pirc17_revision46_links.py --build-dir <fresh-external-directory>
```

For local-only route illustrations, use the explicit `--private-manuscript` and
`--output-dir` options of `scripts/build_pirc17_revision46_local.py`. The
private-manuscript argument names the original `paper/pirc17` directory,
containing the language and figure folders. Pass `--case-figures` for the
separately re-laid-out, hash-bound private maps. The local body is 25 pages in
each language and retains all six maps; 24 error/radius/coverage annotations
match the originals, and checked embedded map labels are at least 8.16 pt.
`scripts/check_pirc17_reader_v2_local.py` verifies those annotations and links.
The rendering command rereads the original display layers and saved arrays;
it performs no new fitting, forecasting or scoring. Do not upload its output
or its case-level input.

The full regression is not green: the isolated original public snapshot has
25 failures and two private-input collection errors. The revision preserves
these checks and compares their actual identities rather than excluding
them. CI does not waive these failures. The new structure guards separately
check current manuscripts; archived-layout guards target the exact preserved
`historical-main-v1.tex`, without deleting their scientific assertions.

The [46-card implementation response](pirc17/revision46-response-v3.json)
retains all 305 criteria and the original 42-item mapping. It distinguishes
editor review, unresolved scientific provenance and pending real author /
independent-reader confirmation; it is not an acceptance certificate. The
incorrect historical ES criterion is explicitly superseded. R05, R06 and
R10 now list their specific remaining gaps and N03/N04/N01 follow-up designs,
not empty gap lists or claims that the experiments have been completed.

Everything below describes earlier handoffs. Older `public-review.pdf`,
review bindings and snapshots are historical, not the current review entry.

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
