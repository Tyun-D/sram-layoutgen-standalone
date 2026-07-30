# Decoder V2 Leaf Source Inventory

- git_head: `e411f6209f5b7a32b9514777e4c7ae37d08103ce`
- exact_clean_gate_count: `2`
- exact_primitive_count: `2`
- all_recorded_sources_drc_zero: `True`

## Assets

- `PINV_NW90_PW270_L50`
  source_authority: `current_project_reusable_primitive`
  role: `exact_primitive`
  gds_sha256: `68f75773e2869548ab559556d5eee2764f836a41ccd2bceb29bc3633360891a2`
  drc_marker_count: `0`
  contract_pin_names: `['A', 'VDD', 'VSS', 'Z']`
- `AND2_PNAND2_PINV_FPDK45`
  source_authority: `primary_repo_formal_team_b_output`
  role: `exact_clean_gate`
  gds_sha256: `291f40e81761c49a60bc5b36e864e160cea5114b5bf27e284a97cac4d019a44c`
  drc_marker_count: `0`
  contract_pin_names: `['VDD', 'VSS', 'A', 'B', 'Z']`
- `AND3_PNAND3_PINV_FPDK45`
  source_authority: `primary_repo_formal_team_b_output`
  role: `exact_clean_gate`
  gds_sha256: `015527cdb1aff01736bd81d1ac401dc6fda000aa2e4305f6872bb92a204aa3cf`
  drc_marker_count: `0`
  contract_pin_names: `['VDD', 'VSS', 'A', 'B', 'C', 'Z']`
- `WORDLINEDRIVER_gen_wl_driver`
  source_authority: `current_project_generated_primitive`
  role: `exact_generated_primitive`
  gds_sha256: `1988fb54b0843d12d556f17616b43254c1adaf3ba6c5ed88a56ccdb8e41945c5`
  drc_marker_count: `0`
  contract_pin_names: `['A', 'B', 'Z', 'gnd', 'vdd']`

## Primitive Rechecks

- `gen_inv`: `marker_count=0` `exists=True`
- `gen_nand2`: `marker_count=0` `exists=True`
- `gen_wl_driver`: `marker_count=0` `exists=True`
