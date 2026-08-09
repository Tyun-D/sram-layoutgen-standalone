# Legacy Layoutgen Capability Baseline

Audit timestamp: 2026-08-09T05:02:51Z

Evidence sources read:

- `docs/PROJECT_TASK_MASTER_LOG.md`
- `docs/PROJECT_CURRENT_STATUS.json`
- `docs/LAYOUTGEN_EXISTING_ACHIEVEMENT_AUDIT.json`
- `docs/LAYOUTGEN_PHYSICAL_REUSE_CONTRACT.json`
- `/data1/qujh/PAPER_EVIDENCE_PACKAGE_20260713_043712.tar.gz`

Historical baseline confirmed:

- GDS: `PAPER_LAYOUTGEN_EVIDENCE_STAGING_20260713_041505/gds/legacy_baseline.gds`
- SHA256: `80d2a37a1bc36692fde44e46cdcfcc3478b7ccdbdbd622dc1630a07de6d3eae0`
- Historical top cell: `legacy_baseline`
- Historical structure count: 33
- Historical reference count: 788
- Historical hierarchy depth: 5

Historical capability boundary:

- This is not the raw OpenRAM compiler path. OpenRAM control logic, characterization and signoff remain OpenRAM framework capabilities.
- The legacy/simplified path was `sram_layoutgen` with `StandaloneSpec`, `build_layout`, and `write_standalone`.
- The path parameterized `num_words`, `word_size`, and `words_per_row`, then derived rows, cols, address bits, row address bits, and column address bits.
- The historical macro composition included storage array replication, dummy/replica cells, precharge, column mux, sense amp, write driver, tri-gate, wordline drivers, DFF rows, inverter/NAND glue, delay-chain/control glue, macro-level routing, VDD/VSS stitching, WL/BL/BR connectivity, and top pins.

Historical module baseline:

| historical role | evidence status |
|---|---|
| bitcell | implemented via bundled hardmacro `cell_1rw.gds` |
| dummy | implemented/partial via `dummy_cell_1rw.gds` and edge placement |
| replica | implemented via `replica_cell_1rw.gds` |
| precharge | implemented via `gen_precharge` |
| column mux | implemented/partial via `gen_col_mux` |
| sense amplifier | implemented via `sense_amp` |
| write driver | implemented via `write_driver` |
| tri-gate | implemented via `tri_gate` |
| wordline driver | implemented via `gen_wl_driver` |
| DFF/control rows | partial via `dff` rows in top layout |
| INV/NAND glue | implemented via generated/replacement `gen_inv`, `gen_nand2` |
| delay-chain glue | implemented via `gen_delay_inv` |
| standalone top SRAM | implemented by `sram_layoutgen/standalone.py` |

Historical output baseline:

- Main GDS
- LEF
- Structural `.sp`
- Layout JSON
- Report JSON
- Report Markdown
- Debug/presentation/complete/integration/architecture/route-guide GDS in later versions
- Architecture/occupancy SVG in later versions

Important limitation:

- The simplified standalone generator did not preserve a dedicated complete OpenRAM `control_logic` class. Address/control DFF rows, gate-row glue, delay-chain placement, and several control network templates were retained at top level.
