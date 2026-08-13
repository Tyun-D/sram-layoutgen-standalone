# Physical Shared Diffusion Contract

Physical shared diffusion is valid only when a logical source/drain adjacency
maps to one continuous ACTIVE component.  A metal-only connection between two
independent ACTIVE rectangles does not count.

Required conditions:
- same MOS type and compatible well/body domain;
- shared source/drain electrical net at the chain boundary;
- continuous ACTIVE geometry across the boundary;
- legal POLY gate crossings for both parent MOS devices;
- node-based contact insertion only where metal access is required;
- external DRC PASS and external LVS PASS.
