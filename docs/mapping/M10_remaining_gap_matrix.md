# M10 Remaining Gap Matrix

- `M10_GAP_001` BLOCKER: Human KLayout review is required for openyield_source_backed_translated_sram_clean_review.gds before any post-M10 stage.
- `M10_GAP_002` NON_BLOCKING_SCOPE_LIMIT: M10 is a source-backed translator v2 but still not a full raw OpenYield netlist compiler.
- `M10_GAP_003` NON_BLOCKING_SCOPE_LIMIT: OpenYield raw source did not provide sufficient capacity/config values; locked golden 8x64_wpr4 layoutgen configuration was used while binding OpenYield source-backed module/net semantics.
