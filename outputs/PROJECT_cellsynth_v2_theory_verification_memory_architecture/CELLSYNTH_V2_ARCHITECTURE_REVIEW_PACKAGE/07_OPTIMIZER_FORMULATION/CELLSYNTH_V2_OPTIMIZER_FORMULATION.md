# CellSynth v2 Algorithm Architecture

## Pipeline
1. Golden electrical specification and canonical MOS graph.
2. TechnologyDB compilation from FreePDK45 rule sources.
3. Symbolic state search over clustering, trail topology, folding, S/D orientation, gate alignment, OD contour requirements, contact access and routing topology.
4. Multi-fidelity validation and pruning.
5. OD/contact/routing geometry synthesis from symbolic state.
6. 2-D constraint compaction without a mandatory central routing channel.
7. Full DRC and layout extraction/LVS.
8. PEX and post-layout characterization for top-K verified candidates.
9. Counterexample feedback into constraints and costs.

## Symbolic State
`S = {transistor_clusters, pn_ordering, trail_topology, finger_assignment, sd_orientation, diffusion_breaks, gate_alignment, od_contour_requirements, contact_access_decisions, pin_access_decisions, routing_topology}`

## Equivalence Relation
Two states are equivalent if they preserve the same parent MOS identity, W/L, G/S/D/B connectivity, pin behavior and TechnologyDB legality, and differ only by canonical reversals, identical-transistor permutations, or mirrored placements that produce the same normalized geometry/resource signatures.

## Variables
- Folding: `nf_i`, finger width partition, legal parent-to-finger mapping.
- Placement: row, column, trail order, cluster order, P/N offset, mirror/orientation, OD contour segments.
- Routing: terminal access, layer assignment, via decisions, track/resource assignment, pin route topology.
- Contact: multiplicity, location, shared-node access, local-only vs routed diffusion node.

## Lower Bounds
- `LB_width`: trail count, gate pitch, contact access and pin corridor minimum.
- `LB_height`: PMOS/NMOS width, rails, well/implant enclosure, routing resources.
- `LB_area`: product/packing lower bound plus mandatory pin and route resources.
- `LB_diffusion_breaks`: graph trail-cover lower bound.
- `LB_routing_tracks`: multi-terminal net demand and layer capacity.
- `LB_vias`: minimum layer transitions required by terminal layers.
- `LB_contact_access`: nodes that must be externally routed.
- `LB_wirelength`: HPWL plus critical-net Steiner lower bound.

## Optimizer
Graph theory supplies transistor graphs, diffusion-sharing relations and trail-cover bounds. BnB/DP explores topology, ordering, folding and break placement with memoized boundary states. CP-SAT/SMT handles discrete placement/routing/contact decisions. A layered routing graph guarantees connectivity through explicit vias. DRC/LVS are correctness oracles; PEX/SPICE are PPA feedback oracles.
