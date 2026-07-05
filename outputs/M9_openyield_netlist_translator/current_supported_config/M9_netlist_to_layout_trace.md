# M9 Netlist To Layout Trace

- OpenYield source / intent:
  `docs/mapping/M1_openyield_to_layoutgen_binding.csv`,
  `docs/mapping/M1_openyield_net_to_layoutgen_pin_binding.csv`,
  `docs/mapping/M4E_openyield_to_layoutgen_implementation_binding.csv`,
  `outputs/openyield_layout_intent/current_supported_config`
- parsed modules: `20`
- parsed nets: `34`
- derived SRAM spec:
  `outputs/M9_openyield_netlist_translator/current_supported_config/M9_SRAM_SPEC.json`
- layoutgen generator arguments:
  `sram_layoutgen.standalone.write_standalone` with locked golden-flow-compatible arguments from `M9_SRAM_SPEC.json`
- generated GDS:
  `outputs/M9_openyield_netlist_translator/current_supported_config/openyield_netlist_translated_sram.gds`
- clean review GDS:
  `outputs/M9_openyield_netlist_translator/current_supported_config/openyield_netlist_translated_sram_clean_review.gds`
- annotated debug GDS:
  `outputs/M9_openyield_netlist_translator/current_supported_config/openyield_netlist_translated_sram_annotated_debug.gds`
- module/net binding evidence:
  `outputs/M9_openyield_netlist_translator/current_supported_config/M9_module_binding_matrix.csv`,
  `outputs/M9_openyield_netlist_translator/current_supported_config/M9_net_binding_matrix.csv`,
  `outputs/M9_openyield_netlist_translator/current_supported_config/M9_placement_routing_power_intent.json`
