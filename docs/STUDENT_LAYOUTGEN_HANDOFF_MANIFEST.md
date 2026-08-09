# Student Layoutgen Handoff Manifest

Audit timestamp: 2026-08-09T05:02:51Z

Readiness classification:

`LEGACY_FULL_MACRO_GENERATOR_PRESERVED_HANDOFF_PACKAGING_REQUIRED`

Rationale:

- Current entrypoint exists and ran.
- Three legal parameter configurations regenerated successfully.
- Generated GDS/LEF/SPICE/layout JSON/report JSON/report Markdown and auxiliary GDS/SVG outputs.
- SRAM modules are present in generated GDS/layout JSON.
- Parameter changes propagate to rows, cols, address bits, instance counts, references, and bbox.
- The code and hardmacro dependencies are identifiable and packageable.
- A polished student handoff still needs a clean README, requirements file, example configs, one-command script, and removal/annotation of server-specific historical paths.

Recommended student release shape:

```text
sram-layoutgen-student/
├── README.md
├── requirements.txt
├── configs/
├── sram_layoutgen/
├── technology/
├── hardmacros/
├── scripts/
├── examples/
└── validation/
```

Mandatory handoff files:

1. Generator source
   - `sram_layoutgen/__init__.py`
   - `sram_layoutgen/__main__.py`
   - `sram_layoutgen/standalone.py`
   - `sram_layoutgen/geometry.py`
   - `sram_layoutgen/gds_writer.py`
   - `sram_layoutgen/gds_util.py`
   - `sram_layoutgen/lef_writer.py`
   - `sram_layoutgen/netlist_writer.py`
   - `sram_layoutgen/tech.py`
   - `sram_layoutgen/stdcell.py`
   - `sram_layoutgen/openram_placement.py`
   - `sram_layoutgen/occupancy.py`
   - `sram_layoutgen/verifier.py`
   - the imported helper subset under `sram_layoutgen/openyield_adapter/` needed by `standalone.py`

2. Hardmacro GDS
   - `technology/freepdk45/gds_lib/cell_1rw.gds`
   - `technology/freepdk45/gds_lib/dummy_cell_1rw.gds`
   - `technology/freepdk45/gds_lib/replica_cell_1rw.gds`
   - `technology/freepdk45/gds_lib/dff.gds`
   - `technology/freepdk45/gds_lib/sense_amp.gds`
   - `technology/freepdk45/gds_lib/write_driver.gds`
   - `technology/freepdk45/gds_lib/tri_gate.gds`
   - `technology/freepdk45/gds_lib/openram_replacements/*.gds`
   - `technology/freepdk45/gds_lib/openyield_repaired/*.gds` if repaired column-mux alias remains in metadata

3. PDK/layer map
   - `technology/freepdk45/layers.map`
   - `technology/freepdk45/replacement_macros.json`
   - `technology/freepdk45/openyield_repaired_macro_aliases.json`

4. SPICE files
   - `technology/freepdk45/sp_lib/*.sp`

5. Config examples
   - `configs/sram_16x16_wpr1.json`
   - `configs/sram_32x16_wpr1.json`
   - `configs/sram_32x16_wpr2.json`

6. One-command script
   - `scripts/generate_example.sh`

7. Documentation
   - README with parameter contract, output inventory, known limitations, and path assumptions.
   - This audit set: `STUDENT_HANDOFF_GENERATOR_SOURCE_AUDIT.*`, `STUDENT_HANDOFF_PARAMETER_CONTRACT.*`, `STUDENT_HANDOFF_DEPENDENCY_AUDIT.*`.

Optional handoff files:

- `technology/freepdk45/tech/freepdk45.lydrc`, `.lylvs`, `.lyt`, `.lyp`
- `sram_layoutgen/signoff.py`
- KLayout viewing/check scripts
- OpenRAM reference source/configs for comparison only
- Selected OpenYield validation modules if the student will inspect newer validation methodology

One-command flow assessment:

- Current true command:

```bash
python -m sram_layoutgen \
  --word-size 16 \
  --num-words 16 \
  --words-per-row 1 \
  --out outputs/sram_16x16
```

- JSON config is supported by current CLI.
- `STUDENT_ONE_COMMAND_FLOW_READY=false` for a polished external handoff because repo-level `configs/`, `requirements.txt`, `scripts/generate_example.sh`, and README are not yet created.
- Minimal packaging work is small and non-algorithmic.

Do not include as mandatory for this legacy handoff:

- authoritative array regeneration outputs
- P2/P3 physical architecture work
- current full-top reconstruction work
- external OpenYield source tree, unless the student is explicitly assigned to the new OpenYield path
