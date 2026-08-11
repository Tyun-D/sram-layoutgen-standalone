from __future__ import annotations

from .mos_graph import MosDevice


LEGAL_ORIENTATIONS = ("R0", "MX", "MY", "R180")


def orientation_matrix(devices: list[MosDevice]) -> list[dict[str, object]]:
    rows = []
    for dev in devices:
        for orient in LEGAL_ORIENTATIONS:
            rows.append({
                "instance": dev.instance,
                "type": dev.type,
                "orientation": orient,
                "legal": True,
                "source": "FreePDK45_rectilinear_MOS_template_pin_transform",
            })
    return rows


def orientation_for(candidate_index: int, dev: MosDevice, cluster: str) -> tuple[str, bool]:
    if candidate_index % 5 == 0:
        return ("R0", False)
    if candidate_index % 5 == 1:
        return ("MX" if dev.type == "PMOS" else "R0", False)
    if candidate_index % 5 == 2:
        return ("MY", True)
    if candidate_index % 5 == 3:
        return ("R180" if cluster in {"master_feedback", "slave_feedback_output"} else "R0", True)
    return (LEGAL_ORIENTATIONS[(hash(dev.instance) + candidate_index) % len(LEGAL_ORIENTATIONS)], candidate_index % 2 == 0)

