"""Reject unresolved references, missing glyphs and significant clipped text."""
import argparse
from pathlib import Path
import re


def validate_log(text, maximum_overfull_pt=2.0):
    if re.search(r'undefined (?:references|citations)|undefined on input line|Rerun to get|Missing character:', text, re.I):
        raise ValueError('PIRC26_TEX: unresolved reference/citation or missing glyph')
    overfull = [float(v) for v in re.findall(r'Overfull \\[hv]box \(([0-9]+(?:\.[0-9]+)?)pt too (?:wide|high)\)', text)]
    if any(value > maximum_overfull_pt for value in overfull):
        raise ValueError('PIRC26_TEX: significant overfull box')
    return {'max_overfull_pt': max(overfull, default=0.), 'threshold_pt': maximum_overfull_pt}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('logs', nargs='+', type=Path)
    args = parser.parse_args()
    for path in args.logs:
        result = validate_log(path.read_text(encoding='utf8', errors='replace'))
        print(str(path) + ': PIRC-26 TeX gate passed; max overflow ' + str(result['max_overfull_pt']) + 'pt')


if __name__ == '__main__':
    main()
