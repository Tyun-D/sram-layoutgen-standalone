# OpenYield WORDLINEDRIVER Placement Smoke Report

This is a limited placement plan smoke. It does not modify standalone.py, routing, or the GDS writer.

## Summary

- rows: `4`
- origin: `(0.0, 0.0)`
- pitch_y: `1.565`
- macro name: `gen_wl_driver`
- row orientation policy: `all_r0`
- power status: `vdd_gnd_metadata_present`
- can enter limited placement: `True`
- standalone modified: `False`
- routing changed: `False`
- GDS writer changed: `False`
- wordline_driver changed: `False`

## Placements

| instance | row | x | y | orientation | a | b | z |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Xwld_r0 | 0 | 0.0 | 0.0 | R0 | decoder_input[0] | wordline_enable | wl[0] |
| Xwld_r1 | 1 | 0.0 | 1.565 | R0 | decoder_input[1] | wordline_enable | wl[1] |
| Xwld_r2 | 2 | 0.0 | 3.13 | R0 | decoder_input[2] | wordline_enable | wl[2] |
| Xwld_r3 | 3 | 0.0 | 4.695 | R0 | decoder_input[3] | wordline_enable | wl[3] |

## Notes

- Adapter-only placement metadata; this does not emit GDS or modify the main flow.
- One wordline driver is planned per row.
- B is treated as active-high based on the NAND2+INV OpenYield source chain.
- Shared rail is intentionally left disabled in this step.
- This smoke is metadata-only and does not emit GDS.
- The physical wordline-driver flow is intentionally left untouched.
