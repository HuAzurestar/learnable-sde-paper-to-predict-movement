# Historical presentation fixture: exact public release 8cbcb114.
# Old monolithic positions are not current six-document acceptance.
# Current source graph, values and layouts: test_pirc17_revision46.py.
import copy
import hashlib
import json
from pathlib import Path
import pytest
from scripts.plot_pirc17_preliminary import absolute_rows, effect_panels, load_snapshot, validate

ROOT = Path(__file__).resolve().parents[1]


def test_complete_original_scope_and_contrast_signs():
    data = load_snapshot()
    assert len(validate(data)) == 28
    assert sum(r["expected"] for r in data["configs"]) == 6440
    assert len(data["comparisons"]) == 21


@pytest.mark.parametrize("field,value", [("missing", 1), ("status", "unavailable"),
                                         ("counts", {"success": 229, "failed": 1})])
def test_failed_or_missing_rows_are_not_charted_as_success(field, value):
    data = copy.deepcopy(load_snapshot())
    data["configs"][0][field] = value
    with pytest.raises(ValueError):
        validate(data)


def test_changed_comparison_sign_is_rejected():
    data = copy.deepcopy(load_snapshot())
    data["comparisons"][0]["delta_estimate_m"] *= -1
    with pytest.raises(ValueError):
        validate(data)


def test_no_final_qualification_is_smuggled_into_stage_renderer():
    data = copy.deepcopy(load_snapshot())
    data["scientific_claim_authorized"] = True
    with pytest.raises(ValueError):
        validate(data)


def test_independent_panel_scales_keep_all_original_comparisons():
    data = load_snapshot()
    panels = effect_panels(data)
    assert len(panels) == 7
    rows = [row for panel in panels for row in panel['rows']]
    assert sorted(row['candidate'] for row in rows) == sorted(row['candidate'] for row in data['comparisons'])
    assert len({row['candidate'] for row in rows}) == 21
    for panel in panels:
        lo, hi = panel['x_limits_m']
        assert lo < 0 < hi
        assert {row['control'] for row in panel['rows']} == {panel['control']}
        for row in panel['rows']:
            assert lo < row['simultaneous_interval_m'][0] <= row['simultaneous_interval_m'][1] < hi
        assert all(lo <= bound <= hi for bound in panel['practical_bounds_visible'])
    assert all(panel['diagnostic_zoom'] for panel in panels[-3:])
    assert all(not panel['practical_bounds_visible'] for panel in panels[-3:])
    assert panels[-1]['x_limits_m'][1] - panels[-1]['x_limits_m'][0] < .001
    assert panels[0]['x_limits_m'][1] - panels[0]['x_limits_m'][0] > 100


def test_only_six_extra_reference_roles_unplotted_without_averaging():
    data = load_snapshot()
    selected = [row for _, row in absolute_rows(data)]
    names = [row['configuration'] for row in selected]
    assert len(names) == len(set(names)) == 22
    assert names[0] == 'arm-01/full'
    assert set(names[1:]) == {row['candidate'] for row in data['comparisons']}
    assert {row['configuration'] for row in data['configs']} - set(names) == {
        'arm-06/dt60', 'arm-07/full', 'arm-11/full', 'arm-16/full', 'arm-18/full', 'arm-20/full'}
    originals = {row['configuration']: row for row in data['configs']}
    assert all(row == originals[row['configuration']] for row in selected)
    assert originals['arm-01/full']['weighted_es_m'] != originals['arm-07/full']['weighted_es_m']


def test_interval_order_is_numeric_not_outcome_sorted_and_sources_unchanged():
    data = load_snapshot()
    names = [row['configuration'] for _, row in absolute_rows(data)
             if row['configuration'].startswith('arm-06/')]
    assert names == ['arm-06/dt30', 'arm-06/dt120', 'arm-06/dt300', 'arm-06/dt600']
    before = copy.deepcopy(data)
    effect_panels(data)
    absolute_rows(data)
    assert data == before


@pytest.mark.parametrize('language', ['en', 'zh'])
def test_all_twenty_eight_absolute_rows_retained_in_bilingual_appendix(language):
    source = ROOT / 'paper/pirc17' / language
    tex = (source / "historical-main-v1.tex").read_text(encoding='utf-8')
    table = (source / 'all-method-absolute.tex').read_text(encoding='utf-8')
    assert r'\input{all-method-absolute.tex}' in tex
    assert table.count(r'\label{tab:all-method-absolute}') == 1
    assert table.count(r'\texttt{arm-') == 28
    for row in load_snapshot()['configs']:
        name = row['configuration'].replace('_', r'\_')
        expected = (r'\texttt{' + name + '} & ' +
                    f"{row['weighted_es_m']:.1f} & {row['ade_m']:.1f} & {row['fde_m']:.1f}")
        assert expected in table
    if language == 'en':
        assert 'different horizontal' in tex and 'diagnostic zooms' in tex
        assert 'not averaged' in tex and '(continued)' in table
    else:
        assert '不同横轴尺度' in tex and '不平均' in tex and '续表' in table


def test_manifest_and_appendix_bindings_without_qualification():
    paper = ROOT / 'paper/pirc17'
    path = paper / 'figures/preliminary-figure-manifest.json'
    manifest = json.loads(path.read_text(encoding='utf-8'))
    entry = json.loads((paper / 'claim-ledger.json').read_text(encoding='utf-8'))['reader_presentation']
    assert entry['figure_manifest_sha256'] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert entry['renderer_sha256'] == manifest['renderer_sha256']
    assert manifest['renderer_sha256'] == hashlib.sha256((ROOT / 'scripts/plot_pirc17_preliminary.py').read_bytes()).hexdigest()
    assert manifest['schema_version'] == 'pirc17-preliminary-presentation-figures-v2'
    assert len(manifest['effects_panels']) == 7
    assert len(manifest['absolute_display_slots']) == 22
    assert len(manifest['absolute_unplotted_slots']) == 6
    assert not manifest['repeated_control_metrics_averaged']
    for name, files in manifest['figures'].items():
        assert files['pdf'] == hashlib.sha256((paper / 'figures' / (name+'.pdf')).read_bytes()).hexdigest()
    for language in ['en', 'zh']:
        assert entry['appendix_table_file_sha256'][language] == hashlib.sha256((paper / language / 'all-method-absolute.tex').read_bytes()).hexdigest()
    for key in ['new_forecasts', 'new_fits', 'new_scores', 'new_statistical_inference']:
        assert manifest[key] == 0
    assert not manifest['final_audit_completed'] and not manifest['scientific_claim_authorized']
    assert not entry['diagnostic_zoom_is_practical_effect_evidence']
    assert not entry['final_qualified_claims_added']
