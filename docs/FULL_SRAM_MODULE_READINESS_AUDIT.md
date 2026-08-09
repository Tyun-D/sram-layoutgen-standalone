# Full SRAM Module Readiness Audit

- status: `BLOCKED_BY_MISSING_FULL_SRAM_MODULE_ASSET`
- git head: `da41cc22109c7f6ce314b2cf038d82e086f12775`
- unready module count: `10`

| module | role | ready_for_top | GDS | blocker |
|---|---|---:|---|---|
| `precharge` | `column_path` | `False` | `outputs/openyield_module_gds/precharge/precharge.gds` | precharge module manifest says boundary pins are contract-backed and need L4/L5 verification; no standalone DRC=0 evidence found for the current precharge_v2 top-use asset; no final-GDS power endpoint coverage / foreign-net / negative-suite evidence found for precharge_v2 |
| `column_mux` | `column_path` | `False` | `outputs/openyield_module_gds/column_mux/column_mux.gds` | formal 16x16/wpr1 config has words_per_row=1, so column-mux use conflicts with current exact config unless owner redefines top contract; adapter evidence reports VDD shape_source=missing for local gen_col_mux canonical pin; no standalone DRC=0/connectivity/foreign-net/negative-suite evidence found for column_mux_v2 top-use asset |
| `sense_amplifier` | `column_path` | `False` | `outputs/openyield_module_gds/sense_amp/sense_amp.gds` | M11V evidence is isolated substitution/risk heuristic and explicitly cannot claim routing/power/DRC/signoff ready; no standalone module machine gate with DRC=0, final power endpoint coverage, foreign-net, and negative suite found |
| `write_driver` | `column_path` | `False` | `outputs/openyield_module_gds/write_driver/write_driver.gds` | no standalone DRC=0/connectivity/foreign-net/pin-access/negative-suite machine gate found for write_driver_v2; write-driver use in complete top needs BL/BR/DIN/write-enable physical route proof, which is absent |
| `control_logic` | `control_path` | `False` | `outputs/openyield_module_gds/CONTROL_LOGIC/CONTROL_LOGIC.gds` | M12C2 says can_claim_control_logic_physical_ready=false; CONTROL_LOGIC generator manifest says candidate geometry does not claim final routing or signoff; time/control placement readiness report marks control subblocks physical_ready=false |
| `DFF` | `control_path` | `True` | `outputs/M12C4ACH_dff_reusable_release/DFF_reusable_clean.gds` | - |
| `DFF_BUF` | `control_path` | `True` | `outputs/Wave3_DFF_BUF_reusable_release/DFF_BUF_reusable_clean.gds` | - |
| `delay_chain` | `control_path` | `False` | `outputs/openyield_module_gds/DELAY_CHAIN/DELAY_CHAIN.gds` | DELAY_CHAIN module manifest says candidate geometry does not claim final routing or signoff; time/control placement readiness marks DELAY_CHAIN_CLUSTER physical_ready=false; no standalone final-GDS connectivity/foreign-net/negative-suite top-use gate found for delay_chain_v2 |
| `pdrive` | `control_path` | `False` | `NOT_FOUND` | no pdrive_v2 GDS asset found in repo, evidence package, /data1 search, historical worktrees, or checkpoints; no pdrive pin map, DRC, connectivity, power endpoint, pin-access, determinism, or negative-suite evidence found |
| `wl_pdrive` | `control_path` | `False` | `NOT_FOUND` | no wl_pdrive_v2 GDS asset found in repo, evidence package, /data1 search, historical worktrees, or checkpoints; no wl_pdrive pin map, DRC, connectivity, power endpoint, pin-access, determinism, or negative-suite evidence found |
| `pdrive2_for_pre` | `control_path` | `False` | `NOT_FOUND` | no pdrive2_for_pre_v2 GDS asset found in repo, evidence package, /data1 search, historical worktrees, or checkpoints; no pdrive2_for_pre pin map, DRC, connectivity, power endpoint, pin-access, determinism, or negative-suite evidence found |
| `top_level_input_output_interface` | `top_interface` | `False` | `NOT_FOUND` | no full 16x16 SRAM top pin physical contract exists for CLK/CSB/WEB/TIME/PRE/WL_EN/S_EN/W_EN/DIN/DOUT/BL/BR/RBL; TIME_schedule, write_sample_point, disabled_hold_semantics, and WL timing budget remain owner-pending |
