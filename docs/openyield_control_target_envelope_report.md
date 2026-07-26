# OpenYield Control Target Envelope Report

This is a metadata-only decoder envelope and write-driver target audit. It does not modify standalone.py, routing, or the GDS writer.

## Summary

- decoder_envelope_bound: `True`
- write_driver_target_bound: `True`
- decoder_envelope_is_metadata_only: `True`
- decoder_envelope_pin_proven: `False`
- write_driver_target_uses_gds_pin_side: `True`
- decoder_envelope_conflict_found: `False`
- write_driver_target_conflict_found: `False`
- hardmacro_overlap_found: `False`
- physical_routing_proven: `False`
- can_enter_very_limited_physical_smoke: `False`
- can_enter_standalone_control_placement: `False`

## Decoder Envelope

```json
{
  "envelope_name": "DECODER_CASCADE_ENVELOPE",
  "target_block": "DECODER_CASCADE",
  "envelope_policy": "metadata_generated_block",
  "geometry_source": "decomposition_graph_plus_anchor_window",
  "pin_proven": false,
  "input_nets": [
    "A[0]",
    "A[1]",
    "A[2]",
    "A[3]",
    "A[4]"
  ],
  "input_source_nets": [
    "addr_q[0]",
    "addr_q[1]",
    "addr_q[2]",
    "addr_q[3]",
    "addr_q[4]"
  ],
  "input_anchor": "DECODER_INPUT_ANCHOR",
  "input_window": "ADDR_TO_DECODER_WINDOW",
  "input_side_hint": "decoder_input_side",
  "output_nets": [
    "WL[*]"
  ],
  "output_consumer": "WORDLINEDRIVER.A / decoder_input",
  "output_side_hint": "wordline_driver_side",
  "metadata_only": true,
  "physical_access_proven": false,
  "physical_routing_proven": false,
  "candidate_bbox": {
    "x0": 17.099999999999984,
    "y0": 0.0,
    "x1": 21.099999999999984,
    "y1": 2.67,
    "width": 4.0,
    "height": 2.67
  },
  "decoder_envelope_bbox_is_estimated": true,
  "decoder_candidate_bbox_is_metadata_only": true,
  "decoder_candidate_bbox_not_physical_layout": true,
  "decoder_hardmacro_pin_proven": false
}
```

## Write-Driver Target

```json
{
  "target_name": "WRITEDRIVER_ARRAY_INPUT_TARGET",
  "target_block": "WRITEDRIVER",
  "target_policy": "gds_pin_side_array_reference",
  "geometry_source": "write_driver_gds_pin_side",
  "write_driver_side_pin_known": true,
  "write_driver_input_side": "bottom",
  "input_nets": [
    "DIN[0]",
    "DIN[1]",
    "DIN[2]",
    "DIN[3]"
  ],
  "source_nets": [
    "din_q[0]",
    "din_q[1]",
    "din_q[2]",
    "din_q[3]"
  ],
  "source_window": "DATA_TO_WRITEDRIVER_WINDOW",
  "array_reference": "WRITEDRIVER column/data group input side",
  "metadata_only": true,
  "physical_access_proven": true,
  "physical_routing_proven": false,
  "target_bbox": {
    "x0": 0.0,
    "y0": 8.01,
    "x1": 0.839999999999995,
    "y1": 10.01,
    "width": 0.839999999999995,
    "height": 2.0
  }
}
```

## Blockers

- Decoder envelope is still an estimated generated-block metadata box, not a physical decoder layout.
- Write-driver target is tied to GDS pin-side evidence, but no routed connection from DATA_DFF_ROW exists yet.
- No physical routing or clock skew proof exists for decoder/output handoff.
- Very-limited physical smoke still lacks decoder-side concrete layout evidence.

## Step 6.9 Recommendation

- Next, refine DECODER_CASCADE into explicit stage/group metadata candidates, or stop and summarize blockers before any control-row physical smoke attempt.
