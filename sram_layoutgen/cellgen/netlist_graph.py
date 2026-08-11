from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from .mos_graph import MosDevice


@dataclass(frozen=True)
class NetTerminal:
    net: str
    instance: str
    terminal: str


def build_net_terminals(devices: list[MosDevice]) -> dict[str, list[NetTerminal]]:
    nets: dict[str, list[NetTerminal]] = defaultdict(list)
    for dev in devices:
        nets[dev.g].append(NetTerminal(dev.g, dev.instance, "G"))
        nets[dev.s].append(NetTerminal(dev.s, dev.instance, "S"))
        nets[dev.d].append(NetTerminal(dev.d, dev.instance, "D"))
        nets[dev.b].append(NetTerminal(dev.b, dev.instance, "B"))
    return dict(sorted(nets.items()))


def dff_cluster_map(devices: list[MosDevice]) -> dict[str, str]:
    clusters: dict[str, str] = {}
    for dev in devices:
        inst = dev.instance
        if inst.startswith("inv1_clk"):
            cluster = "clock"
        elif inst.startswith("inv2_D") or inst.startswith("tg1"):
            cluster = "input_master_entry"
        elif inst.startswith("inv3") or inst.startswith("inv4") or inst.startswith("tg2"):
            cluster = "master_feedback"
        elif inst.startswith("inv5") or inst.startswith("tg3"):
            cluster = "slave_entry"
        elif inst.startswith("inv6") or inst.startswith("inv7") or inst.startswith("tg4"):
            cluster = "slave_feedback_output"
        else:
            cluster = "unclassified"
        clusters[inst] = cluster
    return clusters


def dff_boundary_pins() -> set[str]:
    return {"D", "Q", "CLK", "VDD", "VSS"}

