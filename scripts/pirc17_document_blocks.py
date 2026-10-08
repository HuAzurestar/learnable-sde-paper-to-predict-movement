"""Pure guard: named verbatim relocations and two verified later additions."""
HISTORY_TABLES = ("tab:history-spans", "tab:development-history-spans")
POPULATION_TABLES = ("tab:final-cohort-durations", "tab:final-cohort-speeds", "tab:final-cohort-geography")
POPULATION_EQUATIONS = ("eq:cohort-window-speed",)
LATER_TABLES = ("tab:source-sequence-screen", "tab:terminal-score-inventory")


def assert_preserved_blocks(before, after, kind):
    """Require exact bytes/count/order except the explicitly relocated tables.

    Callers extract complete TeX environments and handle their own separately
    verified later additions first. This is not a broad unordered-set check.
    No document, scientific artifact or process is changed by this helper.
    """
    old, new = list(before), list(after)
    if kind == "table":
        for label in LATER_TABLES:
            needle = r"\label{" + label + "}"
            old_matches = [block for block in old if needle in block]
            new_matches = [block for block in new if needle in block]
            assert len(old_matches) <= 1 and len(new_matches) <= 1, (label, "duplicate table")
            if old_matches:
                # Once present in a baseline, even this addition is immutable.
                assert old_matches == new_matches, (label, "changed or missing addition")
            else:
                for block in new_matches:
                    new.remove(block)
        for label in HISTORY_TABLES + POPULATION_TABLES:
            needle = r"\label{" + label + "}"
            old_matches = [block for block in old if needle in block]
            new_matches = [block for block in new if needle in block]
            assert len(old_matches) <= 1, (label, "duplicate original")
            assert old_matches == new_matches, (label, "changed, missing or duplicate relocated table")
            for block in old_matches:
                old.remove(block)
                new.remove(block)
    if kind == "equation":
        for label in POPULATION_EQUATIONS:
            needle = r"\label{" + label + "}"
            old_matches = [block for block in old if needle in block]
            new_matches = [block for block in new if needle in block]
            assert len(old_matches) <= 1, (label, "duplicate original")
            assert old_matches == new_matches, (label, "changed, missing or duplicate relocated equation")
            for block in old_matches:
                old.remove(block)
                new.remove(block)
    assert old == new, (kind, "other scientific blocks changed or reordered")
