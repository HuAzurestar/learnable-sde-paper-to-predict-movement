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

## CI/CD and releases

Pull requests to `main` run validation only. When one is merged, GitHub pushes
the merge commit to `main`; that push automatically compiles both manuscripts
and creates a new immutable GitHub Release. It never publishes from a
`pull_request` event. Each Release contains only the English PDF, Chinese PDF,
and `SHA256SUMS`; the workflow refuses to replace an existing tag or Release.
For the full trigger and verification details, see [CI_CD.md](CI_CD.md).
