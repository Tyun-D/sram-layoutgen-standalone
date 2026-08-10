# V4.1 Same-PDK Cell Geometry Audit

- source GDS: `outputs/PROJECT_full_single_bank_sram/FULL_SRAM_DFF_AUTHORITY_AND_COLUMN_INTERFACE_ALIGNMENT_V41/clean_unique_top.gds`
- source GDS SHA256: `5f48d1de1ab31091a7ded24e3721b9c4afbbfd3e8ad75fff6a351a08539fda6f`
- actual top: `FULL_SRAM_DFF_AUTHORITY_AND_COLUMN_INTERFACE_ALIGNMENT_V41`
- PDK changed: `False`
- external standard-cell library used in final candidates: `False`

## Extracted Geometry
- array BL pitch: `0.705 um`
- array row pitch: `1.565 um`
- WL driver bbox: `2.16 x 1.8875 um`
- WL driver one-driver-per-row feasible now: `False`
- DFF_TG4 bbox: `13.745 x 4.2525 um`
- DFF_BUF bbox: `18.315 x 5.51 um`

## Conclusions
- Current WL driver remains a two-column/staggered integration structure; current unit height exceeds authoritative array row pitch.
- Precharge/sense/write even-odd V2 banks are retained as real same-PDK assets; deinterleaving is not authorized unless exact-topology cell dimensions close pitch gates.
- DFF_TG4_INV7 remains source-bound for ADDR/DATA; bundled FreePDK45 dff is not authorized by this exploration.
- LCLayout is recorded only as an isolated same-PDK algorithm path; it produced no formal candidate in this environment.
