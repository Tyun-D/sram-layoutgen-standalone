# M2R Layoutgen Flow Reuse Matrix

| component | function | reused_for_M2R | role |
| --- | --- | --- | --- |
| scripts/openyield_generate_layout_prototype.py | main | evidence_only | CLI entry for legacy_baseline / hybrid prototype generation. |
| sram_layoutgen/openyield_adapter/layout_prototype.py | generate_layout_prototype | spec_and_flow_evidence | Build guarded prototype config and call the original SRAM macro generator via write_standalone. |
| sram_layoutgen/standalone.py | write_standalone | direct | Original SRAM top-level generation driver: creates GDS, complete.gds, LEF, SPICE, layout JSON, and metrics. |
| sram_layoutgen/standalone.py | build_layout | direct | Deterministic SRAM physical assembly: bitcell/dummy/replica arrays, row path, column path, control region, routing guides, and pin export. |
| sram_layoutgen/gds_writer.py | GDSWriter.write | direct | Write top cell and hierarchy to GDS using layout DB objects from write_standalone/build_layout. |
