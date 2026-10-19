# PIRC-41 research evolution review — first draft

Start with [the review manuscript](review.md). This standalone Chinese-language
review maps stochastic dynamics, trajectory prediction, search decisions and
empirical search-and-rescue behavior. The directory name is English; the existing
manuscript has not been translated or replaced. This bundle does not change the
authoritative English or aligned Chinese LaTeX papers elsewhere in this repository.

This is a reviewable research snapshot, **not completed field verification, a
peer-reviewed article, a new prediction algorithm or a validated SAR system**.
Literature publication cutoff: 16 October 2026; some supplementary verification
occurred later. The pool contains 208 records rather than arbitrarily dropping
eight to reach the initial target of 200. Distinct publication records do not prove
208 independent inventions, versions or study cohorts.

## Reading the four deliverables

| File | Contents and interpretation |
| --- | --- |
| [review.md](review.md) | Existing manuscript body, research branches, selective historical anchors, maturity judgments, research gaps and 27 references. |
| [papers.xlsx](papers.xlsx) | 208-row `Papers` sheet plus authors, institutions, technical fields, findings, sources, evidence status, version reviews and scoring evidence. Read `Readme` first. |
| [relations.csv](relations.csv) | 585 internal relationships: 548 citations, 19 extensions, 6 transfers and 12 comparisons; 9 external relationships and 1 excluded assertion are separately qualified. Direction is predecessor/cited work → successor/citing work. |
| [timeline.html](timeline.html) | Download and open locally in a browser. Self-contained direction/year/impact/evidence filters, milestone view and paper details; no web server or network is required for interaction. Source links leave the offline document only when opened. GitHub's file view is not an HTML host. |

Main tracks contain A=54 stochastic-dynamics, B=54 trajectory-prediction, C=50
search-decision and D=50 empirical/behavior records; secondary classifications can
overlap. There are 60 focused full-text readings, 143 abstract/short-content records
and 5 metadata-only records. The 160 records with bounded passage supplements
overlap those groups and must not be added as another 160 full readings.

Scores are qualified ordinal judgments for 25 candidates, not scores for all 208
records: 23 have complete scores and 2 retain an unknown dimension with no total.
The 23 selected milestones comprise 20 complete-score selections and 3 historical
qualitative selections. High citations, a channel ranking or a citation edge alone
does not demonstrate technical adoption, external validity or causal influence.

## Evidence and public-export boundary

See [KNOWN_GAPS.md](KNOWN_GAPS.md) before interpreting missing values. Blank/null
means unknown, unverified or inapplicable according to the adjacent status; it does
not mean zero. Channel-quality snapshots are historical institutional reports,
not current rankings or automatically the paper's publication-year ranking.

This is a public projection of the internal accepted snapshot. Workstation/cache
locations, internal evidence-file references and browser handles are omitted.
The manuscript body is unchanged; its mention of later internal audit material
refers to the internal edition, whose post-manuscript execution history is not
included here. Scientific values, nulls, source URLs, locators, version limits and
prior scientific judgments are retained. The original internal files are not
modified. A local storage locator is not a public evidence link.

`RawRecords` reconstructs the **public-projected**, not byte-identical internal,
records: group by `paper_id`, sort `part` numerically, concatenate `json_chunk`,
then parse JSON. These 208 reconstructed records equal the `record` objects in
the HTML's `research-data` JSON. There is no Excel-cell truncation or executable
spreadsheet formula. [manifest.json](manifest.json) records public hashes,
input fingerprints, projection rules and coverage counts. Verify file integrity
with SHA-256; the manuscript body hash is also recorded separately.

This snapshot does not distribute source PDFs, licensed ranking tables, raw study
data, private runtime logs or the complete extraction environment. Public URLs
may change or require legitimate access. The package supports review of recorded
claims; it does not claim independent reproduction of every cited result.

## Verification scope

The accompanying PR records fresh checks of the public export: workbook/HTML
agreement, relationship/status counts, manuscript references, workbook XML and
text privacy scans, and offline timeline interaction. These packaging checks are
not additional full-text readings or a closure of research gaps. Existing LaTeX
sources and PDFs are unchanged; no new bilingual PDF build is claimed.
