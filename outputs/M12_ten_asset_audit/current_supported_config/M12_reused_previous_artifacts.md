# M12 Reused Previous Artifacts

- `M8R/M8RC locked golden layoutgen flow` path=`outputs/M8R_fix_golden_geometry_delta/current_supported_config/m8r_reproduced_fixed.gds` purpose=`locked exact-match geometry baseline for translator-backed physical delivery`
- `M9/M9H translator v1` path=`outputs/M9_openyield_netlist_translator/current_supported_config/openyield_netlist_translated_sram.gds` purpose=`prior translator semantics, binding bridge, and reviewed translator framing`
- `M10 raw source-backed trace` path=`outputs/M10_raw_openyield_trace/current_supported_config/openyield_source_backed_translated_sram.gds` purpose=`source-backed module/net/instance/config trace and exact-match source-backed translator v2 evidence`
- `T1 OpenYield full file analysis` path=`docs/T1_openyield_full_file_report.json` purpose=`key entrypoints, source inventory, and recommended raw-source search set`
- `R1/M1 OpenYield intent and binding` path=`outputs/openyield_layout_intent/current_supported_config/;docs/mapping/M1_openyield_to_layoutgen_binding.csv;docs/mapping/M1_openyield_net_to_layoutgen_pin_binding.csv` purpose=`semantic role map and module/net binding inputs carried into M9 and hardened in M10`
- `M7 golden reference` path=`outputs/M7_correct_golden_reference/current_supported_config/golden_reference.gds` purpose=`locked physical comparison target and exact-match baseline`
