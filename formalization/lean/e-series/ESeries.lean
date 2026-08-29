import ESeries.Basic
import ESeries.E8

/-!
# E-series 软证据 / 双桥理论 · 可形式化核心

本工程对应论文 NEX-342 v3.2 的 Lean4 分层（NEX-324 口径）：

- `ESeries/Basic.lean`：L1（软证据混合恒等式）、L2（TV 界）、
  L3（logistic 斜率界 + 单调性 + 极限）、L4（对偶恒等式）、E6（TV-Lipschitz）。
- `ESeries/E8.lean`：E8（证据集中）权重比乘积的测度代数 / 组合部分。

PDE / h-变换存在性（E1/E3/E4 解析层）为本工程的**文档级声明**（见理论容器），
不在此形式化、不含 `sorry` / `admit` / `pass` / `axiom`。
-/
