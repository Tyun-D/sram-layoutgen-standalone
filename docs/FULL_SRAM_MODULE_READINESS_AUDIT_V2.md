# Full SRAM Module Readiness Audit V2

- status: `BLOCKED_BY_CONTROL_BLOCK_PHYSICAL_AUTHORITY`
- physical_top_entry_allowed: `False`
- column_mux: `NOT_INSTANTIATED_BY_CONFIG` for 16x16 words_per_row=1
- control_logic: hierarchical TIME/control composition, not a required monolithic macro

| module | classification | required by current netlist | top ready | blocker |
|---|---|---:|---:|---|
| `pdrive` | `RECOVERED_VERIFIED_EXISTING_ASSET` | `True` | `True` | - |
| `wl_pdrive` | `RECOVERED_VERIFIED_EXISTING_ASSET` | `True` | `True` | - |
| `pdrive2_for_pre` | `RECOVERED_VERIFIED_EXISTING_ASSET` | `True` | `True` | - |
| `delay_chain` | `RECOVERED_VERIFIED_EXISTING_ASSET` | `True` | `True` | - |
| `precharge` | `READY_FOR_TOP` | `True` | `True` | - |
| `sense_amplifier` | `READY_FOR_TOP` | `True` | `True` | - |
| `write_driver` | `READY_FOR_TOP` | `True` | `True` | - |
| `column_mux` | `NOT_INSTANTIATED_BY_CONFIG` | `False` | `True` | - |
| `CONTROL_BLOCK_HIERARCHICAL_V1` | `AUTHORITY_PENDING` | `True` | `False` | CONTROL_BLOCK_HIERARCHICAL_V1_PARENT_GDS_NOT_GENERATED; CONTROL_BLOCK_PLACEMENT_ROUTING_POWER_GATE_NOT_CLOSED |
