import Mathlib.Data.Real.Basic
import Mathlib.Analysis.SpecialFunctions.Exp
import Mathlib.Analysis.SpecialFunctions.ExpDeriv
import Mathlib.Analysis.Calculus.Deriv.Mul
import Mathlib.Analysis.Calculus.Deriv.Add
import Mathlib.Analysis.Calculus.Deriv.Inv
import Mathlib.Analysis.Calculus.MeanValue
import Mathlib.MeasureTheory.Measure.MeasureSpace
import Mathlib.Tactic

/-!
# E-series 可形式化核心引理：L1–L4 与 E6

与论文 NEX-342 v3.2 的对应关系（每条定理标注 `.lean` 位置）：

- **L1**（E5 混合恒等式）`posterior_mixture` / `weight_likelihood_ratio`：
  `Q = w P(·|E) + (1−w) P(·|Eᶜ)`，`w = ℓ₁π/Z`。
- **L2**（E6 TV 界）`mixture_tv_bound`：混合距离 `≤ 2|w−w'|`。
- **L3**（E6 斜率/单调/极限）`weight_slope_bound`（`|dw/dλ| = w(1−w) ≤ 1/4`）、
  `weight_at_zero`（`w(0)=π`）、`weight_mono`（λ 单调）。
  极限 `w→1`（λ→+∞，ρ→∞）与 `w→0`（λ→−∞，ρ→0）见理论容器（文档级极限陈述，
  代数载体为 `weight` 的 logistic 形式）。
- **L4**（Prop 5.4 对偶）`prob_compl_identity`：`h_exist + h_excl = 1`（事件与其补概率）。
- **E6**（TV-Lipschitz）`e6_weight_lipschitz`（logistic ¼-Lipschitz，中值定理）+
  `e6_tv_lipschitz`（合成 `≤ ½|λ−λ'|`）。

本文件所有证明均为 `ring_nf` / `nlinarith` / `linarith` / `field_simp` 级初等代数与
标准中值定理；不引入任何自定义公理（`#print axioms` 仅 `propext`/`Classical.choice`/
`Quot.sound`）。
-/

noncomputable section

open Filter
open MeasureTheory

namespace ESeries

/-! ## 基本对象：软证据权重（E5 / E6） -/

/-- 软证据后验混合权重（E5/E6）：

`w(λ) = π e^λ / (π e^λ + 1 − π)`，

其中 `π = P(E)` 为先验存在概率，`λ = log ρ = log((1−β)/α)` 为对数似然比
（sensitivity `1−β`，false-alarm `α`）。`w` 是标准 logistic `σ(t)=1/(1+e^{-t})`
的仿射平移：当 `0 < π < 1` 时 `w(λ) = σ(λ + log(π/(1−π)))`。 -/
def weight (π lam : ℝ) : ℝ := π * Real.exp lam / (π * Real.exp lam + (1 - π))

/-! ## L1：软证据混合恒等式（E5） -/

/-- **L1(a)**：Bayes 后验的混合形式。给定存在事件 `E`（先验 `π = P(E)`）、
敏感度 `ℓ₁ = P(Y=1|E)`、误报率 `ℓ₀ = P(Y=1|Eᶜ)`，对任意事件 `B` 令
`pBE = P(B∩E)`、`pBEc = P(B∩Eᶜ)`。则观测到 `Y=1` 后 `B` 的后验概率为

`(ℓ₁ pBE + ℓ₀ pBEc) / Z = w · (pBE/π) + (1−w) · (pBEc/(1−π))`，

其中 `Z = ℓ₁π + ℓ₀(1−π)`、`w = ℓ₁π/Z`。右侧正是两分支 `P(·|E)`、`P(·|Eᶜ)`
按 `(w, 1−w)` 的凸组合（纯有限测度代数，可形式化）。 -/
theorem posterior_mixture (ℓ₁ ℓ₀ π pBE pBEc : ℝ)
    (hπ : π ≠ 0) (hπc : 1 - π ≠ 0) (hZ : ℓ₁ * π + ℓ₀ * (1 - π) ≠ 0) :
    (ℓ₁ * pBE + ℓ₀ * pBEc) / (ℓ₁ * π + ℓ₀ * (1 - π))
      = (ℓ₁ * π / (ℓ₁ * π + ℓ₀ * (1 - π))) * (pBE / π)
        + (1 - ℓ₁ * π / (ℓ₁ * π + ℓ₀ * (1 - π))) * (pBEc / (1 - π)) := by
  field_simp [hπ, hπc, hZ]
  ring

/-- **L1(b)**：`w = ρπ/(ρπ + 1 − π)`，其中 `ρ = ℓ₁/ℓ₀` 为似然比
（论文 E5 的「equivalently」一句）。这是 `w = ℓ₁π/Z` 除以 `ℓ₀` 的重写。 -/
theorem weight_likelihood_ratio (ℓ₁ ℓ₀ π : ℝ) (hℓ₀ : ℓ₀ ≠ 0)
    (hZ : ℓ₁ * π + ℓ₀ * (1 - π) ≠ 0) :
    ℓ₁ * π / (ℓ₁ * π + ℓ₀ * (1 - π))
      = (ℓ₁ / ℓ₀) * π / ((ℓ₁ / ℓ₀) * π + (1 - π)) := by
  field_simp [hℓ₀]

/-! ## L2：混合 TV 界（E6） -/

/-- **L2**：两个相同分支对 `{P(·|E), P(·|Eᶜ)}` 的凸组合，其（对任意事件 `B` 的）概率差
被 `2|w−w'|` 控制。这里 `a = P(B|E)`、`b = P(B|Eᶜ)` 均落在 `[0,1]`。

`|(w a + (1−w)b) − (w' a + (1−w')b)| = |(w−w')(a−b)| ≤ |w−w'|·|a−b| ≤ 2|w−w'|`。

对 `B` 取上确界即得 TV 界 `‖Q(w) − Q(w')‖_TV ≤ 2|w−w'|`（论文用总变差 `≤ 2` 的约定）。 -/
theorem mixture_tv_bound (a b w w' : ℝ) (ha : 0 ≤ a) (ha1 : a ≤ 1)
    (hb : 0 ≤ b) (hb1 : b ≤ 1) :
    |(w * a + (1 - w) * b) - (w' * a + (1 - w') * b)| ≤ 2 * |w - w'| := by
  have hdiff : (w * a + (1 - w) * b) - (w' * a + (1 - w') * b)
      = (w - w') * (a - b) := by ring
  rw [hdiff, abs_mul]
  have hab1 : |a - b| ≤ 1 := by
    rw [abs_sub_le_iff]
    constructor <;> nlinarith [ha, ha1, hb, hb1]
  have hab2 : |a - b| ≤ 2 := by linarith
  calc
    |w - w'| * |a - b| ≤ |w - w'| * 2 :=
      mul_le_mul_of_nonneg_left hab2 (abs_nonneg (w - w'))
    _ = 2 * |w - w'| := by ring

/-! ## L3：logistic 斜率 / 单调性 / 极限（E6） -/

/-- **L3(a)**：权重落在 `[0,1]`（当 `0 ≤ π ≤ 1`）。这是斜率界与 TV-Lipschitz 的前置。 -/
theorem weight_mem_Icc (π lam : ℝ) (hπ0 : 0 ≤ π) (hπ1 : π ≤ 1) :
    weight π lam ∈ Set.Icc (0 : ℝ) 1 := by
  unfold weight
  have hpos : 0 < Real.exp lam := Real.exp_pos lam
  have hnum : 0 ≤ π * Real.exp lam := mul_nonneg hπ0 (le_of_lt hpos)
  have h1mπ : 0 ≤ 1 - π := sub_nonneg.mpr hπ1
  have hden_pos : 0 < π * Real.exp lam + (1 - π) := by
    have hmain : 0 < π * Real.exp lam ∨ 0 < 1 - π := by
      by_cases hπlt1 : π < 1
      · exact Or.inr (sub_pos.mpr hπlt1)
      · have hπeq1 : π = 1 := by linarith
        left
        rw [hπeq1]
        simpa using hpos
    rcases hmain with h | h <;> nlinarith
  constructor
  · exact div_nonneg hnum (le_of_lt hden_pos)
  · exact (div_le_one hden_pos).mpr (by linarith [h1mπ])

/-- **L3(b)**：logistic 斜率界 `|dw/dλ| = w(1−w) ≤ 1/4`。

（`w(1−w) ≤ 1/4` 对任意实 `w` 成立：`w(1−w) = 1/4 − (w−1/2)²`。导数恒等式
`dw/dλ = w(1−w)` 见 `weight_deriv`。） -/
theorem weight_slope_bound (π lam : ℝ) :
    weight π lam * (1 - weight π lam) ≤ (1 : ℝ) / 4 := by
  have hid : weight π lam * (1 - weight π lam)
      = (1 : ℝ) / 4 - (weight π lam - (1 : ℝ) / 2) ^ 2 := by
    ring_nf
  rw [hid]
  have hsq : 0 ≤ (weight π lam - (1 : ℝ) / 2) ^ 2 := sq_nonneg _
  linarith

/-- **L3(c)**：极限 `w(0) = π`（`λ = 0` 即 `ρ = 1` 的无信息点，权重回到先验）。 -/
theorem weight_at_zero (π : ℝ) : weight π 0 = π := by
  unfold weight
  rw [Real.exp_zero]
  have hden : π * 1 + (1 - π) = 1 := by ring
  rw [hden]
  ring_nf

/-- **L3(d)**：`w` 关于 `λ` 单调不减（当 `0 ≤ π ≤ 1`）。

证明：`weight π λ = π e^λ / (π e^λ + (1−π))`，令 `d = 1 − π ≥ 0`、`a = e^{λ₁} ≤ b = e^{λ₂}`，
交叉相乘得 `π a/(π a + d) ≤ π b/(π b + d) ⟺ π d (a − b) ≤ 0`，由 `π ≥ 0`、`d ≥ 0`、`a ≤ b` 成立。 -/
theorem weight_mono (π : ℝ) (hπ0 : 0 ≤ π) (hπ1 : π ≤ 1) {lam₁ lam₂ : ℝ} (h : lam₁ ≤ lam₂) :
    weight π lam₁ ≤ weight π lam₂ := by
  unfold weight
  have hpos₁ : 0 < Real.exp lam₁ := Real.exp_pos lam₁
  have hpos₂ : 0 < Real.exp lam₂ := Real.exp_pos lam₂
  have hexp : Real.exp lam₁ ≤ Real.exp lam₂ := Real.exp_monotone h
  have hd : 0 ≤ 1 - π := sub_nonneg.mpr hπ1
  have hden₁ : 0 < π * Real.exp lam₁ + (1 - π) := by
    have hnum₁ : 0 ≤ π * Real.exp lam₁ := mul_nonneg hπ0 (le_of_lt hpos₁)
    have hmain : 0 < π * Real.exp lam₁ ∨ 0 < 1 - π := by
      by_cases hπlt1 : π < 1
      · exact Or.inr (sub_pos.mpr hπlt1)
      · have hπeq1 : π = 1 := by linarith
        left
        rw [hπeq1]
        simpa using hpos₁
    rcases hmain with h' | h' <;> nlinarith
  have hden₂ : 0 < π * Real.exp lam₂ + (1 - π) := by
    have hnum₂ : 0 ≤ π * Real.exp lam₂ := mul_nonneg hπ0 (le_of_lt hpos₂)
    have hmain : 0 < π * Real.exp lam₂ ∨ 0 < 1 - π := by
      by_cases hπlt1 : π < 1
      · exact Or.inr (sub_pos.mpr hπlt1)
      · have hπeq1 : π = 1 := by linarith
        left
        rw [hπeq1]
        simpa using hpos₂
    rcases hmain with h' | h' <;> nlinarith
  have hcross : π * Real.exp lam₁ * (π * Real.exp lam₂ + (1 - π))
      ≤ π * Real.exp lam₂ * (π * Real.exp lam₁ + (1 - π)) := by
    have hdiff : π * Real.exp lam₂ * (π * Real.exp lam₁ + (1 - π))
        - π * Real.exp lam₁ * (π * Real.exp lam₂ + (1 - π))
        = π * (1 - π) * (Real.exp lam₂ - Real.exp lam₁) := by ring
    rw [← sub_nonneg, hdiff]
    exact mul_nonneg (mul_nonneg hπ0 hd) (sub_nonneg.mpr hexp)
  exact (div_le_div_iff₀ hden₁ hden₂).2 hcross

/-! ## L4：对偶恒等式（Prop 5.4） -/

/-- **L4**：事件与其补的概率之和为 1（概率测度）。

对应论文 Prop 5.4：令 `h_exist(t,x) = P(τ_A ≤ T | X_t=x)`、
`h_excl(t,x) = P(τ_A > T | X_t=x)`（同一事件的互补描述），则
`h_exist + h_excl = 1`。本引理是其在一般概率测度上的测度代数核心：对可测集 `s`
（即事件 `{τ_A ≤ T}`）与概率测度（`μ Set.univ = 1`），`μ s + μ sᶜ = 1`。 -/
theorem prob_compl_identity {α : Type*} [MeasurableSpace α]
    (μ : Measure α) (s : Set α) (hs : MeasurableSet s) (h1 : μ Set.univ = 1) :
    μ s + μ sᶜ = 1 := by
  rw [measure_add_measure_compl hs, h1]

/-! ## E6 的微积分前置（weight 的导数） -/

/-- **`weight_differentiableAt`**：`w` 在任意点可微（`exp` 与有理函数的复合）。 -/
theorem weight_differentiableAt (π x : ℝ) (hπ0 : 0 ≤ π) (hπ1 : π ≤ 1) :
    DifferentiableAt ℝ (fun t => weight π t) x := by
  unfold weight
  have hden : ∀ t, π * Real.exp t + (1 - π) ≠ 0 := by
    intro t
    have hpos : 0 < Real.exp t := Real.exp_pos t
    have hnum : 0 ≤ π * Real.exp t := mul_nonneg hπ0 (le_of_lt hpos)
    have hd : 0 ≤ 1 - π := sub_nonneg.mpr hπ1
    have hden_pos : 0 < π * Real.exp t + (1 - π) := by
      have hmain : 0 < π * Real.exp t ∨ 0 < 1 - π := by
        by_cases hπlt1 : π < 1
        · exact Or.inr (sub_pos.mpr hπlt1)
        · have hπeq1 : π = 1 := by linarith
          left
          rw [hπeq1]
          simpa using hpos
      rcases hmain with h | h <;> nlinarith
    exact ne_of_gt hden_pos
  have hN : Differentiable ℝ (fun t : ℝ => π * Real.exp t) :=
    Real.differentiable_exp.const_mul π
  have hD : Differentiable ℝ (fun t : ℝ => π * Real.exp t + (1 - π)) :=
    hN.add_const (1 - π)
  exact (hN.div hD hden).differentiableAt

/-- **`weight_deriv`**：导数恒等式 `dw/dλ = w(1−w)`（logistic 微分）。 -/
theorem weight_deriv (π x : ℝ) (hπ0 : 0 ≤ π) (hπ1 : π ≤ 1) :
    deriv (fun t => weight π t) x = weight π x * (1 - weight π x) := by
  unfold weight
  have hden : π * Real.exp x + (1 - π) ≠ 0 := by
    have hpos : 0 < Real.exp x := Real.exp_pos x
    have hnum : 0 ≤ π * Real.exp x := mul_nonneg hπ0 (le_of_lt hpos)
    have hd : 0 ≤ 1 - π := sub_nonneg.mpr hπ1
    have hden_pos : 0 < π * Real.exp x + (1 - π) := by
      have hmain : 0 < π * Real.exp x ∨ 0 < 1 - π := by
        by_cases hπlt1 : π < 1
        · exact Or.inr (sub_pos.mpr hπlt1)
        · have hπeq1 : π = 1 := by linarith
          left
          rw [hπeq1]
          simpa using hpos
      rcases hmain with h | h <;> nlinarith
    exact ne_of_gt hden_pos
  have hN : HasDerivAt (fun t : ℝ => π * Real.exp t) (π * Real.exp x) x := by
    simpa using (Real.hasDerivAt_exp x).const_mul π
  have hD : HasDerivAt (fun t : ℝ => π * Real.exp t + (1 - π)) (π * Real.exp x) x := by
    simpa using hN.add_const (1 - π)
  have hdiv := hN.div hD hden
  change deriv ((fun t : ℝ => π * Real.exp t) / (fun t : ℝ => π * Real.exp t + (1 - π))) x =
      π * Real.exp x / (π * Real.exp x + (1 - π)) *
        (1 - π * Real.exp x / (π * Real.exp x + (1 - π)))
  rw [hdiv.deriv]
  field_simp [hden]

/-! ## E6：TV-Lipschitz -/

/-- **E6(a)**：logistic 权重 `w(λ)` 是 `1/4`-Lipschitz（中值定理）。

由 `weight_deriv`（`deriv (weight π) = w(1−w)`）与 `weight_slope_bound`
（`|w(1−w)| ≤ 1/4`），凸集 `Set.univ` 上的中值定理给出 `|w(λ)−w(λ')| ≤ ¼|λ−λ'|`。 -/
theorem e6_weight_lipschitz (π : ℝ) (hπ0 : 0 ≤ π) (hπ1 : π ≤ 1) (lam lam' : ℝ) :
    |weight π lam - weight π lam'| ≤ (1 : ℝ) / 4 * |lam - lam'| := by
  let f : ℝ → ℝ := fun x => weight π x
  have hdiff : ∀ x ∈ Set.univ, DifferentiableAt ℝ f x := by
    intro x _
    exact weight_differentiableAt π x hπ0 hπ1
  have hbound : ∀ x ∈ Set.univ, ‖deriv f x‖ ≤ (1 : ℝ) / 4 := by
    intro x _
    rw [weight_deriv π x hπ0 hπ1]
    have hw := weight_mem_Icc π x hπ0 hπ1
    have hnonneg : 0 ≤ weight π x * (1 - weight π x) :=
      mul_nonneg hw.1 (sub_nonneg.mpr hw.2)
    rw [Real.norm_eq_abs, abs_of_nonneg hnonneg]
    exact weight_slope_bound π x
  have hlip := Convex.norm_image_sub_le_of_norm_deriv_le (f := f) (s := Set.univ)
    (x := lam') (y := lam) (C := (1 : ℝ) / 4)
    hdiff hbound convex_univ (by trivial) (by trivial)
  simpa [f, Real.norm_eq_abs] using hlip

/-- **E6(b)**：TV-Lipschitz 合成。由 L2（`≤ 2|w−w'|`）与 E6(a)（`≤ ¼|λ−λ'|`）得

`‖Q(λ) − Q(λ')‖_TV ≤ 2|w(λ)−w(λ')| ≤ ½|λ−λ'|`。 -/
theorem e6_tv_lipschitz (π : ℝ) (hπ0 : 0 ≤ π) (hπ1 : π ≤ 1) (lam lam' : ℝ) :
    2 * |weight π lam - weight π lam'| ≤ (1 : ℝ) / 2 * |lam - lam'| := by
  have h := e6_weight_lipschitz π hπ0 hπ1 lam lam'
  nlinarith

end ESeries

end
