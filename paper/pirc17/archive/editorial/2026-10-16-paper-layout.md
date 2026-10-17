# One current manuscript entry — 2026-10-16

The user's request is manuscript-directory convergence, not experimental
data or image cleanup. The earlier twenty-TeX archive was insufficient:
ten numbered PDF releases and many review records still competed for
attention. Current reading now starts only at paper/README.md or
paper/pirc17/README.md, with stable current/{zh,en}/main.pdf and
supplement.pdf. Companion audit PDFs are labelled as audit, not another
paper version. No new reader/revision directory was created.

107 paper-only artifacts moved into archive/paper-versions and
archive/editorial; paper-layout-index.tsv preserves original paths and
exact pre-move working-tree SHA256 values. The old paper README remains
as a labelled historical snapshot. All107 archived Git blobs match those
indexed bytes. Eleven differ from their predecessor Git blobs only by
pre-existing Windows checkout line endings; stored JSON contents/keys are
not rewritten. Only verified empty old version directories were removed.
The file contents themselves were not discarded.

Scientific JSON/CSV, data packages, all figure/image paths and Git blobs,
56 active TeX inputs, and twenty regeneration templates remain unchanged.
The only relocated JSON files are explicitly allowed paper-review/build
metadata, not experimental inputs. Existing old figure producer receipts
keep their original keys; explicit path resolution locates archived
snapshots. Old version identifiers never alias mutable current/.

## Verification and review

Implementation052bf3eb0d253e4af8e83460f508c40a94fa67c9; final tested and
reviewed sourcefd3fa90f5fbdc57637e3af5683e91779050f4250. The latter adds
only the remaining historical scoring-binding read adapter.

Six public documents strictly rebuilt from clean052bf3e; all239page texts
and rendered-page hashes match current/, and all58 companion destinations
resolve. Current six PDFs and build manifest preserve the last delivered
release bytes. No unnecessary PDF regeneration release was added.

41 focused checks pass. Full final run onfd3fa90:1047passed/25failed/
2collection errors in240.78s. Compared with the pre-cleanup1043/25/2,
there is no introduced failure/error identity. The suite remains non-green;
private inputs are not fabricated, excluded or skipped. An initial run
found one missing metadata-reader alias; it was fixed before final replay.
Scientific assertions remain; path-only AST normalisation is limited to
explicit read-path adapters, with independent data/image/move-byte guards.

Actual gpt-6-astra/high/read-only ACP session
01a14390-4f0c-7e23-8024-ce40b6f380c9 completed normally (end_turn) after
four actual read-only calls, reporting no substantiveP1/P2. It checked
front-page clarity,107archived hashes, unchanged data/image/source paths
and blobs,76buildinput hashes, six current artifacts, and scoped guards.
The review text misstated its count as six; client observed four calls.
An earlier session-creation attempt failed before any review call and is
not counted as a successful review. Reviewer did not run pytest/builds
or compare full PDF pages; those checks were executed by the primary agent.

This is organisation-only, not submission certification. Original
scientific limitations, author/ethics/consent/research-use declarations,
human acceptance and the PR's draft/unmerged boundary remain.
