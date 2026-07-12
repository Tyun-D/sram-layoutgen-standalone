# M12C4A Human Review Required Items

1. 检查 11 个 child 是否均存在且没有重叠；
2. 检查 VDD/VSS 是否连续且没有短路；
3. 检查 D、Q、CLK 顶层 pin 是否清晰可访问；
4. 检查 CLK/CLKB 两套控制网络是否分开；
5. 检查四个 Transmission Gate 的控制端连接方向；
6. 检查 master latch 的 z1/z2/z3 反馈路径；
7. 检查 slave latch 的 z4/z5/Q/QB 反馈路径；
8. 检查 M1/M2/Via1 是否存在明显断裂或错误交叉；
9. 检查没有 child 标签重影；
10. 检查没有空 cell、悬空实例或异常大面积空白。
