# Final Risk Register

- residual_risk_count: `11`

## Entries

| risk_id | risk_name | evidence | why_it_matters | blocks_drc_clean | blocks_lvs_clean | blocks_timing_closure | recommended_future_action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RISK_01 | approximate_alignment_count=10 | outputs/openyield_structure_complete_gds/current_supported_config/pitch_alignment_report.json | Pitch ownership is not fully proven at signoff granularity. | False | False | True | Replace approximate placements with exact pitch-closed module assemblies. |
| RISK_02 | contract-pin-based routes remain | outputs/openyield_routing_power_pin/current_supported_config/wordline_routing_report.json;bitline_routing_report.json;control_routing_report.json | Some routes still terminate on semantic contract pins rather than extracted signoff pin access shapes. | False | True | False | Replace contract-backed route handoff with exact module pin geometry and LVS-aware naming. |
| RISK_03 | approximate power geometry remains | outputs/openyield_routing_power_pin/current_supported_config/power_routing_report.json | Top-level straps are prototype geometry rather than verified signoff power distribution. | False | True | False | Build explicit rail taps and continuity checks across all regions. |
| RISK_04 | detailed routing not complete | docs/openyield_R4_routing_power_pin_report.json | Prototype mapping evidence exists, but full detailed route closure is not demonstrated. | True | True | True | Add detailed via, enclosure, spacing, and obstruction-aware routing closure. |
| RISK_05 | power network not signoff verified | outputs/openyield_final_validation/current_supported_config/final_power_continuity_audit.json | Current power audit validates participation and prototype stitching only. | False | True | False | Run real IR/EM-ready power verification after exact rail synthesis. |
| RISK_06 | DRC clean not claimed | docs/openyield_R5_final_validation_handoff_report.json | Geometry may still violate spacing or enclosure rules. | True | False | False | Run DRC and feed violations into layout closure work rather than prototype assembly work. |
| RISK_07 | LVS clean not claimed | outputs/openyield_routing_power_pin/current_supported_config/net_to_shape_map.json | Net-to-shape mapping evidence is not yet equivalent to extraction-verified LVS closure. | False | True | False | Implement extractor-aligned net naming and compare against OpenYield semantic netlist. |
| RISK_08 | timing closure not claimed | docs/openyield_R5_final_validation_handoff_report.json | Replica, WL, BL, and control path delays are not timing-closed. | False | False | True | Add parasitic-aware timing characterization and close timing against SRAM specs. |
| RISK_09 | baseline config remains small (word_size=4, num_words=4) | outputs/openyield_structure_complete_gds/current_supported_config/structure_complete_config.json | Parameterization exists, but implementation evidence is only for a minimal 4x4 baseline. | False | False | False | Re-run R3/R4/R5 on larger configs such as word_size=16 and num_words=32. |
| RISK_10 | multi-bank / multi-port / write mask unsupported | outputs/openyield_layout_intent/current_supported_config/openyield_sram_layout_intent.json | Current generator intent and prototype are scoped to single-bank single-port without write mask. | False | False | False | Extend canonical intent, topology, and routing architecture before expanding feature scope. |
| RISK_11 | OpenYield netlist-to-LVS extraction remains future work | outputs/openyield_final_validation/current_supported_config/final_net_mapping_audit.json | Current mapping is audit evidence, not an extraction-ready LVS flow. | False | True | False | Build a formal extraction handoff from GDS geometry to OpenYield semantic nets. |

