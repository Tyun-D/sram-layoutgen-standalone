# OpenYield Step 5 Hardmacro Adapter Summary

## Completed

- sense_amp: Q -> dout, QB dropped, no fake dout_b.
- column mux: OUT/OUTB -> mux_out/mux_out_b, using repaired alias gen_col_mux_vdd_labeled.
- write driver: DIN/EN/BL/BLB -> din/write_enable/bl/br.
- wordline driver: A/B/Z -> decoder_input/wordline_enable/wl, B high-active.
- read/write semantic review passed.
- storage alternating_mx is available as an explicit opt-in.
- All adapters remain default-off, so the legacy default path is preserved.

## Still Unresolved

- TIME / DFF / control logic are not yet decomposed into substructure-level adapters.
- Grouped mux/write mapping still needs a layout-level fanout proof.
- Routing is still not OpenYield-driven.
- Shared rail remains disabled.
- Full DRC/LVS/signoff is still incomplete.
- Peripheral placement is opt-in only; routing still follows the old path.

## Recommendation

- Step 6.1: TIME / DFF / control logic decomposition audit

## Case Notes

### 2x16_wpr1
- legacy bbox: `{'width_um': 15.202499999999999, 'height_um': 50.705, 'area_um2': 770.8427624999999}`
- all_hardmacro bbox: `{'width_um': 15.922499999999975, 'height_um': 50.705, 'area_um2': 807.3503624999987}`
- area delta um2: `36.5076`
- area delta percent: `4.736`

### 4x32_wpr2
- legacy bbox: `{'width_um': 19.392499999999995, 'height_um': 50.705, 'area_um2': 983.2967124999997}`
- all_hardmacro bbox: `{'width_um': 21.292499999999976, 'height_um': 50.705, 'area_um2': 1079.6362124999987}`
- area delta um2: `96.3395`
- area delta percent: `9.798`
