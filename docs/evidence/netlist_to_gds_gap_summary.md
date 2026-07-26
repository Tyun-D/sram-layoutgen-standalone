# OpenYield Netlist-to-GDS Gap Summary

- readiness matrix available: `True`
- rows covered: `25`
- current GDS-generatable modules: `bitcell_array, dummy_array, replica_array, sense_amp, write_driver, column_mux, wordline_driver`
- metadata-only modules: `DELAY_CHAIN`
- candidate-contract-only modules: `PRECHARGE, PRECHARGE_ENABLE_PATH, SENSE_ENABLE_PATH, WRITE_ENABLE_PATH, WORDLINE_ENABLE_PATH, GATED_CLOCK_PATH, DFF_ROW`
- can claim full OpenYield GDS now: `False`

## Largest blockers

- TIME/DFF/control logic are not physical-ready: Start with decoder/gate-row abutment plus DFF/control-row placement contract closure before any full control replacement claim.
- DELAY_CHAIN lacks proven physical integration: Implement delay-chain physical gap closure after decoder row work.
- PRECHARGE has source-linked smoke evidence but no OpenYield physical integration: Do precharge physical representation / placement hook after DELAY_CHAIN.
- Enable paths and gated clock remain candidate-contract only: Physical mapping for enable-path control logic.
- Decoder and gate rows are not signoff-ready: Decoder/gate row abutment and rail stitching audit.

## Recommended order

- P1 `decoder_gate_cells`: Guarded decoder/gate-row abutment with clearer rail continuity and reduced ambiguity for downstream control placement.
- P2 `DELAY_CHAIN`: DELAY_CHAIN transitions from metadata-only to placement-hook-ready without changing legacy default mode.
- P3 `PRECHARGE`: PRECHARGE moves from candidate/spice-only into guarded physical placement readiness.
