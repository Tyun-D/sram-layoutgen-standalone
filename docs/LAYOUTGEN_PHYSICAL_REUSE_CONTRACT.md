# Layoutgen Physical Reuse Contract

Every new bitcell-array, WL-driver-bank, Decoder, or integrated SRAM candidate must load `LAYOUTGEN_PHYSICAL_REUSE_CONTRACT.json`. A missing, malformed, incomplete, or unrecorded contract load is rejected as `REUSE_CONTRACT_NOT_LOADED`.

The contract makes prior Layoutgen behavior executable policy: native row/column pitch, zero-gap intended seams, same-net rail union, endpoint-backed parent stitching, row-aligned WL-driver seams, explicit dummy/tap/replica insertion, final-GDS pin access, and hierarchical/flattened connectivity agreement.

It does not grandfather historical GDS. Shells, zero-width proxies, the L3 4x4 prototype, and flat clipped regions without authoritative pins are explicitly forbidden as authoritative arrays. A new array remains non-authoritative until every required final-GDS gate in the JSON contract passes.
