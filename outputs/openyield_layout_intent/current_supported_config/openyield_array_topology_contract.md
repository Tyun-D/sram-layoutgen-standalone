# OpenYield Array Topology Contract

- bitcell_array role: SRAM main storage array
- dummy_array role: Array edge/dummy placeholder used to represent non-active boundary storage context, not final complete boundary proof.
- replica_array role: Replica timing/reference array feeding timing/control semantics and later replica routing intent.
- num_rows to WL relation: Each physical wordline WL[i] must correspond to exactly one bitcell row in the supported scope.
- num_cols to BL relation: Each physical column contributes one BL and one BR rail; total BL/BR pair count follows num_cols.

## Ownership Summary

- row pitch source: existing bitcell_array reference geometry and future R3 array generator pitch model
- column pitch source: existing bitcell_array reference geometry and future R3 array generator pitch model
- BL/BR expectation: BL/BR vertical along array columns
- WL expectation: WL horizontal across array rows
- rail expectation: Array rails must be exported as top/bottom or side rail handoff metadata first, then proven by real geometry in R4.

## Missing For R3

- Real array wrapper generator for complete main/dummy/replica/boundary composition
- Real pitch-owned geometry rather than standalone candidate references
- Explicit boundary/tap/well implementation policy
