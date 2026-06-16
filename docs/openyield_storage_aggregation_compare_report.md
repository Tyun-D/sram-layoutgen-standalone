# OpenYield Storage Aggregation Compare Report

This report compares the legacy storage placement path with the explicitly enabled limited OpenYield storage-array aggregation path. No GDS is generated here; any later GDS from this mode should be treated as smoke output, not final signoff.

## Summary

- cases: `2x16_wpr1, 4x32_wpr2`
- generated GDS: `False`
- routing changed: `False`
- GDS writer changed: `False`
- shared rail merge: `False`
- peripheral aggregation: `False`
- ready for next step: `True`

## Area And Pitch

| case | rows | cols | legacy area | enabled area | delta area | delta % | legacy pitch | enabled pitch |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2x16_wpr1 | 16 | 2 | 770.842762 | 807.350362 | 36.5076 | 4.736063 | 0.705 x 1.365 | 0.895 x 1.565 |
| 4x32_wpr2 | 16 | 8 | 983.296712 | 1079.636212 | 96.3395 | 9.797602 | 0.705 x 1.365 | 0.895 x 1.565 |

## Case Details

### 2x16_wpr1

| mode | total bbox | storage bbox | bitcell bbox | dummy bbox | replica bbox | storage inst | peripheral inst |
| --- | --- | --- | --- | --- | --- | --- | --- |
| legacy | (0.0, 0.0)-(15.2025, 50.705); 15.2025 x 50.705 | (11.2, 22.9175)-(14.915, 44.9575); 3.715 x 22.04 | (11.905, 22.9175)-(13.505, 44.9575); 1.6 x 22.04 | (11.2, 22.9175)-(14.915, 44.9575); 3.715 x 22.04 | (13.315, 22.9175)-(14.21, 44.9575); 0.895 x 22.04 | 80 | 64 |
| openyield_enabled | (0.0, 0.0)-(15.9225, 50.705); 15.9225 x 50.705 | (11.2, 22.9175)-(15.675, 47.9575); 4.475 x 25.04 | (12.095, 22.9175)-(13.885, 47.9575); 1.79 x 25.04 | (11.2, 22.9175)-(15.675, 47.9575); 4.475 x 25.04 | (13.885, 22.9175)-(14.78, 47.9575); 0.895 x 25.04 | 80 | 64 |

Checks:

| check | result |
| --- | --- |
| only_storage_arrays_replaced | True |
| only_allowed_storage_macros | True |
| disallowed_peripheral_macros_in_aggregation_plan | [] |
| no_disallowed_peripheral_macros_in_aggregation_plan | True |
| routing_unchanged | True |
| shared_rail_merge_unchanged | True |
| gds_writer_unchanged | True |
| default_legacy_mirror_path | True |
| enabled_storage_arrays_r0_no_mirror | True |
| enabled_pitch_matches_openyield_audit | True |
| generated_gds | False |
| clean | True |

### 4x32_wpr2

| mode | total bbox | storage bbox | bitcell bbox | dummy bbox | replica bbox | storage inst | peripheral inst |
| --- | --- | --- | --- | --- | --- | --- | --- |
| legacy | (0.0, 0.0)-(19.3925, 50.705); 19.3925 x 50.705 | (11.2, 22.9175)-(19.145, 44.9575); 7.945 x 22.04 | (11.905, 22.9175)-(17.735, 44.9575); 5.83 x 22.04 | (11.2, 22.9175)-(19.145, 44.9575); 7.945 x 22.04 | (17.545, 22.9175)-(18.44, 44.9575); 0.895 x 22.04 | 176 | 87 |
| openyield_enabled | (0.0, 0.0)-(21.2925, 50.705); 21.2925 x 50.705 | (11.2, 22.9175)-(21.045, 47.9575); 9.845 x 25.04 | (12.095, 22.9175)-(19.255, 47.9575); 7.16 x 25.04 | (11.2, 22.9175)-(21.045, 47.9575); 9.845 x 25.04 | (19.255, 22.9175)-(20.15, 47.9575); 0.895 x 25.04 | 176 | 87 |

Checks:

| check | result |
| --- | --- |
| only_storage_arrays_replaced | True |
| only_allowed_storage_macros | True |
| disallowed_peripheral_macros_in_aggregation_plan | [] |
| no_disallowed_peripheral_macros_in_aggregation_plan | True |
| routing_unchanged | True |
| shared_rail_merge_unchanged | True |
| gds_writer_unchanged | True |
| default_legacy_mirror_path | True |
| enabled_storage_arrays_r0_no_mirror | True |
| enabled_pitch_matches_openyield_audit | True |
| generated_gds | False |
| clean | True |

## Legacy Peripheral Path

The enabled path still uses the legacy placement for sense amps, write drivers, tri-gates, column muxes, wordline drivers, precharge, DFF/control logic, and generated control logic. The aggregation plan is restricted to `cell_1rw`, `dummy_cell_1rw`, and `replica_cell_1rw`.

## Next Steps

- Keep OpenYield aggregation behind the explicit enable flag until routing and signoff are evaluated.
- Investigate whether the larger audited bbox pitch is acceptable before moving from storage-only placement to any peripheral aggregation.
- Do not aggregate sense/write/column/wordline/DFF logic until each macro has a verified pin, rail, and semantic contract.
