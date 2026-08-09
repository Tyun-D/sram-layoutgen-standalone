# Generator Parameter Propagation Comparison

Smoke-test root: `/data1/qujh/layoutgen_handoff_evaluation/20260809T050251Z/`

| config | word_size | num_words | WPR | rows | cols | addr_bits | bitcells | dummy | replica | precharge | col_mux | sense | write | WL drv | DFF | delay | bbox | refs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| `sram_16x16_wpr1` | 16 | 16 | 1 | 16 | 16 | 4 | 256 | 32 | 16 | 17 | 16 | 16 | 16 | 16 | 24 | 6 | 25.133 x 54.665 | 527 |
| `sram_32x16_wpr1` | 16 | 32 | 1 | 32 | 16 | 5 | 512 | 64 | 32 | 17 | 16 | 16 | 16 | 32 | 26 | 6 | 25.860 x 78.230 | 865 |
| `sram_32x16_wpr2` | 16 | 32 | 2 | 16 | 32 | 5 | 512 | 32 | 16 | 33 | 32 | 16 | 16 | 16 | 26 | 6 | 36.723 x 48.925 | 818 |

Evidence statement:

- `16x16 WPR1` derives 16 rows x 16 columns, 4 address bits, 256 bitcells, 16 WL drivers, 17 precharge refs, and a 25.132 x 54.665 um bbox.
- `32x16 WPR1` holds cols=16 but doubles rows to 32, increasing bitcells to 512, dummy cells to 64, replica cells to 32, WL drivers to 32, references to 865, and height to 78.230 um.
- `32x16 WPR2` keeps num_words=32 but changes WPR to 2, deriving rows=16 and cols=32, increasing precharge/column mux to 33/32 and widening bbox to 36.723 um.

Conclusion: input parameter changes propagate into derived address geometry, module counts, GDS hierarchy references, and final macro geometry.
