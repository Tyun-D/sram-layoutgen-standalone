# M12C3 Generator Architecture Decision

- generator_architecture_decision: `OPENRAM_FREEPDK45_DEVICE_CONTACT_ADAPTER`
- reason: OpenRAM already provides FreePDK45-backed transistor, contact, and inverter generators. The safest next step is a thin adapter that locks naming, source trace, and OpenYield-specific parameter contracts instead of drawing new proxy geometry.
- generator_adapter_required: `True`
- generator_implementation_ready: `False`
