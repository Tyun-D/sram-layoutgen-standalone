# OpenYield Source-Linked Timing Metadata Audit Report

- Repo root: `/data1/qujh/work/sram_layoutgen_step45_clean`
- Repo HEAD: `fe96f55ccc3588ff9ae431ce64db47b0899b6693`
- OpenYield HEAD: `1c34428d8b913963c4971d093b1a7c2df97a2509`

## Delay Chain Summary

```json
{
  "evidence_status": "source_linked_and_smoke_timing_metadata_available",
  "worst_smoke_delay_s": 2.15738e-10,
  "corner_coverage": "nom/ff/ss @ VDD=1.0, TEMP=25C"
}
```

## Gates

```json
{
  "source_linked_timing_metadata_available": true,
  "delay_chain_source_linked": true,
  "delay_chain_timing_metadata_available": true,
  "control_mapping_table_available": true,
  "delay_chain_ready_for_metadata_consumption": true,
  "any_control_path_ready_for_physical_integration": false,
  "can_enter_metadata_consumer_adapter": true,
  "can_modify_standalone_now": false,
  "can_generate_time_control_gds_now": false,
  "can_claim_openyield_full_integration_now": false
}
```

## Boundary Assertions

```json
{
  "standalone_modified": false,
  "routing_modified": false,
  "gds_writer_modified": false,
  "time_control_gds_generated": false,
  "delay_proof_claimed": false,
  "timing_closure_claimed": false,
  "physical_integration_enabled": false
}
```