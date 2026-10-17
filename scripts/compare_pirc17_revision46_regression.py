"""Compare actual complete regression runs without suppressing baseline failures."""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def read(path):
    root=ET.parse(path).getroot()
    suites=[n for n in root.iter("testsuite")]
    states={state:[] for state in ("failure","error","skipped")}
    cases=list(root.iter("testcase"))
    for case in cases:
        for state in states:
            if case.find(state) is not None:
                states[state].append(case.attrib.get("classname","")+"::"+case.attrib["name"])
    return {"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
            "passed":len(cases)-sum(len(v) for v in states.values()),
            "failed":len(states["failure"]),"errors":len(states["error"]),
            "skipped":len(states["skipped"]),"states":{k:sorted(v) for k,v in states.items()},
            "seconds":sum(float(s.attrib.get("time",0)) for s in suites)}


def compare(baseline,current,output):
    if output.exists():
        raise ValueError("Use a new regression comparison version")
    b,c=read(baseline),read(current)
    introduced={k:sorted(set(c["states"][k])-set(b["states"][k])) for k in ("failure","error")}
    assert b["failed"]==25 and b["errors"]==2 and b["skipped"]==0
    value={"schema_version":"pirc17-revision46-regression-comparison-v1",
           "baseline_commit":"8cbcb1140d804b25b553ab4e7cda0be3a0d34b1b",
           "baseline":b,"current":c,"introduced_failures_or_errors":introduced,
           "whole_suite_passed":c["failed"]==c["errors"]==0,
           "no_new_failures":not any(introduced.values()),"collection_errors_not_excluded":True,
           "command":"python -m pytest -q --continue-on-collection-errors --junitxml=<external-output>",
           "scientific_runs_or_resampling":0,"human_acceptance":False}
    output.write_text(json.dumps(value,indent=2)+"\n",encoding="utf-8")
    print({"baseline":(b["passed"],b["failed"],b["errors"]),"current":(c["passed"],c["failed"],c["errors"]),
           "introduced":introduced,"whole_suite_passed":value["whole_suite_passed"]})


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("baseline","current","output"):
        parser.add_argument("--"+name,type=Path,required=True)
    args=parser.parse_args()
    compare(args.baseline,args.current,args.output)
