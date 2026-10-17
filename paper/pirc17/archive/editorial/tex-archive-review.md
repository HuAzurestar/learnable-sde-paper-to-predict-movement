# Reversible legacy TeX archive — 2026-10-16

The user requested archiving for inspection before any deletion. Twenty
obsolete manuscript/layout files were moved from the two language source
directories into [the dated archive](archive/2026-10-16/README.md). None was
discarded. The [permanent index](tex-archive-index.tsv) retains original
paths and exact original checkout SHA256 values. All twenty archive Git
blobs were checked against those hashes, including their line endings.

Current compilation inputs (56 TeX / 76 total files), twenty original
regeneration templates and 38 already-separated versioned evidence-table
TeX files remain in place. Existing current chapter filenames were not
renamed in this scope. Scientific JSON/CSV, original manifests, fits,
predictions, inference rules, figures and private maps were not changed.

Historical reads now use an explicit hash-checked resolver, not global
monkeypatching. If archive files are later removed, the resolver obtains
the same bytes from pinned source8caa3a09bdda29a1f8613f11710e1f84eb01e5dc;
checkout-only CRLF reconstruction is accepted only when the exact indexed
hash proves it. A corrupt existing archive raises an error rather than
silently falling back. Keep the index and Git history if deleting later.
The archive is not a current compilation entry; original historical
receipts keep their original paths and are not rewritten.

## Verification

Archive source8125b48f447bb0423444a91160b7f015a6be9f05 rebuilt all six public
documents strictly. Their text and every one of239 rendered pages match
the delivered v10 PDFs exactly. All58 companion links resolve. The final
test-only closure72d7b864e6669d93d2d67475afc893ab06d06bf6 changes no build
input. No redundant new PDF release package was added.

On clean72d7b864,28 focused checks pass. Complete regression:1043passed,
25failed,2collection errors in225.42s. Comparison to v10's1039/25/2 shows
no introduced failure/error identity. The suite remains non-green; missing
private inputs are not fabricated, excluded or skipped. Scientific
assertions remain; the historical migration AST guard normalises only
explicit indexed archive-file read wrappers, not scientific values.

Actual gpt-6-astra/high/read-only ACP session
01a14328-53e2-78d2-9883-f30989d38ca7 reviewed archive bytes, current source
hashes, regeneration sources, mechanical read-path changes and the scoped
AST guard. Initial review ended normally without substantiveP1/P2. A
subsequent test-running closure returned cancelled; the final resumed
code-review response ended normally, reporting no substantiveP1/P2 on
72d7b864. Its attempted tests did not complete; focused/full pytest and
PDF comparisons above were performed by the executing agent, not claimed
as independently rerun by the reviewer. Replayed calls are not new review.

Formal author/ethics/consent/research-use declarations and actual human
acceptance remain separate. This archive does not certify submission
readiness, permit deletion, or publish private trajectories/maps.
