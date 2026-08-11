# CellSynth v2 Symbolic State Canonicalization

`canonical_hash(S)` is computed from sorted parent MOS identities, normalized trail covers, normalized finger partitions, normalized S/D orientations, pin mapping, routing topology and TechnologyDB rule version.

Equivalent states:
- identical-device permutations with same G/S/D/B and W/L;
- source/drain reversal when electrically legal and normalized by unordered S/D pair;
- trail reversal where endpoint pins and access costs are symmetric;
- whole-cell mirror when external pin contract and well/body legality are preserved;
- finger permutations within the same parent MOS;
- routing-resource symmetries that map to the same layer/resource conflict graph.

Invariant data:
parent MOS identity, W/L, type, G/S/D/B up to legal S/D symmetry, external pin mapping, required routed-net connectivity, TechnologyDB version and hard-rule satisfaction.
