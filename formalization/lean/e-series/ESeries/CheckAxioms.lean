import ESeries.Basic
import ESeries.E8

/-! # 公理 / sorry 审计（零自定义公理）

运行 `lake env lean ESeries/CheckAxioms.lean` 应输出各引理仅依赖
`[propext, Classical.choice, Quot.sound]`（Lean 内核自带逻辑公理）。
全文 `grep -E "sorry|admit|axiom|opaque"` 应为 0 处。 -/

#check ESeries.posterior_mixture
#check ESeries.weight_likelihood_ratio
#check ESeries.mixture_tv_bound
#check ESeries.weight_mem_Icc
#check ESeries.weight_slope_bound
#check ESeries.weight_at_zero
#check ESeries.weight_mono
#check ESeries.prob_compl_identity
#check ESeries.e6_weight_lipschitz
#check ESeries.e6_tv_lipschitz
#check ESeries.weight_differentiableAt
#check ESeries.weight_deriv
#check ESeries.mismatch_factor
#check ESeries.weight_ratio_eq
#check ESeries.ratio_exp_neg_logLR
#check ESeries.nested_concentration

#print axioms ESeries.posterior_mixture
#print axioms ESeries.mixture_tv_bound
#print axioms ESeries.weight_slope_bound
#print axioms ESeries.e6_tv_lipschitz
#print axioms ESeries.weight_ratio_eq
#print axioms ESeries.nested_concentration
