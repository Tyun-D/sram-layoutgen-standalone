# OpenYield Control Anchor Binding Report

This is a metadata-only anchor binding audit. It does not modify standalone.py, routing, or the GDS writer.

## Summary

- decoder_side_geometry_proven: `False`
- write_driver_side_pin_known: `True`
- anchor_binding_success: `True`
- decoder_anchor_is_metadata_only: `True`
- write_driver_anchor_uses_gds_pin_side: `True`
- anchor_keepout_conflict_found: `False`
- anchor_hardmacro_overlap_found: `False`
- physical_routing_proven: `False`
- can_enter_limited_physical_smoke: `False`
- can_enter_standalone_control_placement: `False`

## Anchors

```json
{
  "decoder_anchor": {
    "anchor_name": "DECODER_INPUT_ANCHOR",
    "target_block": "DECODER_CASCADE",
    "anchor_policy": "metadata_window",
    "input_nets": [
      "A[0]",
      "A[1]",
      "A[2]",
      "A[3]",
      "A[4]"
    ],
    "source_nets": [
      "addr_q[0]",
      "addr_q[1]",
      "addr_q[2]",
      "addr_q[3]",
      "addr_q[4]"
    ],
    "source_window": "ADDR_TO_DECODER_WINDOW",
    "geometry_source": "metadata_only",
    "decoder_side_geometry_proven": false,
    "decoder_pin_proof_required": true,
    "physical_access_proven": false,
    "physical_routing_proven": false,
    "bbox": {
      "x0": 15.099999999999984,
      "y0": 0.0,
      "x1": 17.099999999999984,
      "y1": 2.67,
      "width": 2.0,
      "height": 2.67
    },
    "side_hint": "decoder_input_side",
    "metadata_only": true,
    "decoder_anchor_geometry_source": "metadata_window"
  },
  "write_driver_anchor": {
    "anchor_name": "WRITEDRIVER_INPUT_ANCHOR",
    "target_block": "WRITEDRIVER",
    "anchor_policy": "gds_pin_side",
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
    "geometry_source": "write_driver_gds_pin_side",
    "write_driver_side_pin_known": true,
    "write_driver_input_side": "bottom",
    "physical_access_proven": true,
    "physical_routing_proven": false,
    "bbox": {
      "x0": 0.0,
      "y0": 8.01,
      "x1": 0.839999999999995,
      "y1": 10.01,
      "width": 0.839999999999995,
      "height": 2.0
    },
    "side_hint": "write_driver_input_side",
    "metadata_only": false
  }
}
```

## Overlap Checks

```json
{
  "anchor_row_overlap": {
    "decoder_anchor": {
      "ADDR_DFF_ROW": false,
      "DATA_DFF_ROW": false
    },
    "write_driver_anchor": {
      "ADDR_DFF_ROW": false,
      "DATA_DFF_ROW": false
    }
  },
  "anchor_keepout_overlap": {
    "decoder_anchor": {
      "CLOCK_CHANNEL_KEEPOUT": false,
      "ADDR_TO_DECODER_KEEPOUT": true,
      "DATA_TO_WRITEDRIVER_KEEPOUT": false
    },
    "write_driver_anchor": {
      "CLOCK_CHANNEL_KEEPOUT": false,
      "ADDR_TO_DECODER_KEEPOUT": false,
      "DATA_TO_WRITEDRIVER_KEEPOUT": true
    }
  }
}
```

## Blockers

- Decoder anchor is still metadata-only because DECODER_CASCADE is not a pin-proven hard macro.
- Write-driver anchor uses GDS pin-side evidence, but route completion is still unproven.
- No physical routing or clock skew proof exists for the bound anchors.
- Standalone control placement remains disabled until anchor binding is backed by real placement/legalization evidence.

## Step 6.8 Recommendation

- Next, convert decoder-side metadata anchors into explicit local placement candidates or generated-block envelopes before any limited physical smoke.
