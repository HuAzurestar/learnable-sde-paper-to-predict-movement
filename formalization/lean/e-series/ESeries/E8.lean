import Mathlib.Data.Real.Basic
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Finset.Basic
import Mathlib.Tactic

/-!
# E8：证据集中的测度代数 / 组合部分

对应论文 E8（Evidence concentration）：`k` 个独立证据项，每项 `i` 对应存在事件 `Eᵢ`
（先验 `πᵢ`）、敏感度 `ℓ₁ᵢ`、误报率 `ℓ₀ᵢ`，真模式 `σ* ∈ {0,1}^k`。

联合后验是模式 `σ ∈ {0,1}^k` 上的混合：

`Q_k = Σ_σ W_k(σ) · P(· | ∩_{σᵢ=1} Eᵢ ∩ ∩_{σᵢ=0} Eᵢᶜ)`，

`W_k(σ) ∝ Π_{σᵢ=1} ℓ₁ᵢ πᵢ · Π_{σᵢ=0} ℓ₀ᵢ (1−πᵢ)`。

本文件形式化其**测度代数 / 组合核心**：

1. `mismatch_factor`：单坐标失配比的两类方向。
2. `weight_ratio_eq`：权重比 `W_k(σ)/W_k(σstar)` 等于只在**失配坐标** `{i : σᵢ ≠ σstarᵢ}` 上的
   逐坐标比之积（匹配坐标在分子分母中相消）。
3. `nested_concentration`：当失配仅为「真存在 → 说缺席」的单调（嵌套）偏离且先验均衡
   （`πᵢ = 1/2`）时，权重比恰为 `Π e^{−|λᵢ|}`，随失配坐标累积指数收敛到 0。

> 更正说明：论文 v3.2 原文 `W_k(σ)/W_k(σstar) = Π e^{−|λᵢ|}` 仅在「嵌套偏离 + 均衡先验」下
> 精确成立；一般情形见 `weight_ratio_eq`（含 `πᵢ/(1−πᵢ)` 因子与两类方向）。 -/

noncomputable section

open scoped BigOperators

namespace ESeries

/-! ## 权重与模式 -/

/-- 坐标 `i` 在模式 `σ` 下的权重因子：`σᵢ=1 ⟹ ℓ₁ᵢ πᵢ`，`σᵢ=0 ⟹ ℓ₀ᵢ (1−πᵢ)`。 -/
def weightFactor {ι : Type*} (ℓ₁ ℓ₀ π : ι → ℝ) (σ : ι → Bool) (i : ι) : ℝ :=
  if σ i then ℓ₁ i * π i else ℓ₀ i * (1 - π i)

/-- 模式 `σ` 的（未归一化）权重：`W(σ) = Πᵢ weightFactor σ i`。 -/
def patternWeight {ι : Type*} [Fintype ι] (ℓ₁ ℓ₀ π : ι → ℝ) (σ : ι → Bool) : ℝ :=
  ∏ i, weightFactor ℓ₁ ℓ₀ π σ i

/-- 坐标 `i` 的对数似然比 `λᵢ = log(ℓ₁ᵢ/ℓ₀ᵢ)`。 -/
def logLR {ι : Type*} (ℓ₁ ℓ₀ : ι → ℝ) (i : ι) : ℝ := Real.log (ℓ₁ i / ℓ₀ i)

/-! ## 单坐标失配比 -/

/-- **mismatch_factor**：单坐标 `i` 上，`σ` 相对 `σstar` 的权重因子之比。
- 若 `σstarᵢ = true`（真存在）而 `σᵢ = false`（说缺席）：`ℓ₀(1−π) / (ℓ₁π)`；
- 若 `σstarᵢ = false`（真缺席）而 `σᵢ = true`（说存在）：`ℓ₁π / (ℓ₀(1−π))`。 -/
theorem mismatch_factor {ι : Type*} (ℓ₁ ℓ₀ π : ι → ℝ) {σ σstar : ι → Bool} {i : ι}
    (hmiss : σ i ≠ σstar i) :
    weightFactor ℓ₁ ℓ₀ π σ i / weightFactor ℓ₁ ℓ₀ π σstar i
      = if σstar i then ℓ₀ i * (1 - π i) / (ℓ₁ i * π i)
        else ℓ₁ i * π i / (ℓ₀ i * (1 - π i)) := by
  unfold weightFactor
  by_cases hst : σstar i
  · have hσ : σ i = false := by
      cases hs : σ i with
      | false => rfl
      | true => exact False.elim (hmiss (by simp [hs, hst]))
    simp [hst, hσ]
  · have hσ : σ i = true := by
      cases hs : σ i with
      | false => exact False.elim (hmiss (by simp [hs, hst]))
      | true => rfl
    simp [hst, hσ]

/-! ## 权重比 = 失配坐标之积 -/

/-- **weight_ratio_eq（E8 核心）**：权重比等于失配坐标上的逐坐标比之积。

匹配坐标（`σᵢ = σstarᵢ`）的因子在分子分母中逐项相消（比为 1），故只剩 `σᵢ ≠ σstarᵢ` 的坐标。 -/
theorem weight_ratio_eq {ι : Type*} [Fintype ι] (ℓ₁ ℓ₀ π : ι → ℝ) (σ σstar : ι → Bool)
    (hWf : ∀ i, weightFactor ℓ₁ ℓ₀ π σstar i ≠ 0) :
    patternWeight ℓ₁ ℓ₀ π σ / patternWeight ℓ₁ ℓ₀ π σstar
      = ∏ i ∈ Finset.univ.filter (fun i => σ i ≠ σstar i),
          weightFactor ℓ₁ ℓ₀ π σ i / weightFactor ℓ₁ ℓ₀ π σstar i := by
  unfold patternWeight
  rw [← Finset.prod_div_distrib]
  rw [Finset.prod_filter_of_ne (s := Finset.univ) (p := fun i => σ i ≠ σstar i)
      (f := fun i => weightFactor ℓ₁ ℓ₀ π σ i / weightFactor ℓ₁ ℓ₀ π σstar i)]
  intro i _ hne
  by_contra hmatch
  have hσ : σ i = σstar i := hmatch
  have hfac : weightFactor ℓ₁ ℓ₀ π σ i = weightFactor ℓ₁ ℓ₀ π σstar i := by
    simp [weightFactor, hσ]
  have hratio : weightFactor ℓ₁ ℓ₀ π σ i / weightFactor ℓ₁ ℓ₀ π σstar i = 1 := by
    rw [hfac, div_self (hWf i)]
  exact hne hratio

/-! ## 对数似然比与指数形式 -/

/-- **ratio_exp_neg_logLR**：`ℓ₀/ℓ₁ = e^{−λᵢ}`（`λᵢ = log(ℓ₁/ℓ₀)`）。

当 `ℓ₁, ℓ₀ > 0`（正概率）时，`e^{−λᵢ} = e^{−log(ℓ₁/ℓ₀)} = (ℓ₁/ℓ₀)⁻¹ = ℓ₀/ℓ₁`。 -/
theorem ratio_exp_neg_logLR {ι : Type*} (ℓ₁ ℓ₀ : ι → ℝ) (i : ι)
    (hℓ₁pos : 0 < ℓ₁ i) (hℓ₀pos : 0 < ℓ₀ i) :
    ℓ₀ i / ℓ₁ i = Real.exp (- logLR ℓ₁ ℓ₀ i) := by
  unfold logLR
  have hpos : 0 < ℓ₁ i / ℓ₀ i := div_pos hℓ₁pos hℓ₀pos
  rw [Real.exp_neg, Real.exp_log hpos]
  field_simp [hℓ₁pos.ne', hℓ₀pos.ne']

/-! ## 均衡先验 + 嵌套偏离下的集中（论文 E8 的 `Π e^{−|λᵢ|}` 形式） -/

/-- **nested_concentration（E8 集中）**：若每个坐标先验均衡（`πᵢ = 1/2`）、
对数似然比 `λᵢ = log(ℓ₁ᵢ/ℓ₀ᵢ) > 0`（信息性：敏感度大于误报），且错误模式 `σ` 只在
「真存在却判缺席」方向上偏离（`σ ⊆ σstar`，即 `σᵢ = true ⟹ σstarᵢ = true`），则

`W(σ)/W(σstar) = ∏_{i : σᵢ ≠ σstarᵢ} e^{−|λᵢ|}`。

每一项 `e^{−|λᵢ|} < 1`，故随失配坐标数增加权重比指数收敛到 0
（论文 E8 的速率 `Σ_{失配} |λᵢ|`）。 -/
theorem nested_concentration {ι : Type*} [Fintype ι] (ℓ₁ ℓ₀ π : ι → ℝ) (σ σstar : ι → Bool)
    (hWf : ∀ i, weightFactor ℓ₁ ℓ₀ π σstar i ≠ 0)
    (hπ : ∀ i, π i = 1 / 2)
    (hℓ₁pos : ∀ i, 0 < ℓ₁ i) (hℓ₀pos : ∀ i, 0 < ℓ₀ i)
    (hinfo : ∀ i, ℓ₀ i < ℓ₁ i)
    (hmono : ∀ i, σ i = true → σstar i = true) :
    patternWeight ℓ₁ ℓ₀ π σ / patternWeight ℓ₁ ℓ₀ π σstar
      = ∏ i ∈ Finset.univ.filter (fun i => σ i ≠ σstar i), Real.exp (-|logLR ℓ₁ ℓ₀ i|) := by
  rw [weight_ratio_eq ℓ₁ ℓ₀ π σ σstar hWf]
  apply Finset.prod_congr rfl
  intro i hi
  have hmiss : σ i ≠ σstar i := (Finset.mem_filter.mp hi).2
  have hσi : σ i = false := by
    cases h : σ i with
    | false => rfl
    | true => exact False.elim (hmiss (by simp [h, hmono i h]))
  have hσsi : σstar i = true := by
    cases h : σstar i with
    | false => exact False.elim (hmiss (by simp [hσi, h]))
    | true => rfl
  have hposLR : 0 < logLR ℓ₁ ℓ₀ i := by
    unfold logLR
    exact Real.log_pos ((one_lt_div (hℓ₀pos i)).mpr (hinfo i))
  rw [mismatch_factor ℓ₁ ℓ₀ π (σ := σ) (σstar := σstar) (i := i) hmiss]
  simp [hσsi, hπ i]
  calc
    ℓ₀ i * (1 - (2 : ℝ)⁻¹) / (ℓ₁ i * (2 : ℝ)⁻¹)
        = ℓ₀ i / ℓ₁ i := by ring_nf
    _ = Real.exp (-logLR ℓ₁ ℓ₀ i) := ratio_exp_neg_logLR ℓ₁ ℓ₀ i (hℓ₁pos i) (hℓ₀pos i)
    _ = Real.exp (-|logLR ℓ₁ ℓ₀ i|) := by rw [abs_of_pos hposLR]

end ESeries

end
