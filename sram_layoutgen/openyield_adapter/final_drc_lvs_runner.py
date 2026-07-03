from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


def try_run_drc(final_gds: Path, top_cell: str, deck: Path, out_dir: Path) -> dict[str, Any]:
    out_db = out_dir / "final_drc_smoke.lyrdb"
    cmd = [
        "klayout",
        "-b",
        "-r",
        str(deck),
        "-rd",
        f"input={final_gds}",
        "-rd",
        f"topcell={top_cell}",
        "-rd",
        f"output={out_db}",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    except Exception as exc:
        return {
            "drc_smoke_status": "DRC_NOT_RUN_WITH_REASON",
            "drc_marker_count": None,
            "can_claim_drc_clean_now": False,
            "command": cmd,
            "reason": f"DRC invocation failed: {exc}",
        }
    marker_count = None
    if out_db.exists():
        text = out_db.read_text(encoding="utf-8", errors="ignore")
        marker_count = text.count("<item>")
    status = "DRC_NOT_RUN_WITH_REASON"
    can_claim = False
    if proc.returncode == 0 and marker_count is not None:
        if marker_count == 0:
            status = "DRC_SMOKE_CLEAN"
            can_claim = True
        else:
            status = "DRC_SMOKE_RAN_WITH_MARKERS"
    else:
        status = "DRC_NOT_RUN_WITH_REASON"
    return {
        "drc_smoke_status": status,
        "drc_marker_count": marker_count,
        "can_claim_drc_clean_now": can_claim,
        "command": cmd,
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
        "deck_path": str(deck),
        "output_db": str(out_db),
        "reason": "" if status != "DRC_NOT_RUN_WITH_REASON" else "DRC deck/tool ran unsuccessfully or did not produce parseable marker DB.",
    }


def assess_lvs(final_gds: Path, top_cell: str, lvs_deck: Path | None, candidate_netlists: list[Path]) -> tuple[dict[str, Any], dict[str, Any]]:
    feasible = bool(lvs_deck and candidate_netlists)
    matching = [p for p in candidate_netlists if top_cell.lower() in p.name.lower()]
    if matching:
        feasibility_status = "LVS_FEASIBLE_READY_FOR_RUN"
        reason = "Found LVS deck and candidate netlist with matching-ish SRAM naming."
    elif feasible:
        feasibility_status = "LVS_FEASIBLE_WITH_GAPS"
        reason = "LVS deck exists, but no candidate netlist name matches final top cell; top-level mapping remains manual."
    else:
        feasibility_status = "LVS_NOT_FEASIBLE_WITH_REASON"
        reason = "Missing LVS deck or candidate netlist for final top-level mapping."
    feasibility = {
        "lvs_feasibility_status": feasibility_status,
        "final_gds": str(final_gds),
        "top_cell": top_cell,
        "lvs_deck": str(lvs_deck) if lvs_deck else "",
        "candidate_netlists": [str(p) for p in candidate_netlists[:20]],
        "reason": reason,
        "has_extraction_deck": bool(lvs_deck),
        "has_candidate_netlist": bool(candidate_netlists),
        "has_lvs_tool": True,
    }
    run = {
        "lvs_run_status": "NOT_RUN_WITH_REASON",
        "can_claim_lvs_clean_now": False,
        "command": [],
        "reason": "C6 records LVS feasibility only; final top cell to schematic/CDL mapping remains unresolved for an evidence-backed LVS run.",
        "matched_nets": None,
        "unmatched_nets": None,
        "errors": [],
    }
    return feasibility, run


def json_dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
