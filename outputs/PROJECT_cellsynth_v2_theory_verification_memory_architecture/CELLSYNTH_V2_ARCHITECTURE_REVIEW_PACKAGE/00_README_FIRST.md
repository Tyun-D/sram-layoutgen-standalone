# CellSynth v2 Architecture Review Package

Status: `PASS_OPENYIELD_CELLSYNTH_V2_THEORY_VERIFICATION_MEMORY_ARCHITECTURE`

This package is intentionally architecture-first. It does not contain a new optimized DFF GDS. The current 9.1017 um^2 DFF is audited as DRC-clean but not LVS-closed.

Review order:
1. `01_PROJECT_MEMORY/`
2. `02_LITERATURE/`
3. `03_GOLDEN_ELECTRICAL_SPEC/`
4. `04_CURRENT_LAYOUT_VERIFICATION/`
5. `05_TECHNOLOGY_RULE_AUDIT/`
6. `06_SYMBOLIC_MODEL/` through `10_IMPLEMENTATION_PLAN/`
