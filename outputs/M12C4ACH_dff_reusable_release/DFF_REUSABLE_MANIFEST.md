# DFF Reusable Manifest

- reusable_status: `HUMAN_REVIEWED_REUSABLE_COMPOSITE`
- logical_module: `DFF`
- physical_cell_name: `DFF_TG4_INV7_FPDK45_26d9543b82b7`
- released_clean_gds_path: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M12C4ACH_dff_reusable_release/DFF_reusable_clean.gds`
- source_clean_gds_path: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M12C4AC_dff_connectivity_repair/current_supported_config/M12C4AC_dff_clean.gds`
- source_topology_hash: `26d9543b82b7`
- binding_hash_sha256: `66b6580cebf9292b9c8457e7843925aa1212cbb62a53214b484f7d957e20f108`
- geometry_hash: `8668df83d4b7e5d14ee35a01`
- source_commit_openyield: `1c34428d8b913963c4971d093b1a7c2df97a2509`
- source_commit_sram_layoutgen_release_base: `25101b4436d1fb3f9f9577646085971fc33820c6`

## Composition Policy

- `only_clean_gds_is_composition_source = true`
- `annotated GDS` and `review atlas` are review-only and must not be composed.
- Failed M12C4A DFF remains quarantined and must not be reused.
- Primitive dependency remains locked to approved `PINV_NW250_PW500_L50` and `TRANSMISSION_GATE_NW250_PW500_L50`.

## Release Checks

- `released_gds_hash`: `f6995536077a191c31e10644bbfcfb4075cda64b7da131987c70a59353c4e45d`
- `source_clean_gds_hash`: `f6995536077a191c31e10644bbfcfb4075cda64b7da131987c70a59353c4e45d`
- `release_hash_matches_M12C4AC_clean`: `True`
- `hierarchy_closure_passed`: `True`
- `top_level_cell_count`: `1`
- `top_level_cell_name`: `DFF_TG4_INV7_FPDK45_26d9543b82b7`
- `missing_reference_target_count`: `0`
- `reference_cycle_count`: `0`
- `top_canonical_label_set_exact`: `True`
- `top_canonical_label_count`: `5`
- `drc_marker_count`: `0`
- `drc_passed`: `True`
- `expected_net_count`: `13`
- `actual_net_component_count`: `13`
- `unexpected_net_merge_count`: `0`
- `missing_expected_endpoint_count`: `0`
- `unexpected_endpoint_count`: `0`
- `connectivity_recheck_passed`: `True`
- `deterministic_release_verified`: `True`
- `failed_attempt_remains_quarantined`: `True`
- `annotated_not_reusable_source`: `True`
- `atlas_not_reusable_source`: `True`
