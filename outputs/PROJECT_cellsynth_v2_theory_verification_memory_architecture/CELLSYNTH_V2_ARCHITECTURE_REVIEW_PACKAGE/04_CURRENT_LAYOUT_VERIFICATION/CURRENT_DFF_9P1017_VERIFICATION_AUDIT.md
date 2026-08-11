# Current 9.1017 um^2 DFF Verification Audit

Candidate: `DFF_TOPO_SHARED_00_7_TRAIL`

- GDS SHA256: `947f731dba2973a568dec435bd0f173b2338eb69e1d62e43f71252e966413cd1`
- DRC: `DRC_PASS`
- LVS: `LVS_FAIL`
- LVS root cause: LVS setup reached extraction but failed top-cell schematic correspondence; generated layout top is DFF_TOPO_SHARED_00_7_TRAIL while golden subckt is dff_openyield_original.
- PEX: `PEX_UNAVAILABLE`
- Post-layout function: `NOT_RUN`
- Source schematic transient: `PASS`

Conclusion: this candidate is compact and DRC-clean, but it is not admitted to the physically valid Pareto set because LVS has not passed. Future CellSynth v2 work must produce a generated-cell LVS wrapper or matching top/subckt naming so extraction can be compared against the golden electrical spec.
