# CI/CD guide

This guide explains the manuscript workflows. It records what the workflows
are configured to verify; a GitHub check is evidence only for the exact commit
and event displayed by GitHub Actions, and no remote result is asserted here.

## When workflows run

`CI` runs for pushes to `main`, pull requests targeting `main`, and manual
`workflow_dispatch` runs. It has read-only repository permission.

`Release` can be dispatched manually for a reproducible build, but publishes a
GitHub Release only from a `paper-v*` tag ref. The publish job is the only job
granted `contents: write`, so a non-tag manual run cannot publish assets.

## CI jobs

| Job shown in GitHub | What it verifies | Why it exists |
| --- | --- | --- |
| `policy` | On pull requests, checks title/branch traceability. On every trigger, scans the source tree for material outside the public-release boundary. | Keeps manuscript revisions auditable and prevents private research material from entering public automation. |
| `tex / en` | Compiles `paper/en/main.tex` with pdfLaTeX in halt-on-error mode, rejects unresolved references/citations or a required rerun notice, and stores the resulting PDF briefly as an Actions artifact. | Ensures the English source of record produces a complete PDF. |
| `tex / zh` | Compiles `paper/zh/main.tex` with XeLaTeX in halt-on-error mode, applies the same log checks, and stores the PDF briefly as an Actions artifact. | Ensures the Chinese translation can be independently typeset with its required engine. |
| `ci / required` | Runs even after an upstream failure and passes only when `policy`, `tex / en`, and `tex / zh` all succeed. | Provides branch protection with one clear aggregate result. |

## Release outputs

For a `paper-v*` tag, `Release` repeats the policy scan and both isolated TeX
builds, including the unresolved-reference checks. The English and Chinese PDFs
are retained as short-lived build artifacts first. When both succeed, the
tag-only publish job downloads them, generates `SHA256SUMS`, and attaches the
two PDFs plus that checksum file to the GitHub Release.

To verify a downloaded release, put all assets in one directory and run
`sha256sum -c SHA256SUMS`. The checksums identify the exact bytes attached to
that release; they do not replace reviewing the sources and tag.

## Publication boundary

The workflows compile manuscript sources and approved aggregate material only.
Raw or transformed trajectories, coordinates, timestamps, identifiers,
checkpoints, row-level predictions, and unreviewed empirical results must not
be committed, uploaded as CI artifacts, or attached to a Release. The English
source remains authoritative; the Chinese source is its aligned translation.
