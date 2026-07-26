# OpenYield WRITEDRIVER Placement Smoke Report

- power status: `vdd_gnd_metadata_present`
- safe_for_physical_mapping: `True`
- safe_for_shared_rail: `False`
- can enter limited placement: `True`
- semantic coexistence with column mux / sense amp / storage array: `True`
- standalone modified: `False`
- routing changed: `False`
- GDS writer changed: `False`
- write_driver changed: `False`

## Primary Plan

- placement count: `16`
- macro name: `write_driver`
- grouped mapping needs confirmation: `False`
- semantic coexistence reason: `placement planning is metadata-only and leaves routing/shared rails untouched.`
- example placements: `3`

| instance | col | group | cols | x | y | orientation | macro |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Xwd_c0 | 0 | 0 | 0 | 0.0 | 0.0 | R0 | write_driver |
| Xwd_c1 | 1 | 1 | 1 | 0.895 | 0.0 | R0 | write_driver |
| Xwd_c2 | 2 | 2 | 2 | 1.79 | 0.0 | R0 | write_driver |

## Pin Mapping

| OpenYield pin | Local pin | Canonical signal |
| --- | --- | --- |
| VDD | vdd | vdd |
| VSS | gnd | gnd |
| EN | write_enable | write_enable |
| DIN | din | din |
| BL | bl | bl |
| BLB | br | br |

## Extra Grouped Example

- placement count: `16`
- grouped mapping needs confirmation: `True`
- macro name: `write_driver`

## Notes

- OpenYield WRITEDRIVER exposes only DIN and EN externally; internal DINB/ENB generation stays inside the SPICE macro.
- BL/BLB map to the local bl/br pins without a routing rewrite.
- Shared rail remains disabled until a separate rail continuity proof exists.
- This smoke is metadata-only and does not modify standalone, routing, or GDS writer code.
- The physical write path is intentionally left untouched.
