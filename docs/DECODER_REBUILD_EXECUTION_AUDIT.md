# Decoder Rebuild Execution Audit

- timestamp: `2026-07-30T13:10:00Z`
- git_head_at_audit: `aeb78085a4b0c60424e6dca9acddb756acb923de`
- fresh_rebuild_executed: `True`
- drc_marker_count: `2663`
- machine_gate_passed: `False`
- negative_suite_passed: `True`
- unexpected_negative_test_pass_count: `0`
- child_pin_abstraction_incomplete: `True`
- primary_rejection_code: `STRUCTURAL_CONTRACT_FAILED`

## Blocking Dependencies

- decoder child assets still export wildcard bus-style pins rather than bit-exact WL/input pins
- fresh rebuild still trips 2663 FreePDK45 DRC markers
- routing/power/connectivity/foreign-net/pin-access remain false because bit-exact child handoff is not yet authoritative

