# E-series Lean 工程（NEX-346 交付物）

论文 NEX-342 v3.2（可学习 SDE 失联人员运动预测）理论侧 Lean4 分层：**可形式化核心引理**
全部形式化（零 `sorry`/`admit`/`pass`/`axiom`），PDE / h-变换存在性（E1/E3/E4 解析层）
如实声明为文档级（见理论容器 `NEX346_theory_container.md`）。

## 环境

- Lean 4.33.0（`lean-toolchain: leanprover/lean4:v4.33.0`），Lake 5.0.0
- Mathlib `v4.33.0`（rev `db584cd6d46c92f209a44c0f1c829460d327499d`，见 `lake-manifest.json`）

## 构建（一条命令）

```bash
lake exe cache get   # 拉取 mathlib 预编译缓存（需网络；也可用本地 ~/.cache/mathlib）
lake build           # 编译本工程，应输出 "Build completed successfully (3124 jobs)"
```

本工程在交付机上已全过：`lake build` → `Build completed successfully (3124 jobs)`。
`build.log` 随包，含完整构建记录 + 零 sorry/公理审计（`lake build` 输出 +
`grep` 零 sorry/admit/axiom/opaque + `#print axioms` 依赖清单）。

## 模块与定理映射

| 论文 | 内容 | `.lean` 位置 | 状态 |
|---|---|---|---|
| E5 / L1 | 软证据混合恒等式 `Q = w P(·\|E) + (1−w) P(·\|Eᶜ)` | `ESeries/Basic.lean` `posterior_mixture`, `weight_likelihood_ratio` | 形式化 |
| E6 / L2 | TV 界 `≤ 2\|w−w'\|` | `ESeries/Basic.lean` `mixture_tv_bound` | 形式化 |
| E6 / L3 | logistic 斜率 `\|dw/dλ\| = w(1−w) ≤ 1/4`；`w(0)=π`；λ 单调 | `ESeries/Basic.lean` `weight_slope_bound`, `weight_at_zero`, `weight_mono` | 形式化 |
| Prop 5.4 / L4 | 对偶 `h_exist + h_excl = 1` | `ESeries/Basic.lean` `prob_compl_identity` | 形式化 |
| E6 | TV-Lipschitz `≤ ½\|λ−λ'\|`（logistic ¼-Lipschitz + MVT） | `ESeries/Basic.lean` `e6_weight_lipschitz`, `e6_tv_lipschitz`, `weight_deriv`, `weight_differentiableAt` | 形式化 |
| E8 | 权重比乘积（测度代数/组合） | `ESeries/E8.lean` `weight_ratio_eq`, `mismatch_factor`, `nested_concentration` | 形式化 |
| E1/E3/E4 | PDE 存在唯一性 / Doob h-变换 / 存在概率 PDE | — | **文档级**（见理论容器） |

## 零公理审计

```bash
lake env lean ESeries/CheckAxioms.lean
```

全部引理仅依赖 `[propext, Classical.choice, Quot.sound]`（Lean 内核自带逻辑公理，非自定义）。
`grep -E "sorry|admit|axiom|opaque" ESeries/` 为 0 处（仅注释/docstring 命中）。

## 关键更正（对论文 v3.2）

E8 原文 `W_k(σ)/W_k(σ*) = Π e^{−|λᵢ|}` 仅在「嵌套偏离（σ ⊆ σ*）+ 均衡先验（πᵢ=1/2）」下
精确成立；一般情形的精确形式为 `weight_ratio_eq`（含 `πᵢ/(1−πᵢ)` 因子与两类失配方向）。
详见理论容器与 `ESeries/E8.lean` 文件头注释。
