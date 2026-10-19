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

## Journal-first reading priority and degree-thesis screening

The user's editorial preference is **journal articles first**. This is a reading
and resource-allocation policy, not an intrinsic-quality verdict or a replacement
for the existing technical scores. No record is removed. `Papers` has five new
priority columns; the filterable `ReadingPriority` sheet gives all 208 decisions.
The timeline defaults to journal-first sorting, displays each label, and can show
only journals, only supplementary theses, hide theses, or inspect type conflicts.
Its filtered CSV export includes the priority, degree and exception fields.

Five degree theses are marked **supplementary / low priority**. None has a currently
established milestone/high-influence exception. Citation values below are the
existing work-specific OpenAlex snapshots from 16 October 2026, not fresh queries,
cross-database totals or proof of research quality. An observed zero is not proof
that a work has never influenced anyone.

| Work | Degree | Snapshot citations | Reading decision |
| --- | --- | --- | --- |
| Lori J. Erickson (1995), *A Monte Carlo approach to modeling lost person behavior in wilderness areas using a geographic information system* | MS; [official catalogue](https://libcat.library.tamu.edu/Record/in00001302822/Details) | 0 | Historical lead only; supplementary, not a priority full-text recovery task absent a demonstrated exception. |
| Jared Doke (2012), *Analysis of Search Incidents and Lost Person Behavior in Yosemite National Park* | MA; [official KU item metadata](https://kuscholarworks.ku.edu/server/api/core/items/62124f5b-087e-4cc2-a85c-cbed866e42a3) | 15 | Prefer the related [2014 Applied Geography article](https://doi.org/10.1016/j.apgeog.2013.11.001), already in the pool; thesis/article equivalence and cohort independence remain unproven. |
| Wallizada Mohibullah (2017), *Agent-based lost person movement modelling, prediction and search in wilderness* | Doctoral; [UCL repository](https://discovery.ucl.ac.uk/id/eprint/1542167/) | 3 | Retain bounded method leads, not a core progress anchor on current evidence. |
| Kyle Harrington (2018), *Decision making within missing person incidents* | PhD; [official thesis source](https://repository.nottingham.ac.uk/server/api/core/bitstreams/ced2a82f-6ab8-443a-a4fb-e83b475b54cf/content) | 1 | Supplementary decision background; prefer the related [2018 journal article](https://doi.org/10.1007/s10111-018-0515-x) for future reading. That external candidate is not silently added to the 208 or certified to cover the entire thesis. |
| Scott Duncan (2020), *Unsolvable? Assessing the Accuracy of Missing Person Case Data* | PhD; [NSU repository](https://nsuworks.nova.edu/fse_etd/256/) | 5 | Supplementary data-quality context; less direct to the motion-prediction/search-method core. |

The 134 `article` records with `journal` venues receive `journal_first`; two further
`journal` venues have conflicting `conference-paper` source types and remain
`type_review_needed`, not silently promoted. The other 67 records remain
content-assessed research, including major conferences and foundational books;
non-journal does not automatically mean low research value. A journal article
reproduced inside an author's thesis remains a journal article, not a degree thesis.

Thesis exceptions require explicit manual evidence of substantive milestone or
actual-adoption importance and high influence interpreted in the work's field and
era; no universal citation threshold is invented. The manifest records the policy,
the five degree-identification sources, snapshot dates and empty exception list.
The added `editorial_screening` field in the public records is clearly separated
from identity, impact, evidence status, technical claims and milestone scores.

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
