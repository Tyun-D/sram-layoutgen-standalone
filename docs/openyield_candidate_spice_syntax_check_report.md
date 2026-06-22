# OpenYield Candidate SPICE Syntax Check Report

- Scope: `candidate_spice_syntax_check_and_simulator_binding`
- Candidate dir: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\docs\candidate_spice`

## Audit Summary

```json
{
  "candidate_spice_syntax_check_available": true,
  "simulator_found": false,
  "selected_simulator": null,
  "pdk_include_binding_available": true,
  "local_model_include_emitted": true,
  "static_spice_check_pass": true,
  "syntax_smoke_attempted": false,
  "syntax_smoke_pass": false,
  "can_run_candidate_spice_now": false,
  "can_run_delay_chain_testbench_now": false,
  "can_claim_delay_proof_now": false,
  "can_claim_timing_closure_now": false,
  "needs_user_simulator_install": true,
  "needs_user_vdd_corner_threshold": true,
  "needs_teacher_or_project_provider": false,
  "can_enter_pvt_corner_definition_plan": true,
  "can_enter_delay_chain_smoke_simulation": false,
  "can_enter_physical_timing_closure_now": false,
  "can_enter_physical_routing_now": false,
  "can_enter_physical_placement_now": false,
  "can_generate_time_control_gds_now": false,
  "can_modify_standalone_now": false
}
```

## Simulator Detection

| simulator | found | version | path | hspice include syntax | basic parse | issue | recommended |
| --- | --- | --- | --- | --- | --- | --- | --- |
| hspice | False | None | None | False | False | not_found_in_PATH | False |
| ngspice | False | None | None | False | False | not_found_in_PATH | False |
| spectre | False | None | None | False | False | not_found_in_PATH | False |

## PDK Include Binding

```json
{
  "pdk_dir_required": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\technology\\freepdk45\\models",
  "pdk_dir_candidate": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\technology\\freepdk45\\models",
  "pdk_dir_env_already_set": null,
  "pdk_dir_env_needed": true,
  "hspice_include_resolves": true,
  "direct_model_includes_resolve": true,
  "hspice_nom_include": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\technology\\freepdk45\\models\\hspice_nom.include",
  "direct_nominal_model_includes": [
    "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\technology\\freepdk45\\models\\tran_models\\models_nom\\PMOS_VTG.inc",
    "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\technology\\freepdk45\\models\\tran_models\\models_nom\\NMOS_VTG.inc"
  ],
  "candidate_local_include_target": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\candidate_spice\\local_model_include_nom.inc",
  "notes": [
    "The HSPICE include file uses $PDK_DIR/ncsu_basekit/... syntax and may require a tool-specific environment mapping.",
    "Direct .inc binding to nominal PMOS_VTG/NMOS_VTG is available and is safer for a local candidate smoke include."
  ]
}
```

## Static SPICE Check

```json
{
  "static_spice_check_pass": true,
  "subckt_check_pass": true,
  "model_name_check_pass": true,
  "include_path_check_pass": true,
  "stage_count_check_pass": true,
  "four_load_check_pass": true,
  "dummy_node_check_pass": true,
  "measure_placeholder_check_pass": true,
  "boundary_text_check_pass": true,
  "issues": [],
  "local_model_include_path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\candidate_spice\\local_model_include_nom.inc",
  "candidate_files_checked": [
    "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\candidate_spice\\gen_delay_inv_candidate.sp",
    "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\candidate_spice\\delay_chain_symbolic_tb.sp",
    "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\candidate_spice\\delay_chain_measure.inc",
    "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\candidate_spice\\delay_chain_corner_placeholder.inc",
    "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\candidate_spice\\README.md"
  ]
}
```

## Optional Syntax Smoke

```json
{
  "syntax_smoke_attempted": false,
  "syntax_smoke_pass": false,
  "simulator_used": null,
  "smoke_file": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\candidate_spice\\delay_chain_syntax_smoke.sp",
  "log_path": null,
  "issues": [
    "No simulator found in PATH; syntax smoke not attempted."
  ]
}
```

## Issues

- No simulator found in PATH; syntax smoke not attempted.

## What Codex Can Fix

- Emit a local direct-model include file for TT/nominal binding
- Check candidate SPICE structure, pin order, stage count, load count, and placeholder policy
- Prepare a simulator-specific syntax smoke deck when a simulator becomes available

## What Needs User / Teacher

- Install or provide a simulator in PATH if smoke parse is required now
- Confirm project simulator choice
- Provide formal VDD, PVT corner, and threshold policy before any real simulation

## Boundary Assertions

```json
{
  "static_check_is_not_timing_proof": true,
  "syntax_smoke_is_not_delay_proof": true,
  "standalone_modified": false,
  "routing_modified": false,
  "gds_writer_modified": false
}
```

## Next Recommended Task

- `install_or_bind_simulator_then_define_vdd_corner_threshold`