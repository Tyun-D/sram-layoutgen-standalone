# OpenYield Upstream TB Interface Contract

- upstream_commit: `1c34428d8b913963c4971d093b1a7c2df97a2509`
- classification: `UPSTREAM_REFERENCE_TB`

## What The Upstream TB Assumes

- A Python/PySpice-driven transient harness, not a standalone checked-in project TB.
- A full SRAM assembly around `TIME`, `ADDR_DFF`, `DATA_DFF`, `DECODER_CASCADE`, `WORDLINEDRIVER`, `PRECHARGE`, `SENSEAMP`, `WRITEDRIVER`, replica/dummy structures, and the core array.
- Explicit control semantics for `clk`, `csb`, `web`, `wl_en`, `s_en`, `w_en`, and `PRE`.
- Explicit address/data staging semantics for `A[0:3]`, `A_dff[0:3]`, `DIN[0:15]`, and `DIN_dff[0:15]`.
- Operation-specific measurement contracts for `read`, `write`, `read&write`, `hold_snm`, `read_snm`, and `write_snm`.

## Why It Is Not Yet A Trusted Project TB

- The current project has reviewed the upstream source, but has not adopted it as-is.
- Current authoritative project evidence does not yet bind all required control/TIME semantics to a reviewed project-owned top-level TB.
- Therefore the upstream files remain `UPSTREAM_REFERENCE_TB`, not `TRUSTED_PROJECT_TB`.
