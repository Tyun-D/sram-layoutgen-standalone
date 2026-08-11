from __future__ import annotations

from collections import defaultdict

from .mos_graph import MosDevice
from .netlist_graph import dff_cluster_map


def diffusion_edges(devices: list[MosDevice], mos_type: str) -> list[dict[str, object]]:
    edges = []
    for dev in devices:
        if dev.type != mos_type:
            continue
        edges.append({"device": dev.instance, "u": dev.s, "v": dev.d, "gate": dev.g, "type": dev.type})
    return edges


def compatible_pair(left: MosDevice, right: MosDevice) -> tuple[bool, str | None]:
    shared = sorted({left.s, left.d}.intersection({right.s, right.d}))
    return (left.type == right.type and bool(shared), shared[0] if shared else None)


def greedy_cluster_chains(devices: list[MosDevice], *, reverse: bool = False) -> list[dict[str, object]]:
    clusters = dff_cluster_map(devices)
    grouped: dict[tuple[str, str], list[MosDevice]] = defaultdict(list)
    for dev in devices:
        grouped[(clusters[dev.instance], dev.type)].append(dev)
    rows = []
    for (cluster, mos_type), devs in sorted(grouped.items()):
        remaining = sorted(devs, key=lambda d: d.instance, reverse=reverse)
        chain: list[MosDevice] = []
        if remaining:
            chain.append(remaining.pop(0))
        while remaining:
            last = chain[-1]
            best_i = 0
            best_score = -1
            for i, cand in enumerate(remaining):
                ok, _ = compatible_pair(last, cand)
                score = 2 if ok else 0
                if cand.g == last.g:
                    score += 1
                if score > best_score:
                    best_i = i
                    best_score = score
            chain.append(remaining.pop(best_i))
        shared = 0
        breaks = max(len(chain) - 1, 0)
        flips = []
        for left, right in zip(chain, chain[1:]):
            ok, net = compatible_pair(left, right)
            if ok:
                shared += 1
                breaks -= 1
                flips.append({"left": left.instance, "right": right.instance, "shared_net": net, "sd_flip": False})
        rows.append({
            "cluster": cluster,
            "mos_type": mos_type,
            "order": [d.instance for d in chain],
            "shared_diffusion_count": shared,
            "diffusion_break_count": breaks,
            "sd_orientation": flips,
            "estimated_width": round(0.72 * len(chain) + 0.16 * max(breaks, 0), 4),
        })
    return rows

