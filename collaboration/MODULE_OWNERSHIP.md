# Module Ownership Baseline

## Locked Inputs

- Project branch: `feature/step45-clean-array-aggregation`
- Project baseline commit: `480ca5200f31bb0c21cdcfbdde25ff50f40108b0`
- OpenYield commit: `1c34428d8b913963c4971d093b1a7c2df97a2509`
- Locked wave plan: `outputs/M12C4_composite_control_cell_generation_plan/current_supported_config/M12C4_composite_implementation_wave_plan.csv`

## Frozen Completed Modules

- `PINV`: approved reusable primitive family under `outputs/M12C3A4_canonical_primitive_label_cleanup/current_supported_config/reusable_cells`
- `TRANSMISSION_GATE`: approved reusable primitive after M12C3A3/M12C3A4R
- `DFF`: approved reusable composite under `outputs/M12C4ACH_dff_reusable_release/DFF_reusable_clean.gds`
- `DFF_BUF`: approved reusable composite under the Wave3H1 release evidence flow

## Owner A

- Physical modules: `ADDR_DFF`, `DATA_DFF`, `TIME`
- Integration and governance: final `CONTROL_LOGIC` integration, shared DFF-array core, final machine audit, human review coordination, reusable release, reusable registry, and the four project ledgers

## Owner B

- Wave2 family: `PNAND2`, `PNAND3`, `AND2`, `AND3`
- Wave3 family: `pdrive`, `pdrive2_for_pre`, `wl_pdrive`, `delay_chain`, `wen_delay_chain`

## Authority and Permissions

- Only Owner A may modify:
- `PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md`
- `PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json`
- `PROJECT_NETLIST_TO_LAYOUT_GOAL.md`
- `PROJECT_NETLIST_TO_LAYOUT_PROGRESS.md`
- reusable registry and release/seal outputs
- approved reusable GDS
- `TIME` integration code
- shared DFF-array core
- integration branch and final merge decisions

- Owner B may work only inside the Team-B allowlist defined in `collaboration/ALLOWED_PATHS_TEAM_B.txt`.
- Owner B never gets ledger write permission, reusable release permission, or merge authority.

## Recorded Discrepancies vs Prompt

- Authority files use logical module name `wen_delay_chain` while the OpenYield source class is `WenDelayChain`.
- The locked wave plan places `PNAND2/PNAND3 and AND2/AND3` in `Wave2`, `DFF_BUF, delay_chain, pdrive family` in `Wave3`, `ADDR_DFF / DATA_DFF` in `Wave4`, and `TIME` in `Wave5`; this baseline follows the wave file rather than informal ordering.
- Current authoritative ledgers show `ADDR_DFF` source/binding/interface gates passed but physical GDS status remains `NOT_GENERATED`, and `DATA_DFF` binding remains unresolved for Wave4B. No new physical stage is started here.
