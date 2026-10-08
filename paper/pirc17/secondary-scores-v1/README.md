# Saved CRPS and endpoint-quantile diagnostics

Pure scalar projection of the unchanged anonymous audited export
`29cb892f47301365b3d7b9a2871f3f71d85fe297f7720d0c6489648f8a4d0c50`
(file SHA-256 `f15578e9da655a2e2df6601427724d11c2ee6effe200e78846bddde54c7fc75e`).
Source analysis `d1d67a3bf4cd08d46f7e73f0178950b047197275f3f32e29a61f3f699fe5febc`,
audit `8ff917ad6db55bb3b058b51412ab2e76154ba8bd38c754dd60829db74e25ec67`.
Projection content SHA-256
`f0cae23999322c49575e2b95d41b4713836666a5d02f0c55af8cc306167e92ac`;
file SHA-256 `47b8ec55940d783012c37b1aa7f1640e15628f280e405fdb500fe976f744d3bc`.

All 11,368 original saved-score rows are accounted for. There are 120
configuration/mode views and 480 repeated time views, not new forecasts or
independent observations. All 40 configurations in each of the three modes
are retained: 28 methods, ten terrain configurations, a diagnostic reference
and deterministic inertial reference. Five configuration/mode views with a
retained failed forecast have no means. Their complete comparison-family
unavailability is unchanged; a successful configuration alone does not
make a failed terrain family valid.

`marginal-crps.csv` contains the local east/north coordinate CRPS at each
original target slot and the range of actual recorded elapsed seconds.
CRPS is in metres, lower is better for its marginal; it is not joint ES,
joint calibration, a rotation-invariant score or a per-horizon hypothesis test.
`endpoint-quantiles.csv` contains the mean-position FDE and **means of the
saved within-forecast particle endpoint-error quantiles** at .50/.90/.95.
These are not quantiles of population FDE, pooled particles, predictive-disk
radii or best-particle paths. Inertial has one deterministic particle, so
its three within-forecast quantiles equal its FDE.

The original rule averages five seeds within each origin, then origins within
each recording-hash block and equally across blocks. Primary configurations
each have 46 blocks × five seeds = 230 forecasts; secondary configurations
have six × five = 30. Inertial has one path per block. The means reproduce
the existing FDE summaries within floating-point roundoff. Original source
scalars, failed dispositions, weights, N, integration step and horizons are
unchanged; no fitting, simulation, particle scoring, resampling or map query.

`en/` and `zh/` contain the compact main-text table for the four models already
used in the preceding horizon/point-error comparison: Full01, GMM, dt300 and
inertial. They are not chosen by the new CRPS/quantile ranking. Complete
all-configuration results remain in both CSVs and `projection.json`.
`manifest.json` pins all five generated files; `README.md` is explanatory.
Original 16 CSVs, 32 figures and 34 TeX fragments remain untouched.

With the original anonymous export available, regenerate using the pure
standard-library consumer from the repository root:

```powershell
python scripts/project_pirc17_secondary_scores.py --input PUBLIC_EXPORT.json --sha256 29cb892f47301365b3d7b9a2871f3f71d85fe297f7720d0c6489648f8a4d0c50 --output-directory NEW_EMPTY_DIRECTORY
```

The full seed-level input is not published here yet; output files alone do
not satisfy final public rebuild requirements. The externally pinned input
is required; an internally self-consistent hash alone is not empirical authority.
All scientific, numerical-convergence, physical-clock, participant-independence
and human-acceptance claims remain unasserted by this descriptive projection.
