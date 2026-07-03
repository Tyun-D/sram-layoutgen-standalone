# M2R Layoutgen Top Flow Trace

- original_layoutgen_complete_sram_entry_script: `scripts/openyield_generate_layout_prototype.py`
- original_layoutgen_top_generator_function: `sram_layoutgen.standalone.write_standalone`
- layoutgen_top_flow_used: `True`
- arbitrary_module_scatter_used: `False`

| step | component | function | role | reused_for_M2R |
| --- | --- | --- | --- | --- |
| 1 | scripts/openyield_generate_layout_prototype.py | main | CLI entry for legacy_baseline / hybrid prototype generation. | evidence_only |
| 2 | sram_layoutgen/openyield_adapter/layout_prototype.py | generate_layout_prototype | Build guarded prototype config and call the original SRAM macro generator via write_standalone. | spec_and_flow_evidence |
| 3 | sram_layoutgen/standalone.py | write_standalone | Original SRAM top-level generation driver: creates GDS, complete.gds, LEF, SPICE, layout JSON, and metrics. | direct |
| 4 | sram_layoutgen/standalone.py | build_layout | Deterministic SRAM physical assembly: bitcell/dummy/replica arrays, row path, column path, control region, routing guides, and pin export. | direct |
| 5 | sram_layoutgen/gds_writer.py | GDSWriter.write | Write top cell and hierarchy to GDS using layout DB objects from write_standalone/build_layout. | direct |
