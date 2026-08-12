# CellSynth v2 Optimizer Formulation V2

This version fixes ambiguous folding and placement variables before engine implementation.

## Folding
For logical MOS \(i\), allowed finger counts are \(M_i\).  Binary \(z_{i,m}\in\{0,1\}\) selects one finger count:
\[
\sum_{m\in M_i} z_{i,m}=1
\]
Physical finger activity \(a_{i,k}\in\{0,1\}\):
\[
a_{i,k} = \sum_{m\in M_i, k\le m} z_{i,m}
\]
Effective width preservation:
\[
\sum_k W_{i,k}=W_i^{golden},\quad L_{i,k}=L_i^{golden}
\]
Every active finger preserves the parent gate, source, drain and bulk under legal parallel-finger semantics.

## Placement
Assignment is separate from coordinates:
\[
place_{i,k,c,r}\in\{0,1\}
\]
means physical finger \(i,k\) occupies column \(c\), row \(r\).  Coordinates are derived from column/row variables \(X_c,Y_r\), not overloaded into assignment variables.

## Routing and Vias
Routing variables are \(route_{n,e}\in\{0,1\}\) on layered graph edges.  Layer transition edges exist only with via variables:
\[
route_{n,e(M1,M2,s)} \le via12_{n,s}
\]

## Valid Lower Bounds
A quantity is a LOWER_BOUND only if it is provably no greater than every completion.  Otherwise it is `HEURISTIC_ESTIMATE`.

Safe Pareto pruning of partial state \(S\) by feasible incumbent \(U\) is allowed only when:
\[
\forall j,\ U_j \le LB_j(S)
\]
and at least one minimized objective is strictly better where required.

## Reclassified Bounds
- `LB_wirelength = sum HPWL(terminals_n)` is valid under rectilinear routing.
- `LB_contacts` is valid only for nodes that must leave diffusion/poly to metal in every completion; optional performance contacts are heuristic.
- `LB_vias` is valid only when terminal layer sets provably require a layer transition.
- `LB_height` is valid only when derived from required rail/well/device/contact stack minima.
- `LB_routing_tracks` is a lower bound only when computed from a cut-demand proof; otherwise it is a heuristic congestion estimate.
