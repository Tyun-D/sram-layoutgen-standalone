# Decoder Child Pin Authority Audit

## Conclusion

- Current decoder child assets are sufficient for executable candidate rebuilds, but not for bit-exact production handoff.
- Every bus handoff remains wildcard-only in the locked child manifests.
- Every audited child top cell has `gds_top_label_count = 0`.
- Each child generation report explicitly says `L3_GDS_GENERATED_CANDIDATE_GEOMETRY` and `not_DRC_clean_claimed = true`.

## Blocking Detail

- `A[*]`, `dec_out[*]`, `DEC_WL[*]`, and `dec_stage[*]` remain `AMBIGUOUS_REQUIRES_NEW_ASSET_CONTRACT`.
- The present `pins.json` files are semantic/contract exports (`pin_source = composition_contract_and_base_leaf_pin_map`) rather than extracted native GDS pin labels.
- Under the current project rules, these wildcard exports cannot be upgraded to formal bit-exact decoder authority without a new child pin contract bound to exact physical shapes.

## Module Summary

- `decoder_gate_cells`: `gds_top_label_count=0`, `generation_status=L3_GDS_GENERATED_CANDIDATE_GEOMETRY`, `not_drc_clean_claimed=True`
- `row_decoder`: `gds_top_label_count=0`, `generation_status=L3_GDS_GENERATED_CANDIDATE_GEOMETRY`, `not_drc_clean_claimed=True`
- `wordline_decoder`: `gds_top_label_count=0`, `generation_status=L3_GDS_GENERATED_CANDIDATE_GEOMETRY`, `not_drc_clean_claimed=True`
