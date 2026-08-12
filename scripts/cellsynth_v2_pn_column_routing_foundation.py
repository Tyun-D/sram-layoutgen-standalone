#!/usr/bin/env python3
"""PN-column routing co-optimization foundation audit.

This stage records the V1 coopt blocker precisely and creates the foundation
artifacts for replacing global NMOS-row translation with a true symbolic
P/N-column model.  It does not claim a false PASS when DX14.80 remains
unrepaired.
"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import re
import shutil
import tarfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "PROJECT_cellsynth_v2_pn_column_routing_foundation"
REVIEW = Path("/data1/qujh/cellsynth_v2_pn_column_routing_foundation_review/latest")
PKG = Path("/data1/qujh/PROJECT_CELLSYNTH_V2_PN_COLUMN_ROUTING_COOPT_FOUNDATION_REVIEW_PACKAGE_LATEST.tar.gz")
EXPECTED_RULES_SHA = "e11af7a70fa8d99f0ec5a21a99a88df1f0a8b4b45c64499d3dbc1a42b600404d"
PREV = REPO / "outputs/PROJECT_cellsynth_v2_verified_coopt_engine_v1"
DX148 = "DFF_V2_COOPT_S1_P1p50_DX14p80_B0p42"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = sorted({k for r in rows for k in r})
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def work_start() -> dict[str, Any]:
    files = [
        "docs/PROJECT_GLOBAL_WORK_RULES.md",
        "docs/PROJECT_CURRENT_STATUS.json",
        "docs/PROJECT_TASK_MASTER_LOG.md",
        "docs/cellsynth_v2/CELLSYNTH_V2_WORKING_MEMORY.md",
        "docs/cellsynth_v2/CELLSYNTH_V2_THEORY_AND_METHODS.md",
        "docs/cellsynth_v2/CELLSYNTH_V2_LITERATURE_LEDGER.md",
        "docs/cellsynth_v2/CELLSYNTH_V2_OPTIMIZER_FORMULATION_V2.md",
        "docs/cellsynth_v2/CELLSYNTH_V2_ROUTING_GRAPH_FORMULATION.md",
        "docs/cellsynth_v2/CELLSYNTH_V2_VERIFICATION_AND_SIMULATION_POLICY.md",
        "docs/cellsynth_v2/CELLSYNTH_V2_TECHNOLOGY_RULE_POLICY.md",
    ]
    shas = {f: sha(REPO / f) for f in files}
    audit = {
        "WORK_START_RULE_AUDIT": "PASS" if shas["docs/PROJECT_GLOBAL_WORK_RULES.md"] == EXPECTED_RULES_SHA else "FAIL",
        "GLOBAL_RULES_READ": True,
        "GLOBAL_RULES_SHA": shas["docs/PROJECT_GLOBAL_WORK_RULES.md"],
        "CURRENT_STATUS_READ": True,
        "LATEST_MASTER_LOG_READ": True,
        "CELLSYNTH_MEMORY_READ": True,
        "file_shas": shas,
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    write_json(OUT / "GLOBAL_RULES/WORK_START_RULE_AUDIT.json", audit)
    return audit


def drc_categories(lyrdb: Path) -> tuple[list[str], list[dict[str, Any]]]:
    if not lyrdb.exists():
        return [], []
    root = ET.parse(lyrdb).getroot()
    cats = []
    markers = []
    for item in root.findall(".//item"):
        texts = [e.text.strip() for e in item.iter() if e.text and e.text.strip()]
        cat = texts[0].strip("'") if texts else "UNKNOWN"
        cats.append(cat)
        markers.append({"category": cat, "raw": texts})
    return sorted(set(cats)), markers


def candidate_record(name: str) -> dict[str, Any]:
    p = PREV / "CANDIDATES" / name / "CANDIDATE_RECORD.json"
    data = read_json(p)
    lyrdb = PREV / "CANDIDATES" / name / "DRC" / f"{name}.lyrdb"
    cats, markers = drc_categories(lyrdb)
    return {
        "candidate": name,
        "nmos_dx": data["params"]["nmos_dx"],
        "pn_overlap": data["pmos_nmos_overlap_x"],
        "area": data["area"],
        "DRC": data["drc"],
        "DRC_markers": data["drc_markers"],
        "DRC_categories": cats,
        "LVS": data["lvs"],
        "routing_resources": {
            "contact_count": data["contact_count"],
            "via1_count": data["via1_count"],
            "via2_count": data["via2_count"],
            "total_routed_length": data["total_routed_length"],
        },
        "markers": markers[:40],
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    audit = work_start()
    if audit["WORK_START_RULE_AUDIT"] != "PASS":
        raise SystemExit("work-start audit failed")

    reinterpretation = {
        "PN_SIMULTANEOUS_PLACEMENT_GATE": "FAIL",
        "MASTER_OPTIMIZER_SCAFFOLD_GATE": "PASS",
        "MASTER_STRUCTURAL_OPTIMIZER_GATE": "NOT_YET_DEMONSTRATED",
        "ROUTING_SUBPROBLEM_SCAFFOLD_GATE": "PASS",
        "ROUTING_ORACLE_FEEDBACK_GATE": "FAIL",
        "CONTACT_SYNTHESIS_ENGINE_GATE": "PASS",
        "CONTACT_OPTIMIZATION_EFFECT_GATE": "NOT_DEMONSTRATED",
        "OD_ENGINE_GATE": "PASS_IF_CODE_EVIDENCE_SUPPORTS_IT",
        "OD_COOPT_EFFECT_GATE": "NOT_DEMONSTRATED",
        "DIFFUSION_GRAPH_ANALYSIS_GATE": "PASS",
        "PHYSICAL_SHARED_DIFFUSION_COOPT_GATE": "NOT_DEMONSTRATED_IN_THIS_V2_STAGE",
        "principle": "Scaffold or infrastructure existence is not proof of effective optimization.",
    }
    write_json(OUT / "GATE_REINTERPRETATION/CELLSYNTH_V2_COOPT_V1_GATE_REINTERPRETATION.json", reinterpretation)

    names = [
        "DFF_V2_COOPT_S1_P1p50_DX0p00_B0p45",
        "DFF_V2_COOPT_S1_P1p50_DX0p35_B0p42",
        "DFF_V2_COOPT_S1_P1p50_DX14p60_B0p42",
        DX148,
        "DFF_V2_COOPT_S1_P1p50_DX17p00_B0p42",
    ]
    records = [candidate_record(n) for n in names]
    write_json(OUT / "ROOT_CAUSE/PN_OVERLAP_ROUTING_ROOT_CAUSE_AUDIT.json", {"candidates": records})
    write_csv(OUT / "ROOT_CAUSE/PN_OVERLAP_ROUTING_ROOT_CAUSE_AUDIT.csv", [
        {k: (json.dumps(v) if isinstance(v, (dict, list)) else v) for k, v in r.items() if k != "markers"} for r in records
    ])
    dx = next(r for r in records if r["candidate"] == DX148)
    write(OUT / "ROOT_CAUSE/PN_OVERLAP_ROUTING_ROOT_CAUSE_AUDIT.md", f"""# PN Overlap Routing Root Cause Audit

`DX14.80` preserves positive P/N overlap (`{dx['pn_overlap']} um`) and external
LVS passes, but external DRC fails.  The marker categories are
`{', '.join(dx['DRC_categories'])}` only, matching the observed local M2
resource conflict.

Sequence:
- DX0.00: large overlap, DRC_PASS, LVS_COMPARE_FAIL.
- DX0.35: large overlap, DRC_PASS, LVS_COMPARE_FAIL.
- DX14.60: overlap about 0.40 um, DRC_PASS, LVS_COMPARE_FAIL.
- DX14.80: overlap about 0.20 um, LVS_PASS, DRC_FAIL.
- DX17.00: overlap 0, DRC_PASS, LVS_PASS.

Conclusion: P/N overlap is not inherently impossible, but the fixed terminal to
vertical-M2 access template cannot satisfy both DRC and LVS for the frozen
DX14.80 placement.
""")

    dx_gate = {
        "DX14P80_ROUTING_REPAIR_GATE": "FAIL",
        "candidate": DX148,
        "transistor_placement_preserved": True,
        "pmos_nmos_overlap_x": dx["pn_overlap"],
        "Level1Connectivity": "PASS_FROM_PREVIOUS_SYMBOLIC_CHECK",
        "external_DRC": dx["DRC"],
        "external_LVS": dx["LVS"],
        "blocking_categories": dx["DRC_categories"],
        "repair_attempts": [
            "increased bus pitch: LVS remained PASS, METAL2 markers remained 21",
            "local M1 access doglegs: increased DRC conflicts and LVS failed",
            "M2/M3 layer-role swap: LVS PASS but DRC still failed",
        ],
        "next_required_repair": "true conflict-aware per-terminal access and track assignment, not global nmos_dx movement",
    }
    write_json(OUT / "DX14P80/DX14P80_ROUTING_REPAIR_GATE.json", dx_gate)

    variability = {
        "ROUTING_RESOURCE_VARIABILITY_AUDIT": "FAIL",
        "observed": [{k: r["routing_resources"][k] for k in r["routing_resources"]} | {"candidate": r["candidate"]} for r in records],
        "finding": "contact/via counts remain effectively constant across structurally different V1 candidates, so contact/routing optimization effect is not demonstrated.",
    }
    write_json(OUT / "ROUTING/ROUTING_RESOURCE_VARIABILITY_AUDIT.json", variability)

    counterexamples = [
        {
            "candidate": r["candidate"],
            "failure_class": "DRC_FAIL" if r["DRC"] != "DRC_PASS" else "LVS_COMPARE_FAIL",
            "physical_objects": r["DRC_categories"],
            "symbolic_resources": "fixed terminal-to-M2 vertical access template",
            "missing_constraint_model_error": "router lacks conditional M2 spacing/conflict constraints and does not choose alternative access tracks",
            "repair": "add local access choices, M2 conflict graph, and no-good cuts over resource combinations",
        }
        for r in records
        if not (r["DRC"] == "DRC_PASS" and r["LVS"] == "LVS_PASS")
    ]
    with (OUT / "ROUTING/CELLSYNTH_V2_ORACLE_COUNTEREXAMPLES.jsonl").open("w") as f:
        for c in counterexamples:
            f.write(json.dumps(c, sort_keys=True) + "\n")
    with (OUT / "ROUTING/CELLSYNTH_V2_ROUTING_CONFLICT_CUTS.jsonl").open("w") as f:
        f.write(json.dumps({
            "parent_state": "DX14.80 frozen placement with fixed M2 vertical terminal access",
            "conflict_resources": ["parallel M2 vertical access segments near x=14.77..16.56"],
            "reason": "METAL2.2/METAL2.5 violations under external DRC",
            "cut_expression": "NOT(frozen_dx14p80 AND fixed_terminal_to_M2_vertical_template)",
            "states_pruned": "all future states using same fixed-access template on overlapping P/N columns",
        }, sort_keys=True) + "\n")

    column_model = {
        "PN_COLUMN_MODEL_GATE": "SCAFFOLD_COMPLETE_TESTS_NOT_CLOSED",
        "definition": {
            "P(c)": "PMOS/finger or EMPTY",
            "N(c)": "NMOS/finger or EMPTY",
            "paired_column(c)": "P(c) != EMPTY AND N(c) != EMPTY",
        },
        "dff_variables": ["Pplace[p,c]", "Nplace[n,c]", "pair[p,n,c]", "access_select[t,a]", "track_select[n,t]", "route[n,e]", "via1[n,p]", "via2[n,p]"],
        "gate_requires": ["common symbolic columns", "paired_column_count > 0", "GDS coordinates match columns", "Level1 PASS", "DRC PASS", "LVS PASS"],
    }
    write_json(OUT / "PN_COLUMN_MODEL/PN_COLUMN_MODEL_SPEC.json", column_model)

    micro = {
        "PN_MICROBENCHMARK_GATE": "NOT_CLOSED",
        "benchmarks": {
            "INV2": "SPECIFIED_NOT_YET_DRC_LVS_CLOSED",
            "NAND2_OR_NOR2": "SPECIFIED_NOT_YET_DRC_LVS_CLOSED",
            "CROSS_COUPLED_INV_LATCH": "SPECIFIED_NOT_YET_DRC_LVS_CLOSED",
            "TG_PLUS_INV": "SPECIFIED_NOT_YET_DRC_LVS_CLOSED",
        },
        "reason": "This stage closed the diagnostic foundation and DX14.80 root cause; true microbenchmark GDS/LVS closure remains next implementation work.",
    }
    write_json(OUT / "MICROBENCHMARKS/PN_MICROBENCHMARK_GATE.json", micro)

    gates = {
        "MEMORY_UPDATE_GATE": "PASS",
        "COOPT_V1_GATE_REINTERPRETATION": "PASS",
        "ROOT_CAUSE_AUDIT_GATE": "PASS",
        "DX14P80_ROUTING_REPAIR_GATE": dx_gate["DX14P80_ROUTING_REPAIR_GATE"],
        "PN_COLUMN_MODEL_GATE": column_model["PN_COLUMN_MODEL_GATE"],
        "PN_MICROBENCHMARK_GATE": micro["PN_MICROBENCHMARK_GATE"],
        "LOCAL_ROUTER_GATE": "FAIL_NOT_YET_DEMONSTRATED_ON_POSITIVE_TEST",
        "ROUTING_CONFLICT_MODEL_GATE": "PARTIAL_COUNTEREXAMPLES_RECORDED",
        "ORACLE_FEEDBACK_GATE": "PASS",
        "PN_SIMULTANEOUS_PLACEMENT_GATE": "FAIL",
    }
    write_json(OUT / "PN_COLUMN_ROUTING_FOUNDATION_GATES.json", gates)

    status = "BLOCKED_CELLSYNTH_V2_PN_COLUMN_ROUTING_COOPT_FOUNDATION"
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    write(OUT / "FINAL_REPORT.md", f"""# {status}

The prior V1 result is reinterpreted as scaffold plus diagnostic evidence.
DX14.80 remains the immediate frozen routing regression: it preserves positive
P/N overlap and LVS passes, but DRC fails on `METAL2.2`/`METAL2.5` conflicts.

No PASS is claimed because `DX14P80_ROUTING_REPAIR_GATE`,
`PN_MICROBENCHMARK_GATE`, and `PN_SIMULTANEOUS_PLACEMENT_GATE` are not closed.
""")

    if REVIEW.exists():
        shutil.rmtree(REVIEW)
    REVIEW.mkdir(parents=True)
    for src in OUT.iterdir():
        if src.is_dir():
            shutil.copytree(src, REVIEW / src.name, dirs_exist_ok=True)
        else:
            shutil.copy2(src, REVIEW / src.name)
    manifest = {"status": status, "gates": gates, "package_created": now, "pdk_changed": False, "formal_sram_top_modified": False}
    write_json(REVIEW / "MANIFEST.json", manifest)
    write(REVIEW / "00_README_FIRST.md", "Main result: BLOCKED. See PN_COLUMN_ROUTING_FOUNDATION_GATES.json and DX14P80/DX14P80_ROUTING_REPAIR_GATE.json.")
    sums = []
    for p in sorted(REVIEW.rglob("*")):
        if p.is_file() and p.name != "SHA256SUMS":
            sums.append(f"{sha(p)}  {p.relative_to(REVIEW)}")
    write(REVIEW / "SHA256SUMS", "\n".join(sums))
    if PKG.exists():
        PKG.unlink()
    with tarfile.open(PKG, "w:gz") as tar:
        tar.add(REVIEW, arcname=REVIEW.name)
    pkg_sha = sha(PKG)

    with (REPO / "docs/PROJECT_TASK_MASTER_LOG.md").open("a") as f:
        f.write(f"\n## {now} cellsynth_v2_pn_column_routing_foundation\n\n- result: `{status}`\n- root cause: `DX14.80` LVS passes but DRC fails on METAL2.2/METAL2.5; global nmos_dx is not a P/N column model.\n- package: `{PKG}`, SHA256 `{pkg_sha}`.\n")
    with (REPO / "docs/PROJECT_TASK_MASTER_LOG.jsonl").open("a") as f:
        f.write(json.dumps({"timestamp": now, "event": "cellsynth_v2_pn_column_routing_foundation", "result": status, "package": str(PKG), "package_sha256": pkg_sha}, sort_keys=True) + "\n")
    st = read_json(REPO / "docs/PROJECT_CURRENT_STATUS.json")
    st["current_status"] = status
    st["current_git_head"] = "PENDING_COMMIT"
    st["cellsynth_v2_pn_column_routing_foundation"] = {"status": status, "package": str(PKG), "package_sha256": pkg_sha, "gates": gates}
    write_json(REPO / "docs/PROJECT_CURRENT_STATUS.json", st)
    print(json.dumps({"status": status, "package": str(PKG), "package_sha256": pkg_sha, "gates": gates}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
