# OpenYield Delay Chain PVT Corner Smoke Report

- Scope: `delay_chain_pvt_corner_smoke`
- Repo root: `/data1/qujh/work/sram_layoutgen_step45_clean`
- Repo HEAD: `4eeeee106db316f4d09322c02c4152c28acf5d77`
- Previous measurement refinement commit: `4eeeee106db316f4d09322c02c4152c28acf5d77`
- Summary CSV: `/data1/qujh/work/sram_layoutgen_step45_clean/docs/candidate_spice/pvt_smoke/delay_chain_pvt_smoke_summary.csv`

## Audit Summary

```json
{
  "delay_chain_pvt_corner_smoke_available": true,
  "repo_head": "4eeeee106db316f4d09322c02c4152c28acf5d77",
  "ngspice_found": true,
  "corner_models_found": true,
  "nom_model_found": true,
  "ff_model_found": true,
  "ss_model_found": true,
  "pvt_matrix_defined": true,
  "corner_decks_generated": true,
  "corner_runs_attempted": true,
  "nom_run_pass": true,
  "ff_run_pass": true,
  "ss_run_pass": true,
  "nom_delay_available": true,
  "ff_delay_available": true,
  "ss_delay_available": true,
  "pvt_summary_available": true,
  "worst_smoke_delay_available": true,
  "worst_smoke_delay_corner": "ss",
  "can_enter_timing_metadata_update": true,
  "can_claim_delay_proof_now": false,
  "can_claim_timing_closure_now": false,
  "can_enter_physical_timing_closure_now": false,
  "can_enter_physical_routing_now": false,
  "can_enter_physical_placement_now": false,
  "can_generate_time_control_gds_now": false,
  "can_modify_standalone_now": false,
  "evidence_timeline_updated": true,
  "milestone_summary_updated": true
}
```

## Corner Models

```json
{
  "nom": {
    "include_path": "/data1/qujh/work/sram_layoutgen_step45_clean/docs/candidate_spice/local_model_include_nom_server.inc",
    "nmos_model": "/data1/qujh/OpenRAM/technology/freepdk45/models/tran_models/models_nom/NMOS_VTG.inc",
    "pmos_model": "/data1/qujh/OpenRAM/technology/freepdk45/models/tran_models/models_nom/PMOS_VTG.inc",
    "found": true
  },
  "ff": {
    "include_path": "/data1/qujh/work/sram_layoutgen_step45_clean/docs/candidate_spice/local_model_include_ff_server.inc",
    "nmos_model": "/data1/qujh/OpenRAM/technology/freepdk45/models/tran_models/models_ff/NMOS_VTG.inc",
    "pmos_model": "/data1/qujh/OpenRAM/technology/freepdk45/models/tran_models/models_ff/PMOS_VTG.inc",
    "found": true
  },
  "ss": {
    "include_path": "/data1/qujh/work/sram_layoutgen_step45_clean/docs/candidate_spice/local_model_include_ss_server.inc",
    "nmos_model": "/data1/qujh/OpenRAM/technology/freepdk45/models/tran_models/models_ss/NMOS_VTG.inc",
    "pmos_model": "/data1/qujh/OpenRAM/technology/freepdk45/models/tran_models/models_ss/PMOS_VTG.inc",
    "found": true
  }
}
```

## PVT Matrix

```json
{
  "corners": [
    "nom",
    "ff",
    "ss"
  ],
  "vdd_volts": 1.0,
  "temp_c": 25,
  "optional_not_run": {
    "low_vdd": 0.9,
    "high_vdd": 1.1,
    "low_temp_c": 0,
    "high_temp_c": 85
  }
}
```

## Corner Table

| corner | VDD | TEMP | run pass | measure pass | rise-to-fall | fall-to-rise | max delay | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nom | 1.0 | 25 | True | True | 1.963452e-10 | 1.87624e-10 | 1.963452e-10 | ngspice measure passed |
| ff | 1.0 | 25 | True | True | 1.801558e-10 | 1.715128e-10 | 1.801558e-10 | ngspice measure passed |
| ss | 1.0 | 25 | True | True | 2.15738e-10 | 2.067219e-10 | 2.15738e-10 | ngspice measure passed |

## Worst Smoke Delay

```json
{
  "corner": "ss",
  "VDD": 1.0,
  "TEMP": 25,
  "deck_path": "/data1/qujh/work/sram_layoutgen_step45_clean/docs/candidate_spice/pvt_smoke/delay_chain_pvt_ss_ngspice.sp",
  "log_path": "/data1/qujh/work/sram_layoutgen_step45_clean/docs/candidate_spice/pvt_smoke/delay_chain_pvt_ss_ngspice.log",
  "ngspice_run_pass": true,
  "measure_pass": true,
  "postprocess_pass": true,
  "rise_to_fall_delay_s": 2.15738e-10,
  "fall_to_rise_delay_s": 2.067219e-10,
  "max_delay_s": 2.15738e-10,
  "warnings": [
    "Warning: toxe, toxp and dtox all given and toxe != toxp + dtox; dtox ignored.",
    "Trying gmin =   1.0000E-05 Warning: Further gmin increment",
    "Trying gmin =   6.4938E-06 Warning: Further gmin increment"
  ],
  "failure_classification": null,
  "notes": "ngspice measure passed"
}
```

## Boundary Assertions

```json
{
  "pvt_smoke_is_not_delay_proof": true,
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