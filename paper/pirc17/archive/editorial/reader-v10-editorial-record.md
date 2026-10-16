# Reader-v10: conclusion and body-layout correction

## Request and source

The user reported repeated Figure 5 / Discussion / Conclusion rendering and
requested numbered experimental conclusions as the main body's only ordered
list. Reviewed/compiled source: `67912a0c0295f3d6e751cc7aec35a44403014975`.

Actual baseline public/local Chinese PDFs already contain Figure 5 once;
their ctex running section titles repeat Discussion/Conclusion on the same
page as the actual heading. The correction uses plain body page style and
a results float barrier, not deletion of scientific evidence. Six conclusions
replace unnumbered conclusion paragraphs; qualifications remain outside.
No figure extension was performed: the preceding Figure 2 clarification is
not silently treated as authorization for a particular four-curve selection.

## Actual outputs

Public: ZH main22/supplement80/audit16 pages; EN main24/supplement80/audit17.
Local owner-only: ZH main30 and EN main32; companion page counts unchanged.
All twelve documents compile with strict logs and no out-of-page text.
All 58 public companion destinations resolve. The six private maps are not
published or changed. Source graph has 76 unique inputs and a clean source
checkpoint; six published PDF SHA256 values are in the build manifest.

Actual public/local ZH Figure 5 is on p16, Discussion on p18, conclusions on
p19–20; EN Figure 5 is on p18, Discussion on p19, conclusions on p21.
Each body has one Figure 5, one Discussion title, one Conclusion title and
one ordered list displaying 1. through 6. The six findings address horizons,
RDM, observation interval, training/adaptation, reliability and terrain.

## Independent review

Fresh actual ACP session `01a13f56-7ae4-7662-99bd-dc2592d80f03` confirmed exact
`gpt-6-astra` / `high` / read-only via configuration. It returned `end_turn`
after seven tool calls, inspected source and four actual public/local body
PDFs plus key-page renderings, and reported no substantive P1/P2 issue.
Scope is this editorial change, not all scientific design or submission
readiness; author/ethics/consent declarations and human acceptance are not
certified by agent review.

## Regression checks

23 focused tests pass. Full run on the source checkpoint: 1039 passed,
25 failed, two collection errors in 210.43 seconds. Comparison with original
967/25/2 baseline introduces no failure or error identity; the suite is not
green and missing private inputs are not replaced or skipped.

The numeric-evidence guard now explicitly validates versioned six-document
build receipts (schema, zero empirical execution and six real PDF hashes).
This fixes its rejection of the already-published v9 build receipt, without
exempting arbitrary numerical JSON/CSV or changing scientific assertions.
All prior figures, numerical source artifacts and inference rules remain.
