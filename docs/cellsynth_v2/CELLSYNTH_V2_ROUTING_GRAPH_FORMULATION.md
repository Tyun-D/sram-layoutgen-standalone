# CellSynth v2 Layered Electrical Routing Graph

\[
G_R=(V_R,E_R)
\]

## Node Classes
- `ACTIVE_ACCESS`: diffusion-contactable electrical nodes
- `POLY_ACCESS`: gate access nodes
- `CONTACT`: active/poly to M1 cut nodes
- `M1`, `M2`, `M3`: legal wire grid nodes
- `VIA1`, `VIA2`: legal layer-transition nodes
- `PIN_ACCESS`: legal external pin access sites

## Edge Classes
- `TERMINAL_ACCESS`: terminal to contact/wire access
- `SAME_LAYER_WIRE`: legal wire movement on one layer
- `VIA_TRANSITION`: M1/VIA1/M2 or M2/VIA2/M3 transition
- `PIN_EXTENSION`: route to legal pin site

Every edge stores layer, geometry, capacity, length, resistance proxy, conflict set, TechnologyDB rule references and cost.

## Multi-Terminal Connectivity
For net \(n\), choose a root terminal \(r_n\).  Single-commodity flow:
\[
0\le f_{n,e}\le M route_{n,e}
\]
\[
\sum_{e\in out(v)}f_{n,e}-\sum_{e\in in(v)}f_{n,e}=
\begin{cases}
|T_n|-1,&v=r_n\\
-1,&v\in T_n\setminus\{r_n\}\\
0,&otherwise
\end{cases}
\]
All terminals are connected only if this flow is feasible.

## Via Correctness
M1/M2 overlap is not connectivity.  Connectivity between M1 node \(u\) and M2 node \(v\) requires a selected VIA1 resource:
\[
route_{n,(u,v)} \le via12_{n,s}
\]
Equivalent constraints apply for M2/M3 through VIA2.

## Conflict Constraints
For incompatible resources \(e_1,e_2\):
\[
route_{n_1,e_1}+route_{n_2,e_2}\le 1
\]
when \(n_1\ne n_2\), unless TechnologyDB marks the same-net overlap as legal.
Conflicts include same-track occupation, minimum spacing, via enclosure, via spacing, contact spacing, route-to-gate spacing and pin-access keepout.
