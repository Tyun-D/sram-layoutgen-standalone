# Wave3 DFF_BUF Source-Level Function Audit

- 本审计只基于真实源码结构级连接，不声明 SPICE、时序或波形已验证。
- `dff.Q -> qint`：DFF child 输出 `Q` 连接到内部网络 `qint`。
- `qint -> inv1.A -> inv1.Z = QB`：相对 `qint`，`QB` 经过 1 级 PINV。
- `QB -> inv2.A -> inv2.Z = Q`：相对 `QB`，`Q` 经过 1 级 PINV。
- 因此相对 `qint`，顶层 `Q` 经过 2 级 PINV；相对 `qint`，顶层 `QB` 经过 1 级 PINV。
- 顶层 `D` 和 `CLK` 直接进入 DFF child 的 `D` / `CLK` 端口，没有额外父级 PINV 级数。

