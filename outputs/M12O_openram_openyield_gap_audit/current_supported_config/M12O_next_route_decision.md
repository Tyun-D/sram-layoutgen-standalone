# M12O Next Route Decision

- recommended_next_stage: `M12N_LOCK_OPENYIELD_AUTHORITATIVE_NETLIST`
- recommended_next_stage_reason: `M12O finds a usable OpenRAM full-reference GDS and a rich OpenYield parameter/config codebase, but it does not prove a single authoritative OpenYield complete SRAM top netlist. Locking that authority is a harder blocker than directly continuing M11V2 connectivity deepening, because control-logic alignment, parameterized SRAM planning, and later combined substitution all still depend on one unambiguous netlist source of truth.`
