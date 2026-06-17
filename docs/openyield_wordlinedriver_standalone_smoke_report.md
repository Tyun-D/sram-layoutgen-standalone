# OpenYield Wordline Driver Standalone Smoke Report

- case: `4x32_wpr2`
- standalone modified: `True`
- new parameter: `enable_openyield_wordlinedriver_adapter` default `False`
- all modes generated GDS: `True`
- legacy_default kept legacy path: `True`
- wordlinedriver_only enabled: `True`
- data_path_plus_wordlinedriver enabled: `True`
- storage_plus_data_path_plus_wordlinedriver enabled: `True`
- storage_plus_data_path_plus_wordlinedriver uses alternating_mx: `True`
- wordline_driver_pin_labels_verified: `True`
- wordline_driver_pin_report_consistent: `True`
- routing changed: `False`
- GDS writer changed: `False`
- shared rail enabled: `False`
- wordline driver instance count: `16`
- next step recommendation: `proceed_to_step5_peripheral_integration_review`

## Mode Summary

| mode | GDS | bbox (W x H) | area | wordline_driver count | local macro | safe phys | safe shared | pin report | enabled | routing changed | GDS writer changed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| legacy_default | True | 19.3925 x 50.7050 | 983.2967 | 16 | gen_wl_driver | False | False | False | False | False | False |
| wordlinedriver_only | True | 19.3925 x 50.7050 | 983.2967 | 16 | gen_wl_driver | True | False | True | True | False | False |
| data_path_plus_wordlinedriver | True | 19.3925 x 50.7050 | 983.2967 | 16 | gen_wl_driver | True | False | True | True | False | False |
| storage_plus_data_path_plus_wordlinedriver | True | 21.2925 x 50.7050 | 1079.6362 | 16 | gen_wl_driver | True | False | True | True | False | False |

## Checks

- default_legacy_path_preserved: `True`
- wordlinedriver_only_ok: `True`
- data_path_plus_wordlinedriver_ok: `True`
- storage_plus_data_path_plus_wordlinedriver_ok: `True`
- routing_unchanged: `True`
- gds_writer_unchanged: `True`
- shared_rail_disabled: `True`
- decoder_unchanged: `True`
- time_control_unchanged: `True`
