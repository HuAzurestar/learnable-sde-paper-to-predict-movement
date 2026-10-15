"""Reader-facing names only; never rename scientific input keys or compare arms."""
from __future__ import annotations

import re

TERRAIN_NAMES = {
    "base": "B (history)", "all-terrain": "A (all groups)",
    "loo-road": "A - road", "loo-river": "A - river",
    "loo-worldcover": "A - cover", "loo-surface": "A - surface",
    "lio-road": "B + road", "lio-river": "B + river",
    "lio-worldcover": "B + cover", "lio-surface": "B + surface",
}

VARIANTS = {
    "pointwise": "Heading/redraw", "pointwise_mixture": "Heading/redraw",
    "single_gaussian": "Single Gaussian", "gmm_kernel": "RDM",
    "explicit_decomp": "Speed/radial", "qmle": "QMLE label",
    "mixed": "Mixed calibration", "pure_es": "ES calibration",
    "d2_mc": "2D MC score", "d2_closed": "2D closed score",
    "scratch": "Scratch", "reptile": "Reptile", "drift_only": "Drift-only",
    "two_step": "Two-step", "em": "Euler-M.", "euler": "Euler alias",
    "mc": "MC", "crn": "CRN",
}


def method_name(arm: str, variant: str) -> str:
    if variant == "full":
        return "HSM-" + arm
    if re.fullmatch(r"dt\d+", variant):
        return "Obs " + variant[2:] + " s"
    if variant not in VARIANTS:
        raise ValueError("unmapped scientific arm: " + arm + "/" + variant)
    return VARIANTS[variant]


def display_text(text: str, *, terrain_codes: bool = True) -> str:
    """Translate complete visible names, leaving numbers and ordinary 'full' alone.

    The raw-to-display crosswalk is recorded separately. Only presentation
    strings are passed here: source JSON/configuration identities are untouched.
    """
    value = re.sub(r"arm-(\d{2})/((?:[a-z0-9_]|\\_)+)",
                   lambda m: method_name(m[1], m[2].replace(r"\_", "_")), text)
    # TeX-escaped variant names can also occur in retained tables.
    for old in sorted(VARIANTS, key=len, reverse=True):
        if old in {"mc", "crn", "em", "euler", "mixed", "scratch", "reptile"}:
            continue  # Avoid altering normal prose or mathematical variable names.
        for spelling in (old, old.replace("_", r"\_")):
            value = re.sub(r"(?<![A-Za-z0-9_])" + re.escape(spelling) + r"(?![A-Za-z0-9_])",
                           lambda _: VARIANTS[old], value)
    value = re.sub(r"\bFull(\d{2})\b", r"HSM-\1", value, flags=re.ASCII)
    value = value.replace("Full coverage percentages", "Complete coverage percentages")
    value = re.sub(r"\bGMM(?: kernel)?\b", "RDM", value, flags=re.ASCII)
    value = re.sub(r"\bResidual mixture\b", "RDM", value, flags=re.ASCII)
    value = re.sub(r"\bFull\b", "HSM", value, flags=re.ASCII)
    value = value.replace("Euler (EM alias)", "Euler alias")
    value = re.sub(r"\bEM(?=\s*\(HSM-\d{2} control\))", "Euler-M.", value, flags=re.ASCII)
    value = re.sub(r"\b(?:Inertial|inertial)\b", "CV", value, flags=re.ASCII)
    value = re.sub(r"\bPointwise mixture\b", "Heading/redraw", value, flags=re.ASCII)
    value = re.sub(r"\bExplicit features\b", "Speed/radial", value, flags=re.ASCII)
    value = re.sub(r"\bdt(\d+)\b", r"Obs \1 s", value, flags=re.ASCII)
    if terrain_codes:
        for old in sorted(TERRAIN_NAMES, key=len, reverse=True):
            value = re.sub(r"(?<![\w-])" + re.escape(old) + r"(?![\w-])",
                           lambda _: TERRAIN_NAMES[old], value)
    return value


def figure_text(text: str) -> str:
    """Use canonical variant labels in annotations and tick formatters alike.

    Unlike prose, a standalone plot label such as 'mixed' or 'em' is an
    experimental variant name. Its descriptive spelling must not depend on
    which historical plotting function originally created it.
    """
    value = display_text(text)
    aliases = {**VARIANTS, "explicit": "Speed/radial", "Explicit": "Speed/radial",
               "single Gaussian": "Single Gaussian", "EM": "Euler-M.",
               "QMLE": "QMLE label", "Scratch adaptation": "Scratch",
               "Reptile initialization": "Reptile", "Drift-only blend": "Drift-only",
               "Two-step label": "Two-step", "Pure ES calibration": "ES calibration",
               "d2 MC score route": "2D MC score", "d2 closed score route": "2D closed score"}
    if value in aliases:
        return aliases[value]
    contrast = re.fullmatch(r"([A-Za-z0-9_]+)(\s*[−-]\s*HSM-\d{2}.*)", value)
    if contrast and contrast[1] in aliases:
        return aliases[contrast[1]] + contrast[2]
    observations = re.fullmatch(r"(\d+) s observations", value)
    if observations:
        return "Obs " + observations[1] + " s"
    return value


def tex_display(text: str) -> str:
    """Keep TeX paths, labels and commands intact while changing printed names."""
    protected = []
    pattern = r"\\(?:label|hypertarget|hyperlink|ref|eqref|autoref|input|includegraphics|path|url|href)\s*(?:\[[^\]]*\])?\{[^}]*\}|\\[A-Za-z]+"

    def hold(match):
        protected.append(match[0])
        return "\x00" + str(len(protected)-1) + "\x00"

    value = re.sub(pattern, hold, text)
    # Raw saved identifiers in tables are evidence keys, not parameter values.
    value = display_text(value, terrain_codes=False)
    value = re.sub(r"\x00(\d+)\x00", lambda m: protected[int(m[1])], value)
    # A table's first cell is a display label, not ordinary narrative prose.
    # In particular standalone EM here is the integration arm; narrative EM
    # about mixture-likelihood fitting and mathematical EM subscripts stay intact.
    lines = []
    for line in value.splitlines(keepends=True):
        if "&" in line and re.fullmatch(r"[A-Za-z][A-Za-z0-9_ .()/−-]*", line.split("&", 1)[0].strip()):
            first, remaining = line.split("&", 1)
            leading = first[:len(first)-len(first.lstrip())]
            trailing = first[len(first.rstrip()):]
            first = leading + figure_text(first.strip()) + trailing
            line = first + "&" + remaining
        lines.append(line)
    return "".join(lines)
