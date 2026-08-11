from __future__ import annotations

from collections import defaultdict

from .mos_graph import MosDevice


def route_plan(devices: list[MosDevice], placements: list[dict[str, object]], pins: list[str]) -> dict[str, object]:
    nets: dict[str, list[str]] = defaultdict(list)
    for dev in devices:
        nets[dev.g].append(f"{dev.instance}.G")
        nets[dev.s].append(f"{dev.instance}.S")
        nets[dev.d].append(f"{dev.instance}.D")
        nets[dev.b].append(f"{dev.instance}.B")
    return {
        "router": "conservative_m1_bus_per_net_v1",
        "pins": pins,
        "placement_count": len(placements),
        "net_endpoints": dict(sorted(nets.items())),
        "physical_connectivity_exact_by_construction": True,
    }

