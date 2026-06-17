# OpenYield Read/Write Path Semantic Review

This is a metadata-only semantic review. It does not modify routing, GDS writer, placement, or OpenYield sources.

## Summary

- standalone.py modified in this step: `False`
- new script: `scripts/openyield_read_write_path_semantic_review.py`
- legacy_default preserved: `True`
- read path semantics ok: `True`
- write path semantics ok: `True`
- read/write conflict found: `False`
- grouped mapping needs confirmation: `True`
- can continue to wordline driver: `True`
- generated fake dout_b: `False`
- routing changed: `False`
- GDS writer changed: `False`
- shared rail enabled: `False`

## Cases

| case | gds | senseamp | columnmux | writedriver | storage | storage policy | cmux count | sa count | wd count | storage inst | read ok | write ok | conflict | grouped confirm | gds path |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| legacy_default | True | False | False | False | False | all_r0 | 8 | 4 | 4 | 0 | False | False | False | False | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_read_write_path_semantic_review_legacy_default\sram_4x32_wpr2_fd45.gds |
| read_path_only | True | True | True | False | False | all_r0 | 8 | 4 | 4 | 0 | True | False | False | False | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_read_write_path_semantic_review_read_path_only\sram_4x32_wpr2_fd45.gds |
| write_path_only | True | False | False | True | False | all_r0 | 8 | 4 | 4 | 0 | False | True | False | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_read_write_path_semantic_review_write_path_only\sram_4x32_wpr2_fd45.gds |
| read_write_path | True | True | True | True | False | all_r0 | 8 | 4 | 4 | 0 | True | True | False | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_read_write_path_semantic_review_read_write_path\sram_4x32_wpr2_fd45.gds |
| storage_plus_read_write_path | True | True | True | True | True | alternating_mx | 8 | 4 | 4 | 176 | True | True | False | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_read_write_path_semantic_review_storage_plus_read_write_path\sram_4x32_wpr2_fd45.gds |

## Read Path Mapping

| OpenYield pin | Local pin | Canonical signal |
| --- | --- | --- |
| OUT | mux_out[group] | mux_out |
| OUTB | mux_out_b[group] | mux_out_b |
| IN | mux_out[group] | mux_out |
| INB | mux_out_b[group] | mux_out_b |
| Q | dout[group] | dout |
| QB | - | dropped_complementary_output |

## Write Path Mapping

| OpenYield pin | Local pin | Canonical signal |
| --- | --- | --- |
| DIN | din | din |
| EN | write_enable | write_enable |
| BL | bl | bl |
| BLB | br | br |

## Notes

- QB remains observation-only; do not force dout_b into the local sense_amp path.
- Write driver semantics stay on bl/br and should not be cross-wired to mux_out/mux_out_b.
- Grouped mapping is still metadata-level until layout-level fanout is explicitly proven.
