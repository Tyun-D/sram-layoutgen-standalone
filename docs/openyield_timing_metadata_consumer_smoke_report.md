# OpenYield Timing Metadata Consumer Smoke Report

## Ready Objects

```json
[
  "DELAY_CHAIN",
  "RBL_DELAY_PATH"
]
```

## Blocked Objects

```json
[
  "SENSE_ENABLE_PATH",
  "PRECHARGE_ENABLE_PATH",
  "WRITE_ENABLE_PATH",
  "WORDLINE_ENABLE_PATH",
  "GATED_CLOCK_PATH",
  "DFF_ROW",
  "PRECHARGE"
]
```

## Delay Chain Summary

```json
{
  "delay_chain_consumable": true,
  "delay_chain_worst_smoke_delay_s": 2.15738e-10,
  "delay_chain_worst_corner": "ss",
  "delay_chain_corner_table": {
    "nom": {
      "rise_to_fall_delay_s": 1.963452e-10,
      "fall_to_rise_delay_s": 1.87624e-10,
      "max_delay_s": 1.963452e-10
    },
    "ff": {
      "rise_to_fall_delay_s": 1.801558e-10,
      "fall_to_rise_delay_s": 1.715128e-10,
      "max_delay_s": 1.801558e-10
    },
    "ss": {
      "rise_to_fall_delay_s": 2.15738e-10,
      "fall_to_rise_delay_s": 2.067219e-10,
      "max_delay_s": 2.15738e-10
    }
  },
  "metadata_consumer_api_available": true,
  "next_adapter_action": "control_path_candidate_generation_or_guarded_adapter_integration",
  "forbidden_actions": [
    "modify_standalone",
    "modify_routing",
    "modify_gds_writer",
    "generate_time_control_gds",
    "claim_openyield_full_integration",
    "claim_timing_closure",
    "claim_physical_integration"
  ]
}
```

## Gates

```json
{
  "metadata_consumer_adapter_available": true,
  "metadata_consumer_smoke_pass": true,
  "delay_chain_metadata_loaded": true,
  "delay_chain_source_linked": true,
  "delay_chain_ready_for_metadata_consumption": true,
  "delay_chain_ready_for_physical_integration": false,
  "blocked_control_objects_recorded": true,
  "control_mapping_loaded": true,
  "consumer_api_ready": true,
  "can_enter_control_path_candidate_generation": true,
  "can_enter_guarded_adapter_integration": true,
  "can_modify_standalone_now": false,
  "can_generate_time_control_gds_now": false,
  "can_claim_openyield_full_integration_now": false,
  "can_claim_timing_closure_now": false
}
```