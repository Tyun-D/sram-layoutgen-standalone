# CellSynth v2 Optimizer Mathematical Formulation

## Sets
- Logical MOS devices: \(I=\{1,\ldots,22\}\)
- Fingers of device \(i\): \(K_i=\{1,\ldots,nf_i\}\)
- Nets: \(N\)
- Routing resources: \(E_R\)
- Candidate contact sites: \(C_{n,s}\)
- Candidate via sites: \(V^{12}, V^{23}\)
- Pins: \(P\)

## Decision Variables
- Folding: integer \(nf_i\), continuous/discrete \(W_{i,k}\)
- Placement: \(x_{i,k}, y_{i,k}, row_i, orientation_i, sdflip_i\)
- Diffusion: \(share_{i,j}\in\{0,1\}\), \(break_k\in\{0,1\}\)
- Gate alignment: \(align_{p,n,k}\in\{0,1\}\)
- Contacts: \(contact_{net,site,index}\in\{0,1\}\)
- Routing: \(route_{net,e}\in\{0,1\}\)
- Vias: \(via12_{net,site}, via23_{net,site}\in\{0,1\}\)
- Pins: \(pin_access_{pin,site}\in\{0,1\}\)
- Compaction: edge coordinates \(x_{edge}, y_{edge}\)

## Hard Constraints
1. Logical MOS represented exactly once:
\[
\forall i\in I: \sum_{k=1}^{nf_i} parent(i,k)=1
\]
2. Effective W preservation:
\[
\forall i: \sum_{k=1}^{nf_i} W_{i,k}=W_i^{golden},\quad L_{i,k}=L_i^{golden}
\]
3. Legal folding:
\[
nf_i\in NF_i^{TechnologyDB},\quad W_{i,k}\ge W_{min,type(i)}
\]
4. Legal S/D reversal:
\[
sdflip_i=1 \Rightarrow source/drain\ symmetry\ allowed(i)
\]
5. Non-overlap:
\[
box_a \cap box_b = \emptyset \lor legal\_shared\_diffusion(a,b)
\]
6. Diffusion sharing:
\[
share_{i,j}=1 \Rightarrow type_i=type_j \land adjacent(i,j) \land SDnet_i=SDnet_j \land same\_well(i,j)
\]
7. Diffusion breaks:
\[
break_k=1 \Rightarrow spacing(OD_k,OD_{k+1})\ge OD\_space_{TechnologyDB}
\]
8. Well legality:
\[
PMOS_i \Rightarrow OD_i\subset NWELL,\quad NMOS_i \Rightarrow OD_i\subset PWELL
\]
9. Contact enclosure/spacing:
\[
contact_{n,s}=1 \Rightarrow enclosure(contact_s, layer)\ge rule(layer,contact)
\]
10. Routing capacity/conflicts:
\[
\forall e: \sum_n route_{n,e}\le capacity(e)
\]
11. Layer transitions:
\[
connected_{M1,M2}(n,s)\Rightarrow via12_{n,s}=1
\]
12. Pin connectivity/access:
\[
\forall p\in P: \sum_s pin\_access_{p,s}=1 \land p\in component(net(p))
\]
13. Grid snapping:
\[
x_{edge},y_{edge}\in grid_{TechnologyDB}\mathbb{Z}
\]

## Lower Bounds
- \(LB_{diffusion\_breaks}=trailCover(G_P)+trailCover(G_N)-2\).
- \(LB_{contacts}=|\{diffusion\ nodes\ requiring\ routed\ metal\ access\}|\).
- \(LB_{vias}\) is the count of nets whose terminal layers cannot be connected in one layer.
- \(LB_{wirelength}=\sum_n HPWL(terminals_n)\); this is a lower bound, while congestion-adjusted estimates are heuristics.
- \(LB_{width}\) is maximum of gate-column pitch requirement, OD/contact packing and mandatory pin-access width.
- \(LB_{height}\) is PMOS/NMOS widths plus rail/well/implant/routing minimum resources.
- \(LB_{area}=LB_{width}\cdot LB_{height}\).
- \(LB_{routing\_tracks}\) is the maximum cut demand over routing-resource cuts divided by capacity.

Prune state \(S\) when its lower-bound vector is dominated by no possible improvement over the current Pareto frontier.
