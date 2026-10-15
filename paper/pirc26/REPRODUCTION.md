# Actual controls and limitations

## Environment and source binding

Research used Python 3.10.13, Windows AMD64, CPU float64, one numerical thread,
torch 2.3.1+cu121, numpy 1.26.4, torchsde 0.2.6 and trampoline 0.1.2. The CUDA
build string does not mean GPU execution. Installed torchsde Python-source
catalog hash for G2/G3 is
`23293641e90f37639d33bad8e2e58c907137e57770d545dbc0f45f3f75b0030f`.

New analysis/forecast implementation: Git
`9ce90059f3611089150928d47aaa0393b699a016`, runtime-code hash
`578687236fca88752d9332840f8e108c3580d309a32693547ce108095fcc316f`.
M1 source Git `c0097bb1069131eee87ab45a4daf7ecd538c0a23`, runtime-code hash
`3ce392ca03b649b537c6766e37402e0597fdda7d110243ca16cc386b7fc729cb`.
Engineering PR27 merge is not a retroactive scientific-source replacement.

## M1 authored recipe

Teacher: A=-0.5I, B=-0.125I, a=0,
L=[[0.125,0],[0.03125,0.125]], identity normalization, no context.
Residual depends only on vx. Seven coefficient rows are
[[0.25,-0.125],[-0.125,0.25],[0.375,0.125],[-0.25,-0.25],
[0.125,0.375],[0.25,-0.125],[-0.125,0.25]].
Spline degree 3, open knots [-2,-2,-2,-2,-1,0,1,2,2,2,2];
RBF centers [-1.5,-1,-0.5,0,0.5,1,1.5], width 0.5.
Initial x=y=vy=0, 65 equally spaced vx in [-1.875,1.875].
Seeds 26091011 through 26091015; dt 0.02/0.1; paths 64/256 nested with
common noise. Teacher is discrete Euler; affine and diffusion are fixed.
QR fitting uses ridge=curvature=0, condition limit 1e6, maximum batch 4096.
The full seven free basis coefficients are used. Recovery requires
relative residual-field RMSE<=0.25 AND coefficient-relative-L2<=0.5 for all 20 matched settings.
Operator archive: `8bd1ecda3d7614e87e260bbfc67aef96c8d6a562fc427679a9e8c0217e9172a9`.
Changing the frozen criterion or discarding failed settings is not reproduction.

## Authored neural O1/O2 recipe

Two hidden layers of width 16, all four state features, no context, identity
normalization, spectral bound=amplitude=alpha=1. Teacher A=-0.3I, B=-0.02I,
a=[0.1,-0.05], L=[[0.1,0],[0.025,0.1]], teacher seed 26101401.
Teacher last weight is 0.25*(arange(32).reshape(2,16)/31-0.5),
last bias [0.2,-0.1]. Seeds 26101411/12/13.
O1 uses 16 Cartesian {-1,1}^4 origins, 32 one-Euler-step paths, dt=0.1,
512 transitions; max steps=patience=40, learning rate 0.005, tolerance zero,
diffusion frozen. Actual preparation artifact:
`ff60c4ed6a48f8460582416c660e3cecc8b62b0ec8856da6ad957526eb28cc83`.

O2 has two fixed training and two fixed challenge origins; teacher two paths on
a 0.125-second grid from zero through 30 seconds, fixed target sample zero.
Fit dt=0.25/0.125, 8 paths, horizons 10/30 seconds, max steps=patience=12,
learning rate 0.005, tolerance zero, gradient clip 100, six-step curriculum,
grid limit 256, gradient-state limit 262144. Best checkpoint is the fixed
all-training-origin/all-horizon independent-Brownian monitor, never challenge
selection. Training grids are not pathwise coupled.
Each score is the two-dimensional position marginal at one selected horizon;
the objective averages those scores, not a score of a concatenated path vector.
Cross-time joint dependence is not separately validated by this objective.
Four FD coordinates: affine.a[0], last.bias[0], last.weight[0,0],
first.weight[0,0]; central epsilon=1e-5, atol=1e-5, rtol=1e-3, restore checkpoint.
Fit wall<=600 seconds and measured lifetime RSS<=2 GiB qualify small-case
feasibility, not convergence or additional termination budgets.
Initial operator archive:
`9cbbd7c0123413a07a31385c05a9ac61075900a8aaf1ec2c5f95029e71b46d64`.
Consumer repair SHA-256:
`929d36999e8781fda4de7a2c8141b4d80331c43b3d1c860d9ab64f989ee12e46`.
The repair retains the numerical suffix, math, roots, thresholds and seeds.

## G2/G3 paired gradient recipe

Use the fixed O1 preparation, not trained O2 winners. No model updates or real
data read. Three seeds x two steps x two forward solvers gives 12 pairs.
G2: reversible_heun direct / adjoint_reversible_heun.
G3: midpoint direct / midpoint continuous adjoint.
Eight paths, query times 0/10/30, training origin zero, target fine indices
80/240. Rank-two constant velocity diffusion, Stratonovich=Ito drift.
BrownianInterval halfway_tree=True, tol=1e-9, dt=None, levy_area='none';
entropy SHA(prefix,seed) first 15 hex digits excludes solver/grid/route;
prefix is `pirc26-authored-o2-gradient-routes-20261014-v1`.
Check coarse increments equal fine sums to 1e-9. Actual entropy serialization
and fixed origins are in the controlled archived operator, not reconstructed
from this prose; this document is not a claim of standalone full replication.

Three fresh sequential helper processes per pair: verifier, direct, candidate.
Direct/candidate order is balanced six each. Full nonempty acceleration
gradient, excluding empty context tensors. FD epsilon=1e-5, atol=1e-5,
rtol=1e-3; G2 relative-L2<=1e-3, G3<=0.05. Coordinate tolerances:
G2 atol=1e-5/rtol=1e-3, G3 atol=1e-4/rtol=0.05.
Forward atol=1e-8/rtol=1e-7; direct-repeat relative-L2<=1e-9.
Benchmark wall<=600 seconds and fresh-process lifetime RSS<=2 GiB.
No general memory advantage or asymptotic speed claim.
Operator archive:
`6dbe9963393afb59bd508f2a53f05ad295b3a2baf0d734d812b467f0d026c1d1`.

## Real data and costs

Only the original seven candidates and four-unit training fits; no raw/model
export, new fit, candidate substitution or final-test access. Native truth, no
interpolation, causal origins, 128 common-root paths. Horizon populations and
all absent/failed statuses remain explicit. Exposed 2,000-replicate paired-unit
intervals are conditional, not formal global superiority intervals.

For each segment/horizon, choose the earliest noninitial native observation
whose exact h-second endpoint is also observed. Score fine-grid predictions at
all native observations strictly after that origin through the endpoint,
including the endpoint. Average Energy scores equally over these native times,
then equally over segments measured by both models within each original unit,
then equally over original units having at least one paired measured segment.
This is Eq. (real-score) in both manuscripts. Irregular native gaps are not
duration-weighted; internal solver knots and interpolated truth add no score
observations. The fine grid halves each coarse interval and retains native
knots. FDE uses the same paired segment/unit population and weighting but only
the endpoint error of the ensemble mean. No missing cell is assigned zero.

The cumulative 24-hour cap applies separately to each genuine arm, including
preparation/retries/orphan settlements. 7,200-second allocations are soft
report/continuation windows; the earlier 120-second stop was an implementation
error, not the user's cap. No arm reset or rename to evade accumulated cost.
The published cost table is a versioned snapshot through compact evidence;
subsequent paper-build/verification costs require separate settled receipts.

## What this package reproduces

Standard-library tests verify summary hashes, exact denominators, retained
failures, fixed cell order, missingness, budget cap and deterministic formatting.
They do not regenerate observations, numerical gradients, fits or bootstrap
replicates. The seven table sources can be regenerated exactly from the reviewed
summary. Full original payloads/operators remain controlled; independent
scientific validation must identify its inputs, authority, cost and exact source
separately rather than relabel table reconstruction as replication.
