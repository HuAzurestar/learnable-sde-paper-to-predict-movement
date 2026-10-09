"""Record bounded citation-role checks,not a claim of reading all23 full texts."""
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
PAPER=ROOT/"paper/pirc17"

# Primary locations actually checked in this revision. Failed direct fetches
# are distinguished from successful abstract/metadata/documentation access.
CHECKS={
 "johnson2008":("continuous-time movement and irregular observations","https://onlinelibrary.wiley.com/doi/10.1890/07-1032.1","publisher metadata and abstract"),
 "ghahramani2000":("latent switching regimes;not the implemented GMM fit","https://www.cs.toronto.edu/~hinton/absps/switch.pdf","author manuscript title,abstract and introductory model definitions"),
 "avgar2016":("joint environmental selection and movement context","https://besjournals.onlinelibrary.wiley.com/doi/10.1111/2041-210X.12528","publisher metadata and abstract; later direct fetch intermittent"),
 "avgar2017correction":("correction accompanies the step-selection source","https://besjournals.onlinelibrary.wiley.com/doi/10.1111/2041-210X.12725","publisher-indexed correction metadata and correction text"),
 "gupta2018":("trajectory forecasting context;not an executed comparator","https://arxiv.org/abs/1803.10892","author preprint metadata and abstract; CVF direct access failed"),
 "salzmann2020":("dynamically feasible,map-aware forecasting context","https://arxiv.org/abs/2001.03093","author preprint metadata and abstract; ECCV2020 relation stated there"),
 "kidger2021":("SDE path generation/GAN context;not performance on this task","https://proceedings.mlr.press/v139/kidger21b.html","official proceedings metadata and abstract"),
 "gao2024":("interpretable stochastic dynamics identification context","https://www.nature.com/articles/s41467-024-50378-x","publisher-indexed metadata; direct body fetch failed/intermittent"),
 "gneiting2007":("proper scoring and energy-score theory;not calibration certification","https://sites.stat.washington.edu/raftery/Research/PDF/Gneiting2007jasa.pdf","author-hosted published PDF title and abstract"),
 "gneiting2008":("multivariate probabilistic/ensemble forecast evaluation","https://link.springer.com/article/10.1007/s11749-008-0114-x","publisher metadata and abstract"),
 "kloeden1992":("numerical SDE background;not proof of global exactness here","https://link.springer.com/book/10.1007/978-3-662-12616-5","publisher authors,edition/copyright,DOI,description and contents"),
 "nichol2018":("first-order Reptile algorithm context;not semantic mode matching","https://arxiv.org/abs/1803.02999v3","author preprint metadata and abstract;v3 retained"),
 "holm1979":("multiple zero-hypothesis tests,not practical margins","https://www.jstor.org/stable/4615733","stable publisher title only; numerical bibliography retained from original,not freshly full-text verified"),
 "davison1997":("bootstrap background;not a guarantee for this small cohort","https://www.cambridge.org/core/books/bootstrap-methods-and-their-application/ED2FD043579F27952363566DC09CBD6A","publisher page accessible; bibliographic identity retained,not full book read"),
 "noaa":("solar calculation formulas,not physical-clock provenance","https://gml.noaa.gov/grad/solcalc/solareqns.PDF","official two-page equation document"),
 "worldcover2021":("2021v200 product identification,not per-route contemporary truth","https://esa-worldcover.org/en/data-access","official citation section confirms 2022,Zanaga et al.,v200 and DOI7254221; Zenodo fetch failed"),
 "overtureattribution":("source-specific attribution documentation,not route permission","https://docs.overturemaps.org/attribution/","official attribution page;does not certify all redistribution requirements"),
 "hydrorivers2013":("HydroRIVERS hydrography methodology","https://onlinelibrary.wiley.com/doi/10.1002/hyp.9740","publisher metadata and official product citation match 27(15),2171-2186"),
 "hydroriverslicense":("product v1 and licence pointer,not blanket map release approval","https://www.hydrosheds.org/products/hydrorivers","official product,licence and reference sections"),
 "mapzenterrain":("Skadi mixed-source format/distribution,not pure NASA provenance","https://github.com/tilezen/joerd/blob/e3d4351ee3e5be333e23f47cb500e9a7c310656a/docs/formats.md","pinned provider format documentation and AWS registry"),
 "mapzenattribution":("provider-specific upstream attribution","https://github.com/tilezen/joerd/blob/d8f587b73d26e0a0c42cdccd9ae8c55de4197763/docs/attribution.md","pinned provider documentation;not all tile permissions certified"),
 "copernicusdem2021":("GLO-30 Public distribution and 2021 release","https://registry.opendata.aws/copernicus-dem/","official distribution registry product,release and licence pointer"),
 "overture202608":("saved transportation release2026-08-19.0","https://docs.overturemaps.org/blog/2026/08/19/release-notes/","official dated release header and version;not replaced with newer release")}


def verify():
    out=PAPER/"revision46-reference-check-v1.json"
    if out.exists():
        raise ValueError("Use a new check version,never overwrite the historical receipt")
    bibliography=(PAPER/"en/revision46-bibliography.tex").read_bytes()
    assert bibliography == (PAPER/"zh/revision46-bibliography.tex").read_bytes()
    entries=re.findall(r"\\bibitem\{([^}]+)\}([\s\S]*?)(?=\\bibitem|\\end\{thebibliography\})",bibliography.decode())
    assert len(entries)==len(CHECKS)==23 and len({key for key,_ in entries})==23
    for lang in ("en","zh"):
        main=(PAPER/lang/"main.tex").read_text(encoding="utf-8")
        cited={key for group in re.findall(r"\\cite\{([^}]+)\}",main) for key in group.split(",")}
        assert cited==set(CHECKS)
    records=[{"key":key,"entry_sha256":hashlib.sha256(text.encode()).hexdigest(),
              "role":CHECKS[key][0],"primary_check_url":CHECKS[key][1],"actual_scope":CHECKS[key][2],
              "full_text_read_this_revision":False,"executed_performance_baseline":False} for key,text in entries]
    value={"schema_version":"pirc17-revision46-reference-check-v1","checked_date":"2026-10-09",
           "bibliography_sha256":hashlib.sha256(bibliography).hexdigest(),"entries":records,
           "all23_unique_and_cited_in_each_current_body":True,"all23_full_text_read":False,
           "journal_specific_style_finalized":False,"route_publication_authorized":False,
           "original_bibliography_access_dates_preserved":True}
    out.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("23 unique bilingual citations with bounded primary-source roles;no full-text or licence certification.")


if __name__=="__main__":
    verify()
