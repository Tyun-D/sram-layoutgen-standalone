# OpenYield Control Timing Mapping Review Report

- Repo root: `/data1/qujh/work/sram_layoutgen_step45_clean`
- Repo HEAD: `fe96f55ccc3588ff9ae431ce64db47b0899b6693`
- OpenYield HEAD: `1c34428d8b913963c4971d093b1a7c2df97a2509`

## Summary

```json
{
  "mapped_object_count": 9,
  "objects_with_smoke_timing_metadata": [
    "DELAY_CHAIN",
    "RBL_DELAY_PATH"
  ],
  "objects_source_identified_only": [
    "SENSE_ENABLE_PATH",
    "PRECHARGE_ENABLE_PATH",
    "WRITE_ENABLE_PATH",
    "WORDLINE_ENABLE_PATH",
    "GATED_CLOCK_PATH",
    "DFF_ROW",
    "PRECHARGE"
  ],
  "next_gate": "metadata_consumer_adapter"
}
```

## Mapping Rows

```json
[
  {
    "openyield_object": "DELAY_CHAIN",
    "openyield_source_file": "/data1/qujh/work/external/OpenYield/sram_compiler/subcircuits/time_generate.py",
    "openyield_signal_or_node": "rbl->rbl_delay",
    "local_timing_object": "DELAY_CHAIN",
    "local_candidate_artifact": "docs/candidate_spice/gen_delay_inv_candidate.sp;docs/candidate_spice/delay_chain_measurement_refined_ngspice.sp",
    "local_metadata_artifact": "docs/openyield_delay_chain_timing_metadata_report.json;docs/evidence/timing_metadata_summary.md",
    "evidence_status": "source_linked_and_smoke_timing_metadata_available",
    "measured_delay_available": true,
    "worst_smoke_delay_s": 2.15738e-10,
    "corner_coverage": "nom/ff/ss @ VDD=1.0, TEMP=25C",
    "integration_readiness": "ready_for_control_timing_metadata_consumption_not_physical_integration",
    "next_required_action": "implement_metadata_consumer_adapter_without_touching_standalone",
    "forbidden_claims": "no_delay_proof;no_timing_closure;no_physical_integration;no_time_control_gds"
  },
  {
    "openyield_object": "RBL_DELAY_PATH",
    "openyield_source_file": "/data1/qujh/work/external/OpenYield/sram_compiler/subcircuits/time_generate.py",
    "openyield_signal_or_node": "rbl_delay;rbl_delay_bar",
    "local_timing_object": "DELAY_CHAIN_RBL_PATH",
    "local_candidate_artifact": "docs/candidate_spice/delay_chain_measurement_refined_ngspice.sp",
    "local_metadata_artifact": "docs/openyield_delay_chain_timing_metadata_report.json",
    "evidence_status": "source_linked_and_smoke_timing_metadata_available",
    "measured_delay_available": true,
    "worst_smoke_delay_s": 2.15738e-10,
    "corner_coverage": "nom/ff/ss @ VDD=1.0, TEMP=25C",
    "integration_readiness": "ready_for_control_timing_metadata_consumption_not_physical_integration",
    "next_required_action": "map_rbl_delay_metadata_to_adapter_consumer",
    "forbidden_claims": "no_delay_proof;no_timing_closure;no_physical_integration;no_time_control_gds"
  },
  {
    "openyield_object": "SENSE_ENABLE_PATH",
    "openyield_source_file": "/data1/qujh/work/external/OpenYield/sram_compiler/subcircuits/time_generate.py",
    "openyield_signal_or_node": "s_en<=AND3(rbl_delay,gated_clk_bar,we_bar)",
    "local_timing_object": "SENSE_ENABLE_PATH",
    "local_candidate_artifact": "",
    "local_metadata_artifact": "",
    "evidence_status": "source_identified_only",
    "measured_delay_available": false,
    "worst_smoke_delay_s": "",
    "corner_coverage": "none",
    "integration_readiness": "not_ready_needs_candidate_spice_and_transient_smoke",
    "next_required_action": "needs_candidate_spice;needs_spice_model;needs_transient_smoke;needs_mapping_to_layoutgen_adapter",
    "forbidden_claims": "no_delay_proof;no_timing_closure;no_physical_integration;no_time_control_gds"
  },
  {
    "openyield_object": "PRECHARGE_ENABLE_PATH",
    "openyield_source_file": "/data1/qujh/work/external/OpenYield/sram_compiler/subcircuits/time_generate.py",
    "openyield_signal_or_node": "PRE_UNBUF/PRE<=PNAND3(gated_clk_buf,rbl_delay,wl_en_bar)",
    "local_timing_object": "PRECHARGE_ENABLE_PATH",
    "local_candidate_artifact": "",
    "local_metadata_artifact": "",
    "evidence_status": "source_identified_only",
    "measured_delay_available": false,
    "worst_smoke_delay_s": "",
    "corner_coverage": "none",
    "integration_readiness": "not_ready_needs_candidate_spice_and_transient_smoke",
    "next_required_action": "needs_candidate_spice;needs_spice_model;needs_transient_smoke;needs_mapping_to_layoutgen_adapter",
    "forbidden_claims": "no_delay_proof;no_timing_closure;no_physical_integration;no_time_control_gds"
  },
  {
    "openyield_object": "WRITE_ENABLE_PATH",
    "openyield_source_file": "/data1/qujh/work/external/OpenYield/sram_compiler/subcircuits/time_generate.py",
    "openyield_signal_or_node": "w_en<=AND3(rbl_delay_bar/gated_variant,gated_clk_bar,we)",
    "local_timing_object": "WRITE_ENABLE_PATH",
    "local_candidate_artifact": "",
    "local_metadata_artifact": "",
    "evidence_status": "source_identified_only",
    "measured_delay_available": false,
    "worst_smoke_delay_s": "",
    "corner_coverage": "none",
    "integration_readiness": "not_ready_needs_candidate_spice_and_transient_smoke",
    "next_required_action": "needs_candidate_spice;needs_spice_model;needs_transient_smoke;needs_mapping_to_layoutgen_adapter",
    "forbidden_claims": "no_delay_proof;no_timing_closure;no_physical_integration;no_time_control_gds"
  },
  {
    "openyield_object": "WORDLINE_ENABLE_PATH",
    "openyield_source_file": "/data1/qujh/work/external/OpenYield/sram_compiler/subcircuits/time_generate.py",
    "openyield_signal_or_node": "wl_en;wl_en_bar",
    "local_timing_object": "WORDLINE_ENABLE_PATH",
    "local_candidate_artifact": "",
    "local_metadata_artifact": "",
    "evidence_status": "source_identified_only",
    "measured_delay_available": false,
    "worst_smoke_delay_s": "",
    "corner_coverage": "none",
    "integration_readiness": "not_ready_needs_candidate_spice_and_transient_smoke",
    "next_required_action": "needs_candidate_spice;needs_spice_model;needs_transient_smoke;needs_mapping_to_layoutgen_adapter",
    "forbidden_claims": "no_delay_proof;no_timing_closure;no_physical_integration;no_time_control_gds"
  },
  {
    "openyield_object": "GATED_CLOCK_PATH",
    "openyield_source_file": "/data1/qujh/work/external/OpenYield/sram_compiler/subcircuits/time_generate.py",
    "openyield_signal_or_node": "gated_clk_bar;gated_clk_buf",
    "local_timing_object": "GATED_CLOCK_PATH",
    "local_candidate_artifact": "",
    "local_metadata_artifact": "",
    "evidence_status": "source_identified_only",
    "measured_delay_available": false,
    "worst_smoke_delay_s": "",
    "corner_coverage": "none",
    "integration_readiness": "not_ready_needs_candidate_spice_and_transient_smoke",
    "next_required_action": "needs_candidate_spice;needs_spice_model;needs_transient_smoke;needs_mapping_to_layoutgen_adapter",
    "forbidden_claims": "no_delay_proof;no_timing_closure;no_physical_integration;no_time_control_gds"
  },
  {
    "openyield_object": "DFF_ROW",
    "openyield_source_file": "/data1/qujh/work/external/OpenYield/sram_compiler/subcircuits/time_generate.py",
    "openyield_signal_or_node": "ADDR_DFF/A_dff*;TIME A*->A_dff*",
    "local_timing_object": "ADDR_DFF_ROW",
    "local_candidate_artifact": "",
    "local_metadata_artifact": "",
    "evidence_status": "source_identified_only",
    "measured_delay_available": false,
    "worst_smoke_delay_s": "",
    "corner_coverage": "none",
    "integration_readiness": "not_ready_needs_candidate_spice_and_transient_smoke",
    "next_required_action": "needs_candidate_spice;needs_spice_model;needs_transient_smoke;needs_mapping_to_layoutgen_adapter",
    "forbidden_claims": "no_delay_proof;no_timing_closure;no_physical_integration;no_time_control_gds"
  },
  {
    "openyield_object": "PRECHARGE",
    "openyield_source_file": "/data1/qujh/work/external/OpenYield/sram_compiler/subcircuits/precharge_and_write_driver.py",
    "openyield_signal_or_node": "PRE-driven precharge devices",
    "local_timing_object": "PRECHARGE",
    "local_candidate_artifact": "",
    "local_metadata_artifact": "",
    "evidence_status": "source_identified_only",
    "measured_delay_available": false,
    "worst_smoke_delay_s": "",
    "corner_coverage": "none",
    "integration_readiness": "not_ready_needs_candidate_spice_and_transient_smoke",
    "next_required_action": "needs_candidate_spice;needs_spice_model;needs_transient_smoke;needs_mapping_to_layoutgen_adapter",
    "forbidden_claims": "no_delay_proof;no_timing_closure;no_physical_integration;no_time_control_gds"
  }
]
```