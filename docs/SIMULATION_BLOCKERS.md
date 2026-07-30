# Simulation Blockers

- Level 1 digital logic regression is asset-blocked: current project audit found no authoritative `.v/.sv` files for the requested control modules.
- Level 2 representative SRAM functional simulation remains blocked by lack of a reviewed standalone SRAM functional testbench bound to the current project's authoritative top netlist.
- Post-layout simulation remains NOT_AVAILABLE_WITH_CURRENT_EVIDENCE because current repo lacks refreshed extraction-rule provenance and fresh LVS/PEX binding for a new regression loop.
- `delay_chain` is no longer an unknown smoke failure: root cause is documented in `docs/DELAY_CHAIN_SPICE_FAILURE_ROOT_CAUSE.md` as an expectation/window mismatch on a 9-stage loaded inverter chain.
