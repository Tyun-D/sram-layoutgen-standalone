# L2 Placement / Abutment Rule Gap Summary

## Scope

This pass closes L2 as a rule-library stage, not a geometry-export stage. The output is a frozen contract set for placement, abutment, rail, orientation, pin access, and module handoff so that L3 can generate standalone module GDS without reopening semantic or primitive-source questions.

## L1 Issues Closed By L2

1. Composition-backed leaves now have explicit row packing, abutment, orientation, rail, and pin-export contracts.
2. Decoder/control/enable/gated-clock gate rows now share one frozen gate-row policy instead of per-audit ad hoc assumptions.
3. `precharge_cell` no longer blocks on vague pin metadata: the L2 pin-access rule freezes GDS-label extraction plus the existing no-local-GND exception contract.
4. Hardmacro peripherals now have explicit per-row placement handoff rules and perimeter routing/power channel expectations.
5. Storage cells now use one frozen array pitch/orientation rule based on the full-bbox storage pitch audit.
6. Module-level handoff rules now exist for every L3 target module and defer only `SRAM_TOP` / `BANK` / integration-semantics objects to later assembly stages.

## Placement Rule Freeze

- Storage cells use full-bbox pitch: `x=0.895um`, `y=1.565um`.
- Gate-row leaves use same-row edge-touch packing with row-level `R0/MX` alternation policy.
- DFF rows remain explicitly non-overlap across rows.
- Hardmacro peripherals export placement as macro-boundary contracts with reserved routing/power channels.

## Abutment Rule Freeze

- Storage cells: left-right and top-bottom abutment are allowed only under alternating row orientation.
- Gate-row leaves: same-row left-right abutment is frozen; cross-row abutment follows rail alignment policy.
- DFF cells: same-row abut is allowed; vertical overlap is forbidden.
- Peripherals: perimeter keepout/routing channel is preserved unless a macro-specific row policy states otherwise.

## Rail Rule Freeze

- Storage and existing hardmacro leaves use extracted or already-audited rail evidence.
- Composition-backed gate leaves use composition rail contracts and defer exact geometry regeneration to L3.
- `precharge_cell` is frozen as a special case: local `VDD` comes from the hardmacro, while `GND` is imported from the surrounding peripheral rail contract.

## Orientation Policy Freeze

- Storage rows recommend alternating `MX/R0`; `all_R0` is explicitly discouraged due to row-seam power-short risk.
- Gate rows recommend same-row abutment plus cross-row `R0/MX` alternation.
- Hardmacro peripherals stay `R0` by default unless a dedicated mirror audit is added later.

## Pin Access Rule Freeze

- Existing GDS-backed leaves use label-guided pin export.
- Composition-backed leaves use frozen manual/composed pin contracts.
- `precharge_cell` pin access is closed by GDS-label extraction plus the documented power exception.

## Module Handoff Rule Freeze

- Every L3 target module now has a required-primitive list, placement strategy, packer choice, bbox export rule, pin export rule, and rail export rule.
- `SRAM_TOP`, `BANK`, `routing_semantics`, `power_semantics`, and `timing_semantics` remain deferred objects and are not required for L3 standalone module GDS.

## L3 Gate

- `can_claim_L2_placement_abutment_rules_closed_now=True`
- `can_enter_L3_module_gds_generation=True`

## Remaining L2 Blockers

None. Remaining work is now an L3 geometry/module-export problem, not an L2 rule-definition problem.
