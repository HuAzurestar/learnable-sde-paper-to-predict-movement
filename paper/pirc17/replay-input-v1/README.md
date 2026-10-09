# Original anonymous saved-score replay input

This package publishes the **unchanged existing** anonymous aggregate export,
not new predictions, a model checkpoint, raw GPX or synthetic empirical data.
The gzip is 10,601,386 bytes; its decoded JSON is exactly 65,494,805 bytes.
It retains all 11,368 saved-score rows (11,363 successful and five failed),
anonymous block/origin and seed membership, the registered numerical witnesses,
original paired/statistical summaries and original timing limitations.
These are repeated forecast evaluations, not 11,368 independent participants.

| Binding | SHA-256 |
| --- | --- |
| Gzip transport | `3f2477689aef427ba85f8bd0232f8c75cf3da44fdf14038cc1eef720a865a3b6` |
| Decoded original file | `f15578e9da655a2e2df6601427724d11c2ee6effe200e78846bddde54c7fc75e` |
| Original export content | `29cb892f47301365b3d7b9a2871f3f71d85fe297f7720d0c6489648f8a4d0c50` |
| Original saved-output audit | `8ff917ad6db55bb3b058b51412ab2e76154ba8bd38c754dd60829db74e25ec67` |
| Original analysis | `d1d67a3bf4cd08d46f7e73f0178950b047197275f3f32e29a61f3f699fe5febc` |

Compression stores neither a filename nor a timestamp. Decompression restores
the original bytes, including its original serialization; it does not re-encode,
repair, replace failures, bootstrap, re-score particles or change any verdict.
Content and file pins are frozen in `scripts/pirc17_replay_input.py`, independently
of the transport manifest. The reader bounds compressed and expanded size to
128 MiB and inspects all decoded structured keys/strings for private data or
credentials. The public-release scan also inspects this gzip instead of treating
it as an opaque binary. Other gzip paths are not permitted by that scan.

No original identifiers, coordinates, GPX, map images, model parameters,
particle arrays or workstation paths are supplied. Ordinal block/origin IDs
allow paired arithmetic, not geographic or participant identification. The
private raw saved-output audit, original trajectories and twelve real route/map
figures remain private. The original qualification and non-acceptance flags
remain unchanged; publication does not constitute scientific or human approval.

## Rebuild the saved CRPS and endpoint-quantile tables

From the TSDE repository root, with Python 3.10 or later, standard library only:

```powershell
python -I scripts/pirc17_replay_input.py verify --directory paper/pirc17/replay-input-v1
New-Item -ItemType Directory -Force .tmp
python -I scripts/pirc17_replay_input.py unpack --directory paper/pirc17/replay-input-v1 --output .tmp/pirc17-export.json
python -I scripts/project_pirc17_secondary_scores.py --input .tmp/pirc17-export.json --sha256 29cb892f47301365b3d7b9a2871f3f71d85fe297f7720d0c6489648f8a4d0c50 --output-directory .tmp/pirc17-secondary-rebuilt
python -I -c "import json; from pathlib import Path; a=Path('paper/pirc17/secondary-scores-v1'); b=Path('.tmp/pirc17-secondary-rebuilt'); names=list(json.loads((a/'manifest.json').read_bytes())['payload']['files'])+['manifest.json']; assert all((a/n).read_bytes()==(b/n).read_bytes() for n in names); print('All six generated files are byte-identical')"
```

Use a new output filename/directory on a repeat run: the commands do not
overwrite original evidence. Expected projection content hash is
`f0cae23999322c49575e2b95d41b4713836666a5d02f0c55af8cc306167e92ac`;
120 configuration/mode views and 480 time views, including five unavailable
configuration views. Both CSVs, projection JSON, bilingual table fragments
and generated manifest must exactly match the committed package. Quantile
entries are means of saved within-forecast particle error quantiles, not pooled
quantiles or predictive-disk radii. This command runs no resampling or forecasts.

## Remaining full-paper reproducibility work

The standard-library diagnostic rebuild above is complete. A separate
[clean public paired replay](../public-paired-replay-v1/README.md) now reproduces
all 90 comparisons and 120 metric views, canonically identical to the original,
in a new NumPy-only environment. It compiles unchanged selected definitions
from hash-pinned public PSDE source and verifies the frozen policy; it does not
modify the sealed producer or pretend its heavyweight CLI has no backend
dependencies. Original fixed statistical streams are replayed, not retuned.
This still does **not** certify a complete public end-to-end rebuild of all
sixteen tables, sixteen figure groups and PDFs. Existing TEST-02 receipts
and the new arithmetic proof do not replace raw-source or human acceptance.
No gate is waived or claimed green.

Final review-response adjudication, manuscript cleanup, verified authorship,
privacy/map publication decisions and actual human acceptance remain required.
