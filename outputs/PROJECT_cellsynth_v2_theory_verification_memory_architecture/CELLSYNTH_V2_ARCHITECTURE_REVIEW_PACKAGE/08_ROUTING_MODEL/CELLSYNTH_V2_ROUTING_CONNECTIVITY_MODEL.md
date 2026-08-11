# CellSynth v2 Routing Connectivity Model

Routing is a layered graph. Nodes are legal grid/access/via points. Edges are legal same-layer wire moves or legal via transitions. A net is connected only if all terminals are in one graph component. M1/M2 geometric overlap without VIA1 is not a connection.

There is no mandatory central routing channel. Routing resources are allocated wherever TechnologyDB and pin-access constraints permit them.
