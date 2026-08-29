# Contributing

The English source is authoritative. The archived Chinese generic draft is not
a translation of the current manuscript. Keep a change focused on one source,
rendering concern, or reviewed paper claim. Never add raw or transformed trajectories, coordinates,
timestamps, identifiers, row-level predictions, checkpoints, private logs,
local paths, credentials, or archives containing them.

## Traceable collaboration

Create or triage one actionable GitHub Issue with one primary type: `feature`,
`bug`, `documentation`, `refactor`, `test`, `build`, `ci`, `maintenance`, or
`paper`. Work from protected `main` on `<prefix>/<issue>-<summary>`; use
`paper/<issue>-<summary>` for manuscript content or production. Ordinary
commit and PR titles use `#<issue> <type>(optional-scope): imperative summary`
and the type must match the branch prefix. The only no-Issue exception is
`chore: repository bootstrap ...`, with its reason documented in the commit.

Open a focused reviewed PR to `main` with `Refs: #<issue>` (or `Closes:
#<issue>` when the merge should close it), source/PDF impact, and actual
validation results. Do not force-push or delete `main`; prefer squash merge and
delete the merged topic branch. See `GIT_WORKFLOW.md` for daily sync, recovery,
hotfix, and release rules.

## Canonical local checks

```powershell
Set-Location paper/en
pdflatex -interaction=nonstopmode -halt-on-error -file-line-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error -file-line-error main.tex
Set-Location ../..
python scripts/check_public_release.py
```

Do not claim that a PDF is clean unless the build succeeded and its log has no
undefined reference/citation warnings. CI produces short-retention preview
artifacts for both language editions; it does not publish releases or Pages.
