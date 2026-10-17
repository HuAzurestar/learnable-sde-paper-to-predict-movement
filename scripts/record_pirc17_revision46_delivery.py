"""Record editor-reviewed implementation, never human/scientific acceptance.

Preserve every original criterion and all 42 mappings. Concrete unfinished
criteria stay unfinished; describing an unknown is not solving that unknown.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper/pirc17"
FIGURES = dict(zip(
    [f"G{i:02d}" for i in range(1,12)]+["G13"],
    ["geometry","design-matrix","population","inertial-horizons",
     "score-error-tradeoff","seeds-and-blocks","history-timeline",
     "development-fit","recorded-runtime","metric-overview",
     "practical-effects","family-availability"]))
ANCHORS = {
 "O01":"main:sec:terrain-results", "O02":"audit:sec:audited-review-update",
 "O03":"supplement:sec:method-model", "O04":"main:tab:actual-changes",
 "O05":"main:fig:inertial", "O06":"supplement:fig:terrain-matrix",
 "O07":"main:sec:protocol", "O08":"main:sec:introduction",
 "R01":"main:fig:practical-effects", "R02":"supplement:eq:segment-rank-mode",
 "R03":"main:tab:inputs", "R04":"main:tab:actual-changes",
 "R05":"main:sec:models", "R06":"main:eq:constant-penalty",
 "R07":"main:sec:models", "R08":"main:sec:protocol",
 "R09":"main:fig:population", "R10":"main:tab:point-errors",
 "R11":"supplement:sec:decision-conditions", "R12":"main:sec:protocol",
 "R13":"audit:sec:terminal-failures", "R14":"main:sec:case-horizons",
 "R15":"supplement:fig:preliminary-full-horizons", "R16":"supplement:fig:method-overview",
 "R17":"audit:sec:audited-review-update", "X01":"supplement:sec:follow-up-designs",
 "X02":"supplement:eq:terrain-rate-Q", "X03":"main:sec:models",
 "X04":"main:sec:introduction", "X05":"audit:sec:audited-review-update",
 "X06":"audit:sec:audited-review-update", "X07":"main:sec:models",
 "X08":"audit:sec:audited-review-update"}


def record(inspection,local_manifest):
    output=PAPER/"revision46-response-v2.json"
    if output.exists():
        import subprocess
        tracked=subprocess.run(["git","ls-files","--error-unmatch",str(output.relative_to(ROOT))],
                               cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        if tracked.returncode==0:
            raise ValueError("Committed delivery records are versioned, not overwritten")
    value=json.loads((PAPER/"revision46-response-v1.json").read_text(encoding="utf-8"))
    value["schema_version"]="pirc17-revision46-response-v2"
    publication=json.loads((PAPER/"revision46-review-v1/build-manifest.json").read_text(encoding="utf-8"))
    layouts=json.loads(inspection.read_text(encoding="utf-8"))
    local=json.loads(local_manifest.read_text(encoding="utf-8"))
    assert len(layouts["documents"])==6 and all(not d["text_outside_page"] for d in layouts["documents"])
    assert local["new_fits_forecasts_scores_map_queries_or_resampling"]==0
    assert local["public_distribution_authorized"] is False
    # These are document-review outcomes, not a claim to have recovered
    # absent physical-clock provenance, intermediate models or raw traces.
    unresolved={"R02","R08","R09","R11","X01","X03","X04","X05"}
    pending=[]
    for task in value["tasks"]:
        ident=task["id"]
        evidence=[]
        if ident in FIGURES:
            evidence.append("paper/pirc17/figures/revision46-v1/revision46-"+FIGURES[ident]+".pdf")
            evidence.append("scripts/plot_pirc17_revision46.py")
        elif ident=="G12":
            evidence += ["scripts/build_pirc17_revision46_local.py","scripts/check_pirc17_revision46_local_cases.py"]
        else:
            kind,label=ANCHORS[ident].split(":",1)
            entry={"main":"main","supplement":"supplement","audit":"audit-notes"}[kind]
            evidence += [f"paper/pirc17/{lang}/{entry}.tex#{label}" for lang in ("en","zh")]
        evidence += ["paper/pirc17/revision46-source-migration.json","tests/test_pirc17_revision46.py"]
        for item in evidence:
            parts=item.split("#",1)
            source=ROOT/parts[0]
            assert source.exists(), item
            if len(parts)==2:
                content=source.read_text(encoding="utf-8")
                if "supplement.tex" in parts[0]:
                    content+=(source.parent/"revision46-supplement-retained.tex").read_text(encoding="utf-8")
                if "audit-notes.tex" in parts[0]:
                    content+=(source.parent/"revision46-audit-notes-retained.tex").read_text(encoding="utf-8")
                assert "{"+parts[1]+"}" in content,item
        task.update(editing="implemented_local_only" if ident=="G12" else "implemented",
                    verification="editor_reviewed_with_disclosed_limits",evidence=evidence,
                    human_accepted=False)
        task["remaining_scientific_gaps"]=(["Original scientific unknowns retained; see named sources and N01-N05. No new experiment or provenance certification."] if ident in unresolved else [])
        for i,check in enumerate(task["checklist"]):
            check["status"]="editor_reviewed_document_scope"
            check["evidence"]=list(evidence)
            if ident=="O08" and "非项目读者" in check["criterion"]:
                check["status"]="pending_independent_reader_feedback"
            if ident=="X06" and "作者姓名" in check["criterion"]:
                check["status"]="pending_true_author_confirmation"
            if ident=="R08" and i==0:
                check["status"]="source_provenance_unresolved_nominal_clock_fallback_applied"
            if check["status"].startswith("pending_"):
                pending.append({"task":ident,"criterion":check["criterion"],"status":check["status"]})
    assert len(value["tasks"])==46 and sum(len(t["checklist"]) for t in value["tasks"])==305
    assert len(value["original42_mapping"])==42
    value.update(editing_complete=True,verification_complete=False,
        pending_criteria=pending,original42_accepted=0,human_accepted=False,
        scientific_gaps_solved_by_prose=False,new_experiments=0,
        verification_definition="Editor reviewed source, numeric guards, strict PDFs and layout; not independent reader, author, scientific or human acceptance.",
        public_build_manifest="paper/pirc17/revision46-review-v1/build-manifest.json",
        local_build_manifest_sha256=hashlib.sha256(local_manifest.read_bytes()).hexdigest(),
        public_pages={r["language"]+"/"+r["entry"]:r["pages"] for r in publication["manuscripts"]},
        layout_review={"all_212_pages_contact_sheet_reviewed":True,"text_outside_page":0,
            "reading_size_spot_checks":"main overview, tradeoff and corrected axis; all new figure source panels inspected",
            "retained_layout_limits":["Separate supplement float pages; section openings may follow a figure-only page.","A historical longtable starts with one row then continues with repeated headings.","English main final page contains one reference; font and margins were not reduced."],
            "no_claim_all_pages_full_text_independently_reviewed":True},
        paper_pr_delivered=False,MPA_master_merged=False)
    output.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("46 implemented editor-reviewed cards;305 preserved criteria;42 mapped;2 pending human-information criteria;not acceptance")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inspection",type=Path,required=True)
    parser.add_argument("--local-manifest",type=Path,required=True)
    args=parser.parse_args()
    record(args.inspection,args.local_manifest)
