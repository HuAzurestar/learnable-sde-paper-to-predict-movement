# Historical presentation fixture: exact public release 8cbcb114.
# Old monolithic positions are not current six-document acceptance.
# Current source graph, values and layouts: test_pirc17_revision46.py.
"""Citation trace and saved-source boundaries, not a literature or licence audit."""
import hashlib
import json
from pathlib import Path
import re

import pytest

PAPER = Path(__file__).resolve().parents[1] / "paper/pirc17"


def manuscript(language):
    return (PAPER / language / "historical-main-v1.tex").read_text(encoding="utf-8")


def bibliography(language):
    text = manuscript(language).split(r"\begin{thebibliography}{99}", 1)[1]
    return dict(re.findall(r"\\bibitem\{([^}]+)\}(.*?)(?=\\bibitem|\\end\{thebibliography\})",
                           text, re.S))


@pytest.mark.parametrize("language", ["en", "zh"])
def test_all_23_references_are_unique_and_citations_are_resolved_without_orphans(language):
    tex = manuscript(language)
    labels = re.findall(r"\\bibitem\{([^}]+)\}", tex)
    cited = {key for group in re.findall(r"\\cite\{([^}]+)\}", tex) for key in group.split(",")}
    assert len(labels) == len(set(labels)) == 23
    assert set(labels) == cited


def test_every_bibliography_entry_matches_between_languages():
    en, zh = bibliography("en"), bibliography("zh")
    assert en.keys() == zh.keys()
    assert all(" ".join(en[key].split()) == " ".join(zh[key].split()) for key in en)


@pytest.mark.parametrize("language", ["en", "zh"])
def test_model_product_references_are_not_only_background_or_licence_references(language):
    tex = manuscript(language)
    section = tex.split(r"\label{sec:data-reference-roles}", 1)[1].split(r"\subsection{", 1)[0]
    cited = {key for group in re.findall(r"\\cite\{([^}]+)\}", section) for key in group.split(",")}
    assert {"mapzenterrain", "copernicusdem2021", "worldcover2021", "overture202608",
            "hydrorivers2013", "hydroriverslicense", "mapzenattribution", "overtureattribution"} <= cited
    assert "pure NASA SRTM" in section if language == "en" else "纯 NASA SRTM" in section
    assert "not acquisition dates" in section if language == "en" else "不是下载日" in section


@pytest.mark.parametrize("language", ["en", "zh"])
def test_missing_bibliographic_pointers_and_document_versions_are_explicit(language):
    bib = bibliography(language)
    assert "1803.02999v3" in bib["nichol2018"] and "[Preprint]" in bib["nichol2018"]
    assert "10.1017/CBO9780511802843" in bib["davison1997"]
    assert "4615733" in bib["holm1979"]
    assert "(n.d.)" in bib["noaa"] and "7 October 2026" in bib["noaa"]
    assert "e3d4351ee3e5be333e23f47cb500e9a7c310656a" in bib["mapzenterrain"]
    assert "d8f587b73d26e0a0c42cdccd9ae8c55de4197763" in bib["mapzenattribution"]
    assert "2021 release" in bib["copernicusdem2021"]
    assert "2026-08-19.0" in bib["overture202608"]


def test_source_description_preserves_original_receipts_and_unverified_science_permissions():
    d = json.loads((PAPER / "data-reference-description-v1.json").read_text(encoding="utf-8"))
    for key, file in (("original_map_provider_projection_sha256", "map-provider-description-v1.json"),
                      ("original_case_acknowledgement_sha256", "map-source-acknowledgements-v1.json")):
        assert hashlib.sha256((PAPER / file).read_bytes()).hexdigest() == d[key]
    for key in ("all_23_bibliography_entries_full_text_read_this_revision",
                "target_journal_specific_style_finalized", "per_tile_upstream_identity_and_acquisition_epoch_certified",
                "all_redistribution_requirements_verified", "public_case_route_release_authorized",
                "independent_saved_output_audit_completed", "paper_or_human_acceptance_completed"):
        assert d[key] is False
    assert d["new_fits_forecasts_scores_resampling_or_map_queries"] == 0
    srtm = d["model_input_reference_roles"]["srtm_label"]
    assert not srtm["pure_nasa_srtm_provenance_of_all_retained_tiles_established"]
    assert not srtm["documentation_commit_is_assigned_as_data_release"]


@pytest.mark.parametrize("language", ["en", "zh"])
def test_primary_metadata_correction_and_distinct_neural_sde_tasks(language):
    bib = bibliography(language)
    assert bib["avgar2017correction"].lstrip().startswith("(2017). Corrigendum.")
    assert "[Correction to Avgar et al." in bib["avgar2017correction"]
    assert "38th International Conference on Machine Learning" in bib["kidger2021"]
    assert "139, 5453--5463" in bib["kidger2021"]
    section = manuscript(language).split(r"\label{sec:related-work}", 1)[1].split(r"\section{", 1)[0]
    assert "LaGNA" in section and "Wasserstein-GAN" in section
    for phrase in (("self, interaction and diffusion", "distinct objectives",
                    "does not identify", "known", "ground truth")
                   if language == "en" else
                   ("自身、相互作用与扩散", "不同目标", "不识别主体间", "已知真实方程")):
        assert phrase in section


def test_bounded_primary_check_does_not_close_literature_or_scientific_review():
    ledger = json.loads((PAPER / "claim-ledger.json").read_text(encoding="utf-8"))
    revision = ledger["literature_primary_metadata_revision"]
    assert revision["source_base_commit"] == "434d2d99629d59a440772dbb01320f9e7f4902b8"
    assert revision["review_items"] == ["P1-26", "P2-10"]
    assert set(revision["primary_pages"]) == {"avgar2017correction", "kidger2021", "gao2024", "salzmann2020"}
    assert not revision["primary_pages"]["avgar2017correction"]["named_author_added"]
    assert revision["primary_metadata_and_abstract_task_scope_check_not_full_literature_audit"]
    assert not revision["all23_full_texts_or_target_journal_style_verified"]
    assert not revision["external_models_executed_or_journal_quartiles_claimed"]
    assert revision["new_fits_forecasts_scores_resampling_or_map_queries"] == 0
    assert not revision["original_scientific_values_tables_figures_and_protocol_changed"]
    assert not revision["licences_privacy_independent_output_audit_or_final_paper_complete"]
