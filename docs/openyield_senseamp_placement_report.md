# OpenYield SenseAmp Placement Adapter Report

This Step 5.2 report is adapter-only smoke. It does not modify standalone placement, routing, GDS writer, or OpenYield source.

## Inputs

- cols: `16`
- mux_ratio: `1`
- origin_x: `0.0`
- origin_y: `0.0`
- pitch_x: `0.895`
- tech_dir: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45`

## Summary

- adapter strategy: `single_ended_q_to_dout`
- placement count: `16`
- local sense_amp pins: `bl, br, dout, en, vdd, gnd`
- OpenYield SENSEAMP pins: `VDD, VSS, EN, IN, INB, Q, QB`
- requires netlist rewrite: `True`
- requires layout pin: `False`
- generated fake dout_b: `False`
- can enter standalone sense_amp opt-in placement: `True`

## Mapping Rules

| OpenYield pin | Local pin/net meaning | Physical? |
| --- | --- | --- |
| VDD | vdd | yes |
| VSS | gnd | yes |
| EN | en / sense_enable | yes |
| IN | bl | yes |
| INB | br | yes |
| Q | dout | yes |
| QB | dropped_complementary_output | no |

## Example Placements

| instance | x | y | orientation | nets | dropped pins |
| --- | --- | --- | --- | --- | --- |
| Xsa_c0 | 0.0 | 0.0 | R0 | `{'vdd': 'vdd', 'gnd': 'gnd', 'en': 'sense_enable', 'bl': 'bl[0]', 'br': 'br[0]', 'dout': 'dout[0]'}` | `{'QB': 'dropped_complementary_output'}` |
| Xsa_c1 | 0.895 | 0.0 | R0 | `{'vdd': 'vdd', 'gnd': 'gnd', 'en': 'sense_enable', 'bl': 'bl[1]', 'br': 'br[1]', 'dout': 'dout[1]'}` | `{'QB': 'dropped_complementary_output'}` |
| Xsa_c2 | 1.79 | 0.0 | R0 | `{'vdd': 'vdd', 'gnd': 'gnd', 'en': 'sense_enable', 'bl': 'bl[2]', 'br': 'br[2]', 'dout': 'dout[2]'}` | `{'QB': 'dropped_complementary_output'}` |
| Xsa_c3 | 2.685 | 0.0 | R0 | `{'vdd': 'vdd', 'gnd': 'gnd', 'en': 'sense_enable', 'bl': 'bl[3]', 'br': 'br[3]', 'dout': 'dout[3]'}` | `{'QB': 'dropped_complementary_output'}` |

## Checks

- local_macro_is_sense_amp: `True`
- local_pins_match_expected: `True`
- q_to_dout_established: `True`
- qb_to_dout_b_established: `False`
- qb_recorded_as_dropped: `True`
- fake_dout_b_generated: `False`
- safe_for_physical_mapping: `True`
- requires_netlist_rewrite: `True`
- requires_layout_pin: `False`
- modified_standalone: `False`
- modified_routing_or_gds_writer: `False`

## Conclusions

- `QB` is recorded only in metadata and dropped-pin tables.
- No physical `dout_b`, `qb`, or `sense_qb` output net is generated.
- The plan is safe only for the current single-ended `Q -> dout` sense_amp architecture.
- This smoke does not place write drivers, column muxes, wordline drivers, or control logic.

## Next Step

- Use this placement adapter as an explicit opt-in layer before touching standalone peripheral placement.
