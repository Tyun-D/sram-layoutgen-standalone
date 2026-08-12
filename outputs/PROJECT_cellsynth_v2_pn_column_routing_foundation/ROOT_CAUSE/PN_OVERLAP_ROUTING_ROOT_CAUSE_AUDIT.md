# PN Overlap Routing Root Cause Audit

`DX14.80` preserves positive P/N overlap (`0.1999999999999993 um`) and external
LVS passes, but external DRC fails.  The marker categories are
`METAL2.2, METAL2.5` only, matching the observed local M2
resource conflict.

Sequence:
- DX0.00: large overlap, DRC_PASS, LVS_COMPARE_FAIL.
- DX0.35: large overlap, DRC_PASS, LVS_COMPARE_FAIL.
- DX14.60: overlap about 0.40 um, DRC_PASS, LVS_COMPARE_FAIL.
- DX14.80: overlap about 0.20 um, LVS_PASS, DRC_FAIL.
- DX17.00: overlap 0, DRC_PASS, LVS_PASS.

Conclusion: P/N overlap is not inherently impossible, but the fixed terminal to
vertical-M2 access template cannot satisfy both DRC and LVS for the frozen
DX14.80 placement.
