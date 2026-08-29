# Formalized core

`lean/e-series` contains the Lean4 source supplied with the NEX-345 v4.2
manuscript. It formalizes the measure-algebraic core used for the dual evidence
conditioning results. The manuscript states the boundary explicitly: analytic
PDE existence and Doob `h`-transform results are documented mathematical
arguments, not Lean formalizations in this directory.

The supplied build record reports Lean 4.33.0 / mathlib v4.33.0, a successful
`lake build`, and no custom axioms or proof placeholders in the source. Re-run
the build in a controlled Lean environment before treating that record as fresh
verification.
