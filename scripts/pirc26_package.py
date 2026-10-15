"""Validate/rebuild the reviewed PIRC-26 aggregate-only paper package.

No research runtime, raw data, simulator or scientific re-estimation is used.
"""
import argparse
import json
from pathlib import Path

from pirc26.evidence import encoded, render_tables, claim_index, validate_summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='compare without writing')
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1] / 'paper/pirc26')
    args = parser.parse_args()
    evidence = json.loads((args.root / 'evidence/summary.json').read_text(encoding='utf8'))
    validate_summary(evidence)
    tables = render_tables(evidence)
    outputs = {**{'shared/' + name: body.encode('utf8') for name, body in tables.items()},
               'evidence/claims.json': encoded(claim_index(evidence, tables)) + b'\n'}
    for name, body in outputs.items():
        path = args.root / name
        if args.check:
            if not path.is_file() or path.read_bytes().replace(b'\r\n', b'\n') != body:
                raise ValueError('PIRC26_PACKAGE_MISMATCH: ' + name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
    print('PIRC-26 aggregate package ' + ('verified' if args.check else 'rebuilt') + '; no numerical experiment rerun')


if __name__ == '__main__':
    main()
