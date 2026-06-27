# OpenYield Server ngspice Syntax Smoke Report

- Scope: `server_ngspice_syntax_smoke`
- Repo root: `/data1/qujh/work/sram_layoutgen_step45_clean`
- Repo HEAD: `e76b52ef1e8d5eadce2003cbb4ef6f112ceb43fe`
- Expected HEAD: `e76b52ef1e8d5eadce2003cbb4ef6f112ceb43fe`
- Candidate dir: `/data1/qujh/work/sram_layoutgen_step45_clean/docs/candidate_spice`

## Audit Summary

```json
{
  "server_ngspice_syntax_smoke_available": true,
  "server_repo_head_matches_expected": true,
  "ngspice_found": true,
  "server_model_include_generated": true,
  "ngspice_smoke_deck_generated": true,
  "syntax_smoke_attempted": true,
  "syntax_smoke_pass": true,
  "can_enter_delay_chain_smoke_simulation": true,
  "can_claim_delay_proof_now": false,
  "can_claim_timing_closure_now": false,
  "can_enter_physical_timing_closure_now": false,
  "can_enter_physical_routing_now": false,
  "can_enter_physical_placement_now": false,
  "can_generate_time_control_gds_now": false,
  "can_modify_standalone_now": false
}
```

## Server Environment

```json
{
  "path": "/usr/bin/ngspice",
  "version": "******\n** ngspice-36 : Circuit level simulation program\n** The U. C. Berkeley CAD Group\n** Copyright 1985-1994, Regents of the University of California.\n** Copyright 2001-2020, The ngspice team.\n** Please get your ngspice manual from http://ngspice.sourceforge.net/docs.html\n** Please file your bug-reports at http://ngspice.sourceforge.net/bugrep.html\n** Creation Date: Mon Mar 11 21:44:53 UTC 2024\n******"
}
```

## FreePDK45 Model Paths

```json
{
  "include_file": "/data1/qujh/work/sram_layoutgen_step45_clean/docs/candidate_spice/local_model_include_nom_server.inc",
  "includes": [
    "/data1/qujh/OpenRAM/technology/freepdk45/models/tran_models/models_nom/NMOS_VTG.inc",
    "/data1/qujh/OpenRAM/technology/freepdk45/models/tran_models/models_nom/PMOS_VTG.inc"
  ]
}
```

## Generated Server Include

```json
{
  "path": "/data1/qujh/work/sram_layoutgen_step45_clean/docs/candidate_spice/local_model_include_nom_server.inc",
  "exists": true,
  "contents": "* CANDIDATE LOCAL INCLUDE FOR SERVER NGSPICE SYNTAX SMOKE\n* NOT A VALIDATED MODEL BUNDLE\n* NOT TIMING PROOF\n\n.include \"/data1/qujh/OpenRAM/technology/freepdk45/models/tran_models/models_nom/NMOS_VTG.inc\"\n.include \"/data1/qujh/OpenRAM/technology/freepdk45/models/tran_models/models_nom/PMOS_VTG.inc\"\n"
}
```

## Generated ngspice Smoke Deck

```json
{
  "path": "/data1/qujh/work/sram_layoutgen_step45_clean/docs/candidate_spice/delay_chain_syntax_smoke_ngspice.sp",
  "exists": true,
  "contents": "* SERVER NGSPICE SYNTAX SMOKE\n* CANDIDATE / PLANNING-ONLY\n* NOT VALIDATED SPICE\n* NOT TIMING PROOF\n* DO NOT CLAIM TIMING CLOSURE\n* Temporary sources and transient settings are parse/startup-only, not formal PVT.\n\n.include \"local_model_include_nom_server.inc\"\n.include \"gen_delay_inv_candidate.sp\"\n\n.param VDD_VALUE=1.0\n.temp 25\n\nVDD_SRC vdd 0 {VDD_VALUE}\nVIN rbl 0 DC 0 PULSE(0 {VDD_VALUE} 0 10p 10p 100p 200p)\n\nXdinv0 rbl dout_1 vdd 0 gen_delay_inv\nXdload_0_0 dout_1 n_0_0 vdd 0 gen_delay_inv\nXdload_0_1 dout_1 n_0_1 vdd 0 gen_delay_inv\nXdload_0_2 dout_1 n_0_2 vdd 0 gen_delay_inv\nXdload_0_3 dout_1 n_0_3 vdd 0 gen_delay_inv\n\nXdinv1 dout_1 dout_2 vdd 0 gen_delay_inv\nXdload_1_0 dout_2 n_1_0 vdd 0 gen_delay_inv\nXdload_1_1 dout_2 n_1_1 vdd 0 gen_delay_inv\nXdload_1_2 dout_2 n_1_2 vdd 0 gen_delay_inv\nXdload_1_3 dout_2 n_1_3 vdd 0 gen_delay_inv\n\nXdinv2 dout_2 dout_3 vdd 0 gen_delay_inv\nXdload_2_0 dout_3 n_2_0 vdd 0 gen_delay_inv\nXdload_2_1 dout_3 n_2_1 vdd 0 gen_delay_inv\nXdload_2_2 dout_3 n_2_2 vdd 0 gen_delay_inv\nXdload_2_3 dout_3 n_2_3 vdd 0 gen_delay_inv\n\nXdinv3 dout_3 dout_4 vdd 0 gen_delay_inv\nXdload_3_0 dout_4 n_3_0 vdd 0 gen_delay_inv\nXdload_3_1 dout_4 n_3_1 vdd 0 gen_delay_inv\nXdload_3_2 dout_4 n_3_2 vdd 0 gen_delay_inv\nXdload_3_3 dout_4 n_3_3 vdd 0 gen_delay_inv\n\nXdinv4 dout_4 dout_5 vdd 0 gen_delay_inv\nXdload_4_0 dout_5 n_4_0 vdd 0 gen_delay_inv\nXdload_4_1 dout_5 n_4_1 vdd 0 gen_delay_inv\nXdload_4_2 dout_5 n_4_2 vdd 0 gen_delay_inv\nXdload_4_3 dout_5 n_4_3 vdd 0 gen_delay_inv\n\nXdinv5 dout_5 dout_6 vdd 0 gen_delay_inv\nXdload_5_0 dout_6 n_5_0 vdd 0 gen_delay_inv\nXdload_5_1 dout_6 n_5_1 vdd 0 gen_delay_inv\nXdload_5_2 dout_6 n_5_2 vdd 0 gen_delay_inv\nXdload_5_3 dout_6 n_5_3 vdd 0 gen_delay_inv\n\nXdinv6 dout_6 dout_7 vdd 0 gen_delay_inv\nXdload_6_0 dout_7 n_6_0 vdd 0 gen_delay_inv\nXdload_6_1 dout_7 n_6_1 vdd 0 gen_delay_inv\nXdload_6_2 dout_7 n_6_2 vdd 0 gen_delay_inv\nXdload_6_3 dout_7 n_6_3 vdd 0 gen_delay_inv\n\nXdinv7 dout_7 dout_8 vdd 0 gen_delay_inv\nXdload_7_0 dout_8 n_7_0 vdd 0 gen_delay_inv\nXdload_7_1 dout_8 n_7_1 vdd 0 gen_delay_inv\nXdload_7_2 dout_8 n_7_2 vdd 0 gen_delay_inv\nXdload_7_3 dout_8 n_7_3 vdd 0 gen_delay_inv\n\nXdinv8 dout_8 rbl_delay vdd 0 gen_delay_inv\nXdload_8_0 rbl_delay n_8_0 vdd 0 gen_delay_inv\nXdload_8_1 rbl_delay n_8_1 vdd 0 gen_delay_inv\nXdload_8_2 rbl_delay n_8_2 vdd 0 gen_delay_inv\nXdload_8_3 rbl_delay n_8_3 vdd 0 gen_delay_inv\n\n.tran 1p 400p\n.print tran v(rbl) v(rbl_delay)\n.end\n"
}
```

## Syntax Smoke Result

```json
{
  "syntax_smoke_attempted": true,
  "syntax_smoke_pass": true,
  "log_path": "/data1/qujh/work/sram_layoutgen_step45_clean/docs/candidate_spice/delay_chain_syntax_smoke_ngspice.log",
  "failure_classification": null
}
```

## Key Log Excerpt

```text
Trying gmin =   1.0000E-05 Warning: Further gmin increment
Trying gmin =   6.4938E-06 Warning: Further gmin increment
Trying gmin =   1.7154E-05 Warning: Further gmin increment
```

## Log Findings

```json
[
  "Trying gmin =   1.0000E-05 Warning: Further gmin increment",
  "Trying gmin =   6.4938E-06 Warning: Further gmin increment",
  "Trying gmin =   1.7154E-05 Warning: Further gmin increment"
]
```

## What Codex Can Fix

- Generate a server-local nominal include that uses Linux paths.
- Generate a minimal ngspice syntax smoke deck for parse/elaboration only.
- Collect ngspice logs and classify failures without claiming timing proof.
- Regenerate JSON/Markdown evidence after reruns.

## What Needs User / Teacher

- Formal VDD/PVT/slew thresholds for any real simulation remain undefined.
- Timing proof, timing closure, and physical closure require separate validated flows.

## Boundary Assertions

```json
{
  "syntax_smoke_is_not_delay_proof": true,
  "timing_closure_not_claimed": true,
  "physical_timing_closure_not_claimed": true,
  "physical_routing_not_claimed": true,
  "physical_placement_not_claimed": true,
  "time_control_gds_not_claimed": true,
  "standalone_modified": false,
  "routing_modified": false,
  "gds_writer_modified": false
}
```