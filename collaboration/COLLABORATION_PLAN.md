# COLLAB-P0 Collaboration Plan

This baseline only prepares two-person collaboration boundaries. It does not authorize any physical implementation, Wave4A2, TIME work, or new GDS generation.

## Locked Baseline

- Project branch: `feature/step45-clean-array-aggregation`
- Project baseline commit: `480ca5200f31bb0c21cdcfbdde25ff50f40108b0`
- OpenYield commit: `1c34428d8b913963c4971d093b1a7c2df97a2509`
- Team-B branch target: `collab/team-b-control-support`
- Team-B worktree target: `/data1/qujh/worktrees/team_b_control_support`

## Module Split

- Owner A / 曲珈豪:
- `ADDR_DFF`
- `DATA_DFF`
- `TIME`
- final `CONTROL_LOGIC` integration
- shared DFF-array core
- final machine audit
- human review coordination
- reusable release and reusable registry
- all four project ledgers

- Owner B:
- `PNAND2`
- `PNAND3`
- `AND2`
- `AND3`
- `pdrive`
- `pdrive2_for_pre`
- `wl_pdrive`
- `delay_chain`
- `wen_delay_chain`

## Pass Constraints

- Every unfinished physical module has exactly one implementation owner.
- Shared code owner is unique: Owner A.
- Ledger write owner is unique: Owner A.
- Release/seal owner is unique: Owner A.
- Team B starts at `TEAM-B0 / ASSIGNED_MODULE_SOURCE_ASSET_AND_DEPENDENCY_LOCK`.
- Team B cannot generate GDS or advance stages until GPT evidence review explicitly approves the next minimal stage.

## Recorded Differences From Informal Prompt

- `wen_delay_chain` is the authority-file module name; `WenDelayChain` is the source class name.
- The locked wave plan is used as the true schedule authority: Wave2 covers NAND/AND, Wave3 covers `DFF_BUF`, `delay_chain`, and the `pdrive` family, Wave4 covers `ADDR_DFF/DATA_DFF`, and Wave5 covers `TIME`.
