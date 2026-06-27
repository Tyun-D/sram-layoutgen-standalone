# OpenYield Control Path Candidate Generation Wave1 Report

- Repo root: `/data1/qujh/work/sram_layoutgen_step45_clean`
- Repo HEAD: `80ac61f10acef8751460a8b5afba68f6e995d43c`
- OpenYield root: `/data1/qujh/work/external/OpenYield`
- OpenYield HEAD: `1c34428d8b913963c4971d093b1a7c2df97a2509`

## Gates

```json
{
  "control_path_candidate_generation_wave1_available": true,
  "openyield_source_available": true,
  "control_source_scan_completed": true,
  "candidate_contracts_generated": true,
  "candidate_contracts_table_available": true,
  "precharge_source_found": true,
  "precharge_candidate_contract_available": true,
  "precharge_spice_candidate_available": true,
  "precharge_testbench_skeleton_available": true,
  "precharge_enable_candidate_contract_available": true,
  "sense_enable_candidate_contract_available": true,
  "write_enable_candidate_contract_available": true,
  "wordline_enable_candidate_contract_available": true,
  "gated_clock_candidate_contract_available": true,
  "dff_row_candidate_contract_available": true,
  "all_blocked_objects_have_next_action": true,
  "metadata_consumer_contract_link_available": true,
  "can_enter_selected_control_path_spice_smoke": true,
  "can_enter_guarded_adapter_registry": true,
  "can_modify_standalone_now": false,
  "can_generate_time_control_gds_now": false,
  "can_claim_openyield_full_integration_now": false,
  "can_claim_timing_closure_now": false
}
```

## Source Scan

```json
[
  {
    "control_object": "PRECHARGE",
    "priority": 1,
    "openyield_source_file": "/data1/qujh/work/external/OpenYield/sram_compiler/subcircuits/precharge_and_write_driver.py",
    "source_symbol": "Precharge",
    "source_ports_or_nodes": "VDD, ENB, BL, BLB",
    "instance_naming": "NAME=PRECHARGE; M1/M2 precharge BL/BLB, M3 equalization",
    "logical_role": "PMOS-only precharge/equalization cell for BL/BLB",
    "transistor_sizing_visible": true,
    "uses_standard_cells": "none; direct PMOS devices",
    "recoverable_spice_candidate": true,
    "recoverable_testbench_skeleton": true
  },
  {
    "control_object": "PRECHARGE_ENABLE_PATH",
    "priority": 1,
    "openyield_source_file": "/data1/qujh/work/external/OpenYield/sram_compiler/subcircuits/time_generate.py",
    "source_symbol": "pre_unbuf + pre",
    "source_ports_or_nodes": "gated_clk_buf, rbl_delay, wl_en_bar -> PRE_UNBUF -> PRE",
    "instance_naming": "Xpre_unbuf, Xpre",
    "logical_role": "Generate active-low precharge enable from gated clock, delay chain, and wl_en_bar",
    "transistor_sizing_visible": true,
    "uses_standard_cells": "PNAND3 + pdrive2_for_pre",
    "recoverable_spice_candidate": true,
    "recoverable_testbench_skeleton": true
  },
  {
    "control_object": "SENSE_ENABLE_PATH",
    "priority": 2,
    "openyield_source_file": "/data1/qujh/work/external/OpenYield/sram_compiler/subcircuits/time_generate.py",
    "source_symbol": "s_en",
    "source_ports_or_nodes": "rbl_delay, gated_clk_bar, we_bar -> s_en",
    "instance_naming": "Xs_en",
    "logical_role": "Read-side sense amplifier enable generated from delayed RBL and gated control",
    "transistor_sizing_visible": true,
    "uses_standard_cells": "AND3; SENSEAMP in mux_and_sa.py",
    "recoverable_spice_candidate": true,
    "recoverable_testbench_skeleton": true
  },
  {
    "control_object": "WRITE_ENABLE_PATH",
    "priority": 3,
    "openyield_source_file": "/data1/qujh/work/external/OpenYield/sram_compiler/subcircuits/time_generate.py",
    "source_symbol": "w_en / WenDelayChain",
    "source_ports_or_nodes": "rbl_delay_bar or rbl_delay_bar_wen, gated_clk_bar, we -> w_en",
    "instance_naming": "Xwen_delaychain, Xw_en",
    "logical_role": "Write enable timing path with optional write-only delay chain",
    "transistor_sizing_visible": true,
    "uses_standard_cells": "WenDelayChain + AND3",
    "recoverable_spice_candidate": true,
    "recoverable_testbench_skeleton": true
  },
  {
    "control_object": "WORDLINE_ENABLE_PATH",
    "priority": 4,
    "openyield_source_file": "/data1/qujh/work/external/OpenYield/sram_compiler/subcircuits/time_generate.py",
    "source_symbol": "wl_pdrive + inv_wl_en_bar",
    "source_ports_or_nodes": "gated_clk_bar -> wl_en -> wl_en_bar",
    "instance_naming": "Xwl_en, Xinv_wl_en_bar",
    "logical_role": "Wordline-enable buffer chain from gated clock",
    "transistor_sizing_visible": true,
    "uses_standard_cells": "Pinv-based wl_pdrive + Pinv",
    "recoverable_spice_candidate": true,
    "recoverable_testbench_skeleton": true
  },
  {
    "control_object": "GATED_CLOCK_PATH",
    "priority": 5,
    "openyield_source_file": "/data1/qujh/work/external/OpenYield/sram_compiler/subcircuits/time_generate.py",
    "source_symbol": "and2_gated_clk_bar / and2_gated_clk_buf",
    "source_ports_or_nodes": "cs, clk_bar -> gated_clk_bar; cs, clk_buf -> gated_clk_buf",
    "instance_naming": "Xand2_gated_clk_bar, Xand2_gated_clk_buf",
    "logical_role": "Clock gating for timing tree entry into WL and control enables",
    "transistor_sizing_visible": true,
    "uses_standard_cells": "AND2",
    "recoverable_spice_candidate": true,
    "recoverable_testbench_skeleton": true
  },
  {
    "control_object": "DFF_ROW",
    "priority": 6,
    "openyield_source_file": "/data1/qujh/work/external/OpenYield/sram_compiler/subcircuits/time_generate.py",
    "source_symbol": "dff / DFF_BUF / ADDR_DFF",
    "source_ports_or_nodes": "VDD, VSS, D, Q, CLK and row-indexed A/A_dff nodes",
    "instance_naming": "Xdff_buf_addr, Xdff_buf, Xdff_buf1, Xdff_<i>",
    "logical_role": "Address/control flip-flop capture chain feeding cs/we and row address path",
    "transistor_sizing_visible": true,
    "uses_standard_cells": "Pinv + TransmissionGate + DFF_BUF/ADDR_DFF",
    "recoverable_spice_candidate": true,
    "recoverable_testbench_skeleton": true
  }
]
```

## Candidate Contracts

```json
[
  {
    "control_object": "PRECHARGE",
    "priority": 1,
    "openyield_source_file": "/data1/qujh/work/external/OpenYield/sram_compiler/subcircuits/precharge_and_write_driver.py",
    "source_symbol": "Precharge",
    "source_ports_or_nodes": "VDD, ENB, BL, BLB",
    "local_candidate_name": "precharge",
    "candidate_type": "subckt_skeleton",
    "candidate_artifact": "docs/candidate_spice/control_paths/precharge_candidate_contract.sp",
    "spice_candidate_available": true,
    "testbench_skeleton_available": true,
    "timing_metadata_available": false,
    "source_evidence_status": "source_linked_candidate_contract_available",
    "recovery_status": "skeleton_generated_requires_model_binding_and_pin_validation",
    "blocked_reason": "not_validated_spice_requires_model_binding_and_transient_smoke",
    "next_required_action": "requires_pin_validation;requires_model_recovery;requires_transient_smoke",
    "integration_readiness": "candidate_contract_only_not_physical_ready",
    "forbidden_claims": "no_delay_proof;no_timing_closure;no_physical_integration;no_time_control_gds"
  },
  {
    "control_object": "PRECHARGE_ENABLE_PATH",
    "priority": 1,
    "openyield_source_file": "/data1/qujh/work/external/OpenYield/sram_compiler/subcircuits/time_generate.py",
    "source_symbol": "pre_unbuf + pre",
    "source_ports_or_nodes": "gated_clk_buf, rbl_delay, wl_en_bar -> PRE_UNBUF -> PRE",
    "local_candidate_name": "precharge_enable_path",
    "candidate_type": "testbench_skeleton",
    "candidate_artifact": "docs/candidate_spice/control_paths/precharge_enable_candidate_tb.sp",
    "spice_candidate_available": false,
    "testbench_skeleton_available": true,
    "timing_metadata_available": false,
    "source_evidence_status": "source_linked_candidate_contract_available",
    "recovery_status": "testbench_skeleton_generated_requires_logic_cell_contracts",
    "blocked_reason": "needs_pre_unbuf_and_pre_driver_spice_contracts_for_simulation",
    "next_required_action": "requires_model_recovery;requires_pin_validation;requires_transient_smoke",
    "integration_readiness": "candidate_contract_only_not_physical_ready",
    "forbidden_claims": "no_delay_proof;no_timing_closure;no_physical_integration;no_time_control_gds"
  },
  {
    "control_object": "SENSE_ENABLE_PATH",
    "priority": 2,
    "openyield_source_file": "/data1/qujh/work/external/OpenYield/sram_compiler/subcircuits/time_generate.py",
    "source_symbol": "s_en",
    "source_ports_or_nodes": "rbl_delay, gated_clk_bar, we_bar -> s_en",
    "local_candidate_name": "sense_enable_path",
    "candidate_type": "candidate_contract",
    "candidate_artifact": "docs/candidate_spice/control_paths/sense_enable_path_candidate_contract.inc",
    "spice_candidate_available": true,
    "testbench_skeleton_available": true,
    "timing_metadata_available": false,
    "source_evidence_status": "source_linked_candidate_contract_available",
    "recovery_status": "source_linked_contract_generated_requires_transistor_or_stdcell_binding",
    "blocked_reason": "needs_model_recovery_and_path_specific_transient_smoke",
    "next_required_action": "needs_spice_model;needs_transient_smoke;needs_mapping_to_layoutgen_adapter",
    "integration_readiness": "candidate_contract_only_not_physical_ready",
    "forbidden_claims": "no_delay_proof;no_timing_closure;no_physical_integration;no_time_control_gds"
  },
  {
    "control_object": "WRITE_ENABLE_PATH",
    "priority": 3,
    "openyield_source_file": "/data1/qujh/work/external/OpenYield/sram_compiler/subcircuits/time_generate.py",
    "source_symbol": "w_en / WenDelayChain",
    "source_ports_or_nodes": "rbl_delay_bar or rbl_delay_bar_wen, gated_clk_bar, we -> w_en",
    "local_candidate_name": "write_enable_path",
    "candidate_type": "candidate_contract",
    "candidate_artifact": "docs/candidate_spice/control_paths/write_enable_path_candidate_contract.inc",
    "spice_candidate_available": true,
    "testbench_skeleton_available": true,
    "timing_metadata_available": false,
    "source_evidence_status": "source_linked_candidate_contract_available",
    "recovery_status": "source_linked_contract_generated_requires_transistor_or_stdcell_binding",
    "blocked_reason": "needs_model_recovery_and_path_specific_transient_smoke",
    "next_required_action": "needs_spice_model;needs_transient_smoke;needs_mapping_to_layoutgen_adapter",
    "integration_readiness": "candidate_contract_only_not_physical_ready",
    "forbidden_claims": "no_delay_proof;no_timing_closure;no_physical_integration;no_time_control_gds"
  },
  {
    "control_object": "WORDLINE_ENABLE_PATH",
    "priority": 4,
    "openyield_source_file": "/data1/qujh/work/external/OpenYield/sram_compiler/subcircuits/time_generate.py",
    "source_symbol": "wl_pdrive + inv_wl_en_bar",
    "source_ports_or_nodes": "gated_clk_bar -> wl_en -> wl_en_bar",
    "local_candidate_name": "wordline_enable_path",
    "candidate_type": "candidate_contract",
    "candidate_artifact": "docs/candidate_spice/control_paths/wordline_enable_path_candidate_contract.inc",
    "spice_candidate_available": true,
    "testbench_skeleton_available": true,
    "timing_metadata_available": false,
    "source_evidence_status": "source_linked_candidate_contract_available",
    "recovery_status": "source_linked_contract_generated_requires_transistor_or_stdcell_binding",
    "blocked_reason": "needs_model_recovery_and_path_specific_transient_smoke",
    "next_required_action": "needs_spice_model;needs_transient_smoke;needs_mapping_to_layoutgen_adapter",
    "integration_readiness": "candidate_contract_only_not_physical_ready",
    "forbidden_claims": "no_delay_proof;no_timing_closure;no_physical_integration;no_time_control_gds"
  },
  {
    "control_object": "GATED_CLOCK_PATH",
    "priority": 5,
    "openyield_source_file": "/data1/qujh/work/external/OpenYield/sram_compiler/subcircuits/time_generate.py",
    "source_symbol": "and2_gated_clk_bar / and2_gated_clk_buf",
    "source_ports_or_nodes": "cs, clk_bar -> gated_clk_bar; cs, clk_buf -> gated_clk_buf",
    "local_candidate_name": "gated_clock_path",
    "candidate_type": "candidate_contract",
    "candidate_artifact": "docs/candidate_spice/control_paths/gated_clock_path_candidate_contract.inc",
    "spice_candidate_available": true,
    "testbench_skeleton_available": true,
    "timing_metadata_available": false,
    "source_evidence_status": "source_linked_candidate_contract_available",
    "recovery_status": "source_linked_contract_generated_requires_transistor_or_stdcell_binding",
    "blocked_reason": "needs_model_recovery_and_path_specific_transient_smoke",
    "next_required_action": "needs_spice_model;needs_transient_smoke;needs_mapping_to_layoutgen_adapter",
    "integration_readiness": "candidate_contract_only_not_physical_ready",
    "forbidden_claims": "no_delay_proof;no_timing_closure;no_physical_integration;no_time_control_gds"
  },
  {
    "control_object": "DFF_ROW",
    "priority": 6,
    "openyield_source_file": "/data1/qujh/work/external/OpenYield/sram_compiler/subcircuits/time_generate.py",
    "source_symbol": "dff / DFF_BUF / ADDR_DFF",
    "source_ports_or_nodes": "VDD, VSS, D, Q, CLK and row-indexed A/A_dff nodes",
    "local_candidate_name": "dff_row",
    "candidate_type": "candidate_contract",
    "candidate_artifact": "docs/candidate_spice/control_paths/dff_row_candidate_contract.inc",
    "spice_candidate_available": true,
    "testbench_skeleton_available": true,
    "timing_metadata_available": false,
    "source_evidence_status": "source_linked_candidate_contract_available",
    "recovery_status": "source_linked_contract_generated_requires_transistor_or_stdcell_binding",
    "blocked_reason": "needs_model_recovery_and_path_specific_transient_smoke",
    "next_required_action": "needs_spice_model;needs_transient_smoke;needs_mapping_to_layoutgen_adapter",
    "integration_readiness": "candidate_contract_only_not_physical_ready",
    "forbidden_claims": "no_delay_proof;no_timing_closure;no_physical_integration;no_time_control_gds"
  }
]
```

## Summary

```json
{
  "precharge_candidate_artifact": "docs/candidate_spice/control_paths/precharge_candidate_contract.sp",
  "precharge_enable_candidate_artifact": "docs/candidate_spice/control_paths/precharge_enable_candidate_tb.sp",
  "remaining_blocked_objects": [
    "PRECHARGE",
    "PRECHARGE_ENABLE_PATH",
    "SENSE_ENABLE_PATH",
    "WRITE_ENABLE_PATH",
    "WORDLINE_ENABLE_PATH",
    "GATED_CLOCK_PATH",
    "DFF_ROW"
  ],
  "next_gate": "selected_control_path_spice_smoke_or_guarded_adapter_registry"
}
```