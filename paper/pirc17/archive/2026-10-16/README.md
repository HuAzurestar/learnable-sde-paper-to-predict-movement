# Legacy TeX archive — pending owner inspection

These twenty files were moved, not rewritten or discarded. They are obsolete
manuscript/layout sources formerly mixed into `paper/pirc17/en` and `zh`.
The current six-document build does not input any of them. No figure, table
value, current source input, private map or scientific inference was changed.

Each language has the old complete `historical-main-v1.tex`, four historical
table fragments, three reader-v2 layout fragments and two revision46 layout
fragments. Paths beneath `en/` and `zh/` preserve the original language and
filename. These are historical source snapshots, not an alternative current
compilation entry; do not compile this directory as today's paper.

The permanent [archive index](../../tex-archive-index.tsv) records original
paths, archive paths and exact SHA256 bytes. The recoverable source commit is
`8caa3a09bdda29a1f8613f11710e1f84eb01e5dc`. Current entries remain
`../../en/main.tex`, `../../zh/main.tex` and their supplement/audit companions.

Historical readers use `scripts/pirc17_historical_tex.py`: archived files are
hash-checked; if this review directory is later removed, the same bytes are
read from that pinned Git commit. Keep the index and Git history. Corruption
does not silently fall back or bypass assertions. Original manifests keep
their original IDs and checksums; they are not rewritten to pretend the
historical build used the new archive location.

Restoration: for a row in the index, move its archive path back to its original
path relative to `paper/pirc17`, only if that destination is absent. Verify
the indexed SHA256 before and after; do not overwrite current work.

Not moved: 56 TeX inputs used by the current six-document build; 20 original
templates still used by today's display regeneration; and 38 versioned
evidence-table artifacts already isolated in `final-results-v1`,
`secondary-scores-v1` and `figures/terrain-description-v1`. The latter are
evidence packages, not abandoned chapters. Other research-lineage sources
under `paper/en` and `paper/zh` are also outside this archival change.

This archive has not been approved for deletion. Please inspect it first.
