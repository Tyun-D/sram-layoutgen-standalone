# DRC Provenance And Waiver Policy

## Classification

- `PREEXISTING_CHILD_MARKER`: 独立 child 资产在集成前已存在的 marker。
- `NEW_PARENT_GENERATED_MARKER`: 父级生成/集成后新增的 marker。
- `BOUNDARY_INTERACTION_MARKER`: 由合法 child 之间边界拼接带来的交互 marker。
- `APPROVED_WAIVER`: 有明确批准依据、规则、SHA、bbox 和来源的 waiver。
- `UNAPPROVED_MARKER`: 任何缺少批准依据的 marker。

## Rules

- 不修改 foundry/approved hard macro 内部几何来“消掉” marker。
- 先记录 child baseline marker 和 asset SHA，再判断集成后 delta。
- waiver 必须记录 rule、cell SHA、bbox、marker 来源、批准依据。
- 没有批准依据，不得把 marker 标成 waiver。
- 如果正式资产独立 DRC 为 0，则项目目标仍是 `0 unapproved markers`，而不是通过 waiver 消化问题。

## Current Project Position

- 当前正式项目资产中，没有发现已批准 intentional DRC waiver 的证据。
- Team B 九单元正式集成 gate 已记录 `combined_atlas_drc_marker_count = 0`。
- Decoder 在当前 restored worktree 中没有发现用户要求的 `24-marker M2-only closure baseline` 与 dedicated decoder gate，因此不能把任何 decoder marker 直接归类为 approved waiver。
