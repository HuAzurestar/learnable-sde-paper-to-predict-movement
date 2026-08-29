# Learnable SDE paper to predict movement

The current source of record is the NEX-345 v4.2 manuscript, *Learning a
Dual-Conditioned Stochastic Differential Equation for Lost-Person Movement
Prediction in Search and Rescue*. The former generic bilingual draft is
archived and must not be released as the current paper.

## Layout

```text
paper/
  en/main.tex       Current English source of record (NEX-345 v4.2)
  en/main.pdf       Checked PDF supplied with the reviewed delivery
  en/figures/       Reviewed, aggregate-only figures
  en/tables/        Reviewed, aggregate-only tables
  archive/          Historical drafts, excluded from the current release
formalization/
  lean/e-series/    Lean4 source for the paper's formalized core
```

The English source is authoritative. A reviewed Chinese translation of this
specific manuscript has not been supplied, so this revision releases no Chinese
PDF. The bibliography is embedded in `main.tex` and should be independently
verified before external submission.

## Build

```powershell
Set-Location paper/en
pdflatex -interaction=nonstopmode -halt-on-error main.tex

```

The repository must not contain raw or transformed trajectories, coordinates,
timestamps, identifiers, checkpoints, row-level predictions, or unreviewed
empirical results. Public builds use only the included manuscript sources and
approved aggregate material.

## CI/CD and releases

For workflow triggers, the English compilation check, and the tagged PDF
release asset, see [CI_CD.md](CI_CD.md).
