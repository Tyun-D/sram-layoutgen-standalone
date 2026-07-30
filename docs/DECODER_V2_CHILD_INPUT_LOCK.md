# Decoder V2 Child Input Lock

- git_head: `ddadb176e2faf31bf344fa3368ff753ce9af4e81`
- logical_contract_path: `/tmp/qujh_delay_chain_scratch/storage_relief_20260725/worktrees/project_mainline_inventory_20260726/docs/DECODER_V2_LOGICAL_CONTRACT.json`
- leaf_source_inventory_path: `/tmp/qujh_delay_chain_scratch/storage_relief_20260725/worktrees/project_mainline_inventory_20260726/docs/DECODER_V2_LEAF_SOURCE_INVENTORY.json`

## Child Targets

- `decoder_gate_cells_v2` role=`predecode_plus_enable_leaf_group`
  exported_ports=`['A0', 'A1', 'A2', 'EN', 'WL0_pre', 'WL1_pre', 'WL2_pre', 'WL3_pre', 'WL4_pre', 'WL5_pre', 'WL6_pre', 'WL7_pre', 'WL0', 'WL1', 'WL2', 'WL3', 'WL4', 'WL5', 'WL6', 'WL7', 'VDD', 'VSS']`
  row_templates=`[['inv', 'nand3_metadata_only', 'and2', 'and3'], ['decoder_leaf_gate_v2', 'and2', 'inv']]`
  required_exact_leaf_sources=`['and2', 'and3', 'inv']`
- `row_decoder_v2` role=`cascade_stage_decoder`
  exported_ports=`['A0', 'A1', 'A2', 'EN', 'WL0', 'WL1', 'WL2', 'WL3', 'WL4', 'WL5', 'WL6', 'WL7', 'VDD', 'VSS']`
  row_templates=`[['inv', 'nand3_metadata_only', 'and3'], ['decoder_leaf_gate_v2', 'inv', 'nand3_metadata_only']]`
  required_exact_leaf_sources=`['and3', 'inv']`
- `wordline_decoder_v2` role=`row_decoder_to_wordline_handoff`
  exported_ports=`['A0', 'A1', 'A2', 'EN', 'DEC_WL0', 'DEC_WL1', 'DEC_WL2', 'DEC_WL3', 'DEC_WL4', 'DEC_WL5', 'DEC_WL6', 'DEC_WL7', 'VDD', 'VSS']`
  row_templates=`[['inv', 'nand3_metadata_only', 'and3'], ['wordline_decoder_leaf_gate_v2', 'inv', 'and3']]`
  required_exact_leaf_sources=`['and3', 'inv', 'wordline_driver']`

## Notes

- This lock upgrades decoder v2 child generation inputs from wildcard candidate assets to exact leaf source references.
- nand3 remains metadata-only at this stage and must not be promoted to formal child output without regenerated geometry or exact clean gate substitution.
- wordline_decoder_v2 still depends on exact wordline-driver semantics and A/B/Z polarity from OpenYield WORDLINEDRIVER.
