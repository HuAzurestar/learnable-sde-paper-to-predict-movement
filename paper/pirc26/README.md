# PIRC-26 independent report

English is authoritative; Chinese follows the same section labels. This report
does not replace the repository's existing SAR manuscript. Authorship is a project
record, not invented human authorship or journal acceptance.

The public boundary is reviewed aggregates and authored controls only: no raw or
transformed trajectories, coordinates, observation timestamps, unit/segment IDs,
per-row real predictions, models, checkpoints, private paths or credentials.
Source artifacts remain controlled in DSDE/shared storage. A summary hash is
traceability, not permission to read those artifacts or a public raw-data license.

## Aggregate smoke reproduction

From the repository root, using Python 3.10 or newer (standard library only):

```sh
python -B -m unittest discover -s tests -p test_pirc26_evidence.py -v
python -B scripts/pirc26_package.py --check
python -B scripts/pirc26_package.py
python -B scripts/pirc26_package.py --check
python scripts/check_public_release.py
```

`--check` is read-only. The rebuild writes only the seven deterministic table
sources and claim index beneath this report. It performs no simulations, fitting,
score recomputation, interval recomputation or model selection. Actual research
qualification is not inferred from fixture tests or a successful PDF build.

Build English with `pdflatex` twice from `en`, Chinese with `xelatex` twice from
`zh`, always with `-no-shell-escape -interaction=nonstopmode -halt-on-error`.
Reject undefined citations/references after the second pass. Both languages use
the same seven generated numeric tables; each edition selects full readable names
and column headings in its own language. PDFs are build products, not committed research data.
From the repository root, run
`python scripts/pirc26_check_tex_log.py paper/pirc26/en/main.log paper/pirc26/zh/main.log`.
This also rejects missing glyphs and boxes overflowing by more than 2 pt, so a
successful compilation alone cannot hide clipped provenance identifiers.

## Scientific reproduction scope

`REPRODUCTION.md` specifies the actual controls, source epochs, population and
stopping rules. `evidence/summary.json` retains the six terminal source bindings,
all authored challenge score rows, failure/missingness counts and the cumulative
all-attempt cost snapshot. `evidence/claims.json` binds table bytes and research
questions to those sources. These are aggregate-copy reproduction, not an
independent numerical replication. Full replication needs authorized access to
original artifacts and their immutable archived operators; do not invent a new
dataset copy, source grant, model arm or cleared cost ledger.

The embedded disclosure review is Codex's exact technical/privacy review under
the approved aggregate-paper scope, not human scientific acceptance. The shared
owner creates a separate derived-output grant; the compact input's no-export
grant and all original raw/model grants remain unchanged.
