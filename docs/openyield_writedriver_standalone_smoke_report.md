# OpenYield WriteDriver Standalone Smoke Report

- case: `4x32_wpr2`
- standalone modified: `True`
- new parameter: `enable_openyield_writedriver_adapter` default `False`
- all modes generated GDS: `True`
- legacy_default kept legacy path: `True`
- writedriver_only enabled: `True`
- read_path_plus_writedriver enabled: `True`
- storage_plus_read_write_path uses alternating_mx: `True`
- routing changed: `False`
- GDS writer changed: `False`
- shared rail enabled: `False`
- write_driver mapping ok: `True`
- next step recommendation: `proceed_to_write_driver_read_write_path_review`

## Mode Summary

| mode | GDS | bbox (W x H) | area | write_driver count | local macro | safe phys | safe shared | mapping ok | senseamp | columnmux | storage enabled | storage policy | routing changed | GDS writer changed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| legacy_default | True | 19.3925 x 50.7050 | 983.2967 | 4 | write_driver | False | False | True | False | False | False | all_r0 | False | False |
| writedriver_only | True | 19.3925 x 50.7050 | 983.2967 | 4 | write_driver | True | False | True | False | False | False | all_r0 | False | False |
| read_path_plus_writedriver | True | 19.3925 x 50.7050 | 983.2967 | 4 | write_driver | True | False | True | True | True | False | all_r0 | False | False |
| storage_plus_read_write_path | True | 21.2925 x 50.7050 | 1079.6362 | 4 | write_driver | True | False | True | True | True | True | alternating_mx | False | False |

## Storage Modes

- `storage_plus_read_write_path`: enabled=`True`, policy=`alternating_mx`, cross_row_power_short_risk=`False`
