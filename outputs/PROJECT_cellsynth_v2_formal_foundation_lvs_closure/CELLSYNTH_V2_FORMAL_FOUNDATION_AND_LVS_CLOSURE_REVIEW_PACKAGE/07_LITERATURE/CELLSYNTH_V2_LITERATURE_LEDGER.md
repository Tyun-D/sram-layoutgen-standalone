# CellSynth v2 Literature Ledger - Evidence Classified

Evidence tags: `PAPER_EXPLICIT`, `PAPER_DERIVED`, `ABSTRACT_ONLY`, `IMPLEMENTATION_EVIDENCE`, `OUR_ADAPTATION`, `OPEN_QUESTION`.

The previous ledger is retained below, but future claims must carry evidence tags. Items whose full paper text was unavailable remain `ABSTRACT_ONLY` or `OPEN_QUESTION`; CellSynth-specific equations are `OUR_ADAPTATION` unless explicitly paper-backed.

## Evidence Separation Rules
- Do not attribute lower-bound, canonicalization or pruning formulas to a paper unless the paper states them.
- AutoCellGen observations are `IMPLEMENTATION_EVIDENCE`, not proof of correctness.
- DATE 2024 PDF-derived pin-access/ghost-resource concepts are `PAPER_EXPLICIT` only where the PDF text supports them.

# CellSynth v2 Literature Ledger - Evidence Classified

Evidence tags: `PAPER_EXPLICIT`, `PAPER_DERIVED`, `ABSTRACT_ONLY`, `IMPLEMENTATION_EVIDENCE`, `OUR_ADAPTATION`, `OPEN_QUESTION`.

The previous ledger is retained below, but future claims must carry evidence tags. Items whose full paper text was unavailable remain `ABSTRACT_ONLY` or `OPEN_QUESTION`; CellSynth-specific equations are `OUR_ADAPTATION` unless explicitly paper-backed.

## Evidence Separation Rules
- Do not attribute lower-bound, canonicalization or pruning formulas to a paper unless the paper states them.
- AutoCellGen observations are `IMPLEMENTATION_EVIDENCE`, not proof of correctness.
- DATE 2024 PDF-derived pin-access/ghost-resource concepts are `PAPER_EXPLICIT` only where the PDF text supports them.

# CellSynth v2 Literature Ledger - Evidence Classified

Evidence tags: `PAPER_EXPLICIT`, `PAPER_DERIVED`, `ABSTRACT_ONLY`, `IMPLEMENTATION_EVIDENCE`, `OUR_ADAPTATION`, `OPEN_QUESTION`.

The previous ledger is retained below, but future claims must carry evidence tags. Items whose full paper text was unavailable remain `ABSTRACT_ONLY` or `OPEN_QUESTION`; CellSynth-specific equations are `OUR_ADAPTATION` unless explicitly paper-backed.

## Evidence Separation Rules
- Do not attribute lower-bound, canonicalization or pruning formulas to a paper unless the paper states them.
- AutoCellGen observations are `IMPLEMENTATION_EVIDENCE`, not proof of correctness.
- DATE 2024 PDF-derived pin-access/ghost-resource concepts are `PAPER_EXPLICIT` only where the PDF text supports them.

# CellSynth v2 Theory and Methods

## Kyeongrok Jo, Taewhan Kim, Optimal Transistor Placement Combined with Global In-cell Routing in Standard Cell Layout Synthesis, ICCD 2021, DOI 10.1109/ICCD53106.2021.00085
- **SOURCE_URL:** https://www.researchgate.net/publication/357217721_Optimal_Transistor_Placement_Combined_with_Global_In-cell_Routing_in_Standard_Cell_Layout_Synthesis
- **EVIDENCE_LEVEL:** metadata/abstract-backed; full paper not locally licensed in this run
- **PROBLEM:** Transistor placement quality is limited when routability is evaluated only after placement.
- **INPUTS:** Cell transistor netlist, technology constraints, placement candidates, global in-cell routing model.
- **DECISION_VARIABLES:** Transistor positions/orderings plus global routing resources coupled to placement.
- **HARD_CONSTRAINTS:** Legal device placement and in-cell routing under technology rules.
- **OBJECTIVE_FUNCTION:** Placement objectives with routability integrated before final routing.
- **SEARCH_METHOD:** Optimization/SMT-style combined placement and global routing, per available metadata.
- **LOWER_BOUNDS:** Use routing-resource lower bounds to reject placement states that cannot route.
- **SYMMETRY_BREAKING:** Canonicalize electrically equivalent transistor orderings and mirrored trail orders.
- **PRUNING:** Prune placement states whose global-route lower bound cannot dominate.
- **ROUTABILITY_MODEL:** Global in-cell routing should be in the placement loop, not a post-check.
- **GEOMETRY_MODEL:** Symbolic layout state must carry routing resources, pins and device access.
- **CONTACT_MODEL:** Access points are part of routing feasibility, not fixed per-terminal contacts.
- **VERIFICATION_MODEL:** DRC/LVS remain external correctness gates.
- **PPA_MODEL:** Area alone is insufficient; route length and congestion affect quality.
- **SCALABILITY:** Coupling placement/routing increases complexity; use lower bounds and staged fidelity.
- **STRENGTHS:** Directly addresses the previous OpenYield failure mode: compact FEOL but fragile routing.
- **LIMITATIONS:** This run did not access full formulation details; use as design direction, not exact implementation.
- **DIRECTLY_APPLICABLE_IDEAS:** Route-aware placement state; routing lower-bound pruning; candidate invalidation on route infeasibility.
- **IDEAS_NOT_APPLICABLE_TO_FREEPDK45:** Advanced-node grid assumptions not present in FreePDK45 must not be copied.
- **IMPLEMENTATION_ACTIONS_FOR_OPENYIELD:** Add routing-resource lower bounds to Level-0 symbolic state and feed LVS/DRC route failures back to placement.

## Kyeonghyeon Baek, Taewhan Kim, CSyn-fp: Standard Cell Synthesis of Advanced Nodes With Simultaneous Transistor Folding and Placement, IEEE TCAD 43(2), 2024, DOI 10.1109/TCAD.2023.3320631
- **SOURCE_URL:** https://ieeexplore.ieee.org/document/10266711/
- **EVIDENCE_LEVEL:** IEEE metadata-backed plus AutoCellGen implementation README
- **PROBLEM:** Folding and placement are strongly coupled and should not be optimized sequentially.
- **INPUTS:** SPICE/CDL netlist and process/layout constraints.
- **DECISION_VARIABLES:** Folding choice, transistor placement/order, row/column assignment, routability estimates.
- **HARD_CONSTRAINTS:** Topology/W/L preservation, legal folding, legal placement.
- **OBJECTIVE_FUNCTION:** Cell size and routability-aware cost via DP/search.
- **SEARCH_METHOD:** Search tree and dynamic programming for simultaneous folding/placement.
- **LOWER_BOUNDS:** Partial placement/folding cost lower bounds for pruning.
- **SYMMETRY_BREAKING:** Identical-device partitioning and equivalent state canonicalization.
- **PRUNING:** Dominance and bound-based pruning of partial placement states.
- **ROUTABILITY_MODEL:** Expected routability must enter placement scoring.
- **GEOMETRY_MODEL:** Column-based transistor placement representation, not raw polygons.
- **CONTACT_MODEL:** Contacts/access must be evaluated with placement because folding changes terminals.
- **VERIFICATION_MODEL:** Generated placements still require routing/GDS/verification; AutoCellGen notes DRC violations may remain.
- **PPA_MODEL:** Cell area and routability first; CellSynth v2 extends with PEX/timing feedback.
- **SCALABILITY:** DP/search avoids raw exhaustive enumeration.
- **STRENGTHS:** Closest match to OpenYield DFF need: 22 MOS, folding as a first-class decision.
- **LIMITATIONS:** Source implementation is advanced-node/ASAP7-oriented; cannot import PDK or cells.
- **DIRECTLY_APPLICABLE_IDEAS:** Canonical state, folding variables, DP cost, lower bounds, identical transistor pruning.
- **IDEAS_NOT_APPLICABLE_TO_FREEPDK45:** ASAP7 fin/grid specifics and bundled Z3 versions are not FreePDK45 authority.
- **IMPLEMENTATION_ACTIONS_FOR_OPENYIELD:** Define DFF symbolic state with finger assignment and no geometry generation until folding/placement state is legal.

## Handong Cho et al., Standard Cell Layout Generator Amenable to Design Technology Co-Optimization in Advanced Process Nodes, DATE 2024
- **SOURCE_URL:** https://past.date-conference.com/proceedings-archive/2024/DATA/518_pdf_upload.pdf
- **EVIDENCE_LEVEL:** full DATE PDF accessible in this run
- **PROBLEM:** Routing completion and pin accessibility degrade when placement ignores pin-access resources.
- **INPUTS:** Cell topology, technology grids/layers, pin-access constraints, routing resources.
- **DECISION_VARIABLES:** FET placement, ghost-via/ghost-metal reservation, pin separation/extension, routing assignments.
- **HARD_CONSTRAINTS:** Technology legality, pin accessibility, routing feasibility.
- **OBJECTIVE_FUNCTION:** Improve in-cell routing completion and pin accessibility, not just cell area.
- **SEARCH_METHOD:** Generator with prediction/reservation concepts and SMT-style routing references.
- **LOWER_BOUNDS:** Pin access/routing resource lower-bound checks before final routing.
- **SYMMETRY_BREAKING:** Not the primary contribution; CellSynth should handle canonical states separately.
- **PRUNING:** Reject placements with insufficient pin openings or blocked access corridors.
- **ROUTABILITY_MODEL:** Ghost-via and ghost-metal reserve resources during placement/routing.
- **GEOMETRY_MODEL:** Layered grid/resource model with pin access as a design object.
- **CONTACT_MODEL:** Contact/via access is modeled as routing capacity, not accidental overlap.
- **VERIFICATION_MODEL:** Full DRC/LVS remains necessary.
- **PPA_MODEL:** Pin accessibility and congestion are PPA-relevant because unusable pins harm block implementation.
- **SCALABILITY:** Use resource reservation rather than exhaustive detailed routing for all partial states.
- **STRENGTHS:** Directly applies to our DFF pin/via correctness policy.
- **LIMITATIONS:** Advanced-node MOL/M0 details must be mapped to FreePDK45 M1/VIA1/M2/M3 only if rules exist.
- **DIRECTLY_APPLICABLE_IDEAS:** Pin access penalties, ghost via/metal resource reservation, no overlap-without-via connectivity.
- **IDEAS_NOT_APPLICABLE_TO_FREEPDK45:** M0/MOL constructs absent from current rule deck unless TechnologyDB maps an equivalent.
- **IMPLEMENTATION_ACTIONS_FOR_OPENYIELD:** Add pin-access corridors and ghost-via reservations to TechnologyDB and symbolic state.

## Sehyeon Chung, Hyunbae Seo, Taewhan Kim, Synthesis of Standard Cells of Minimum Delay, ICCAD 2025, DOI 10.1109/ICCAD66269.2025.11240906
- **SOURCE_URL:** https://ieeexplore.ieee.org/document/11240906/
- **EVIDENCE_LEVEL:** IEEE/SNU metadata and abstract-backed; full paper not locally licensed in this run
- **PROBLEM:** Minimum-area cell synthesis may produce electrically poor cells; delay can be the primary objective.
- **INPUTS:** Cell netlist, timing/delay objective, technology constraints.
- **DECISION_VARIABLES:** Placement/folding/routing choices weighted by critical paths.
- **HARD_CONSTRAINTS:** Physical correctness and topology preservation.
- **OBJECTIVE_FUNCTION:** Delay-first objective with area as secondary/constraint dimension.
- **SEARCH_METHOD:** Critical-path-driven placement/routing with pruning, per abstract/metadata.
- **LOWER_BOUNDS:** Critical-net delay lower bounds should prune states with unavoidable bad timing.
- **SYMMETRY_BREAKING:** Equivalent geometric states need canonicalization before timing evaluation.
- **PRUNING:** Reject partial states whose critical-net parasitic bounds exceed frontier.
- **ROUTABILITY_MODEL:** Critical nets are routed with higher priority/constraints.
- **GEOMETRY_MODEL:** Device proximity and pin access affect clock-to-Q and setup/hold.
- **CONTACT_MODEL:** Extra contacts may reduce resistance; contact count is not always to be minimized.
- **VERIFICATION_MODEL:** PEX/post-layout characterization required before delay claims.
- **PPA_MODEL:** Delay, setup/hold, slew, input cap, dynamic/leakage power join Pareto vector.
- **SCALABILITY:** Run SPICE only on top-K verified candidates.
- **STRENGTHS:** Prevents repeating the 9.1017 um² mistake of ranking area without LVS/PEX.
- **LIMITATIONS:** No FreePDK45-calibrated delay model currently exists.
- **DIRECTLY_APPLICABLE_IDEAS:** Timing-aware feedback from PEX/SPICE to placement/routing cost.
- **IDEAS_NOT_APPLICABLE_TO_FREEPDK45:** Any advanced-node parasitic model not backed by current extraction data.
- **IMPLEMENTATION_ACTIONS_FOR_OPENYIELD:** Add Level-4 characterization only after Level-2/3 qualification; do not call schematic transient post-layout.

## CPCell / Extended Study of Gear-Ratio-Aware Standard Cell Layout Generation for DTCO Exploration, arXiv:2603.13665
- **SOURCE_URL:** https://arxiv.org/abs/2603.13665
- **EVIDENCE_LEVEL:** arXiv full abstract and PDF available
- **PROBLEM:** Arbitrary gear ratios and offsets affect routability and block PPA; cell generation must represent layered grids explicitly.
- **INPUTS:** Netlists, architecture/design rules, CPP/M1 pitch/gear-ratio/offset configuration.
- **DECISION_VARIABLES:** Placement-routing co-optimization variables, M0 pin enablement, routing graph resources, offset variants.
- **HARD_CONSTRAINTS:** Technology rules, pin accessibility, global optimality target under configured PDK.
- **OBJECTIVE_FUNCTION:** Weighted multi-objective optimization including layout quality, pin access and routing.
- **SEARCH_METHOD:** Constraint programming / CP-SAT compatible with SMT formulations.
- **LOWER_BOUNDS:** Routing lower-bound tightening and early termination with optimality gap.
- **SYMMETRY_BREAKING:** Transistor clustering and identical-transistor partitioning.
- **PRUNING:** Early termination and lower-bound tightening to scale up to larger cells.
- **ROUTABILITY_MODEL:** Fine-grained layered grid graph with pin and routing resources.
- **GEOMETRY_MODEL:** Technology-compiled grid/layer model.
- **CONTACT_MODEL:** Pin/via resources are explicit and capacity-constrained.
- **VERIFICATION_MODEL:** External DRC/LVS remains required after generated candidate.
- **PPA_MODEL:** Cell-level and block-level PPA/IR-drop evaluation.
- **SCALABILITY:** Reported acceleration and larger transistor-count support in source abstract.
- **STRENGTHS:** Best match for TechnologyDB + layered routing graph architecture.
- **LIMITATIONS:** Gear-ratio concepts are advanced-node-specific; FreePDK45 may not need arbitrary GR.
- **DIRECTLY_APPLICABLE_IDEAS:** Layered graph, CP-SAT resource constraints, identical-transistor partitioning, routing lower-bound tightening.
- **IDEAS_NOT_APPLICABLE_TO_FREEPDK45:** PROBE3.0-specific PDK assumptions, M0/MOL unless mapped.
- **IMPLEMENTATION_ACTIONS_FOR_OPENYIELD:** Implement TechnologyDB-backed layered graph and a configurable top-K PEX/SPICE policy.

## Haoxing Ren, Matthew Fojtik, Brucek Khailany, NVCell: Standard Cell Layout in Advanced Technology Nodes with Reinforcement Learning, arXiv:2107.07044
- **SOURCE_URL:** https://arxiv.org/abs/2107.07044
- **EVIDENCE_LEVEL:** arXiv abstract/PDF available
- **PROBLEM:** Complex design rules make placement and routing repair difficult for handcrafted search.
- **INPUTS:** Cell candidates, routing/DRC state, placement state.
- **DECISION_VARIABLES:** RL-guided placement and DRC-repair actions.
- **HARD_CONSTRAINTS:** DRC/LVS correctness cannot be replaced by RL.
- **OBJECTIVE_FUNCTION:** Area-quality and DRC repair efficiency.
- **SEARCH_METHOD:** Reinforcement learning for placement guidance and violation repair.
- **LOWER_BOUNDS:** Not a correctness backbone; use exact lower bounds separately.
- **SYMMETRY_BREAKING:** Learning may rank canonical states but should not define equivalence.
- **PRUNING:** Use ML only as heuristic ranking/prediction.
- **ROUTABILITY_MODEL:** RL can guide routing repair but physical router remains explicit.
- **GEOMETRY_MODEL:** Generated geometry must still be rule-checked.
- **CONTACT_MODEL:** Can suggest access repair actions, not authority.
- **VERIFICATION_MODEL:** DRC/LVS are non-negotiable oracles.
- **PPA_MODEL:** ML can predict PPA but PEX/SPICE characterize top candidates.
- **SCALABILITY:** Useful for candidate ordering when exact search is expensive.
- **STRENGTHS:** Good future repair-action ranker for DRC/LVS counterexamples.
- **LIMITATIONS:** Cannot be used as proof of correctness.
- **DIRECTLY_APPLICABLE_IDEAS:** Learned proposal/ranking/repair policy as optional accelerator.
- **IDEAS_NOT_APPLICABLE_TO_FREEPDK45:** Any pretrained model or process-specific learned rule not trained on current FreePDK45 evidence.
- **IMPLEMENTATION_ACTIONS_FOR_OPENYIELD:** Document ML/RL as optional; do not implement until exact CellSynth v2 gates exist.

## The OpenROAD Project AutoCellGen implementation
- **SOURCE_URL:** https://github.com/The-OpenROAD-Project/AutoCellGen
- **EVIDENCE_LEVEL:** GitHub README inspected
- **PROBLEM:** End-to-end standard-cell layout generation needs netlist, placement, routing, and GDS flow integration.
- **INPUTS:** Netlist files (.cdl/.sp), placement style/config files, technology-dependent assets.
- **DECISION_VARIABLES:** Transistor placement columns and route execution.
- **HARD_CONSTRAINTS:** Tool-specific dependency versions; generated cells may still require DRC cleanup.
- **OBJECTIVE_FUNCTION:** Automated placement/routing/GDS generation.
- **SEARCH_METHOD:** CSyn-fp placement plus in-cell route process using Z3 in implementation.
- **LOWER_BOUNDS:** Implementation details require source review before adoption.
- **SYMMETRY_BREAKING:** Placement output representation suggests canonical column pair encoding.
- **PRUNING:** Use ideas only after license review.
- **ROUTABILITY_MODEL:** In-cell routing is part of executable flow.
- **GEOMETRY_MODEL:** Pipeline produces placement, IO net, and GDS outputs.
- **CONTACT_MODEL:** Implementation reference only; do not copy geometry/PDK.
- **VERIFICATION_MODEL:** README notes generated cells may have DRC violations; external verification mandatory.
- **PPA_MODEL:** Use as software architecture reference, not a FreePDK45 signoff model.
- **SCALABILITY:** Separates netlist-to-placement from route/GDS flow.
- **STRENGTHS:** Useful architecture decomposition and file discipline.
- **LIMITATIONS:** ASAP7 examples and source license must be reviewed before code reuse.
- **DIRECTLY_APPLICABLE_IDEAS:** Clean module boundaries: netlist, placement, routing, GDS, verification artifacts.
- **IDEAS_NOT_APPLICABLE_TO_FREEPDK45:** ASAP7 netlists/rules and bundled standard cells.
- **IMPLEMENTATION_ACTIONS_FOR_OPENYIELD:** Use architecture pattern only; implement FreePDK45/OpenYield-native code under project license.
