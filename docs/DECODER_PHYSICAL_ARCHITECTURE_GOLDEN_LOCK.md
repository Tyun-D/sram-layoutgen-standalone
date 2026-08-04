# Decoder physical architecture golden lock

P2 is the provisional preferred architecture and P3 is the retained alternative. Their GDS and evidence SHA256 values are frozen in `DECODER_PHYSICAL_ARCHITECTURE_GOLDEN_LOCK.json` at build-source HEAD `5dc3f712a2fedf79c5f2f14192201bc58bb82104`.

All local WL timing-closure work must be emitted under `outputs/PROJECT_decoder_physical_timing_closure/`. Existing P2/P3 files must not be regenerated or overwritten.

Both locked integrations use an approved nonzero physical array shell. They are floorplan-feasibility evidence, not full bitcell-array GDS integration and not formal timing closure.
