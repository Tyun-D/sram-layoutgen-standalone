# OpenYield Step 5 Final Hardmacro Smoke Report

This report is a final-step combination smoke only. It is not final DRC/LVS signoff.

## Checks

- legacy_default_preserved: `True`
- storage_only_passed: `True`
- read_path_only_passed: `True`
- write_path_only_passed: `True`
- wordline_only_passed: `True`
- all_hardmacro_opt_in_passed: `True`

## Case Summary

### 2x16_wpr1

| mode | GDS | bbox (W x H) | area | storage | storage policy | senseamp | columnmux | writedriver | wordline | repaired alias | fake dout_b | write mapping | B polarity | read/write conflict | routing changed | GDS writer changed | shared rail |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| legacy_default | True | 15.2025 x 50.7050 | 770.8428 | False | all_r0 | False | False | False | False | False | False | True | None | False | False | False | False |
| storage_only | True | 15.9225 x 50.7050 | 807.3504 | True | alternating_mx | False | False | False | False | False | False | True | None | False | False | False | False |
| read_path_only | True | 15.2025 x 50.7050 | 770.8428 | False | all_r0 | True | True | False | False | True | False | True | None | False | False | False | False |
| write_path_only | True | 15.2025 x 50.7050 | 770.8428 | False | all_r0 | False | False | True | False | False | False | True | None | False | False | False | False |
| wordline_only | True | 15.2025 x 50.7050 | 770.8428 | False | all_r0 | False | False | False | True | False | False | True | high_active | False | False | False | False |
| all_hardmacro_opt_in | True | 15.9225 x 50.7050 | 807.3504 | True | alternating_mx | True | True | True | True | True | False | True | high_active | False | False | False | False |

- legacy_default bbox: `15.2025 x 50.7050` area `770.8428`
- all_hardmacro_opt_in bbox: `15.9225 x 50.7050` area `807.3504`
- area delta: `36.5076`
- area delta percent: `4.736`

### 4x32_wpr2

| mode | GDS | bbox (W x H) | area | storage | storage policy | senseamp | columnmux | writedriver | wordline | repaired alias | fake dout_b | write mapping | B polarity | read/write conflict | routing changed | GDS writer changed | shared rail |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| legacy_default | True | 19.3925 x 50.7050 | 983.2967 | False | all_r0 | False | False | False | False | False | False | True | None | False | False | False | False |
| storage_only | True | 21.2925 x 50.7050 | 1079.6362 | True | alternating_mx | False | False | False | False | False | False | True | None | False | False | False | False |
| read_path_only | True | 19.3925 x 50.7050 | 983.2967 | False | all_r0 | True | True | False | False | True | False | True | None | False | False | False | False |
| write_path_only | True | 19.3925 x 50.7050 | 983.2967 | False | all_r0 | False | False | True | False | False | False | True | None | False | False | False | False |
| wordline_only | True | 19.3925 x 50.7050 | 983.2967 | False | all_r0 | False | False | False | True | False | False | True | high_active | False | False | False | False |
| all_hardmacro_opt_in | True | 21.2925 x 50.7050 | 1079.6362 | True | alternating_mx | True | True | True | True | True | False | True | high_active | False | False | False | False |

- legacy_default bbox: `19.3925 x 50.7050` area `983.2967`
- all_hardmacro_opt_in bbox: `21.2925 x 50.7050` area `1079.6362`
- area delta: `96.3395`
- area delta percent: `9.798`

## Summary

- sense_amp: Q -> dout, QB dropped, no fake dout_b.
- column mux: OUT/OUTB -> mux_out/mux_out_b, using repaired alias gen_col_mux_vdd_labeled.
- write driver: DIN/EN/BL/BLB -> din/write_enable/bl/br.
- wordline driver: A/B/Z -> decoder_input/wordline_enable/wl, B high-active.
- read/write semantic review passed.
- storage alternating_mx is available as an explicit opt-in.
- All adapters remain default-off, so the legacy default path is preserved.

## Remaining

- TIME / DFF / control logic are not yet decomposed into substructure-level adapters.
- Grouped mux/write mapping still needs a layout-level fanout proof.
- Routing is still not OpenYield-driven.
- Shared rail remains disabled.
- Full DRC/LVS/signoff is still incomplete.
- Peripheral placement is opt-in only; routing still follows the old path.

## Next Step

- Step 6.1: TIME / DFF / control logic decomposition audit
