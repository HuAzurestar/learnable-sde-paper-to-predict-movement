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
