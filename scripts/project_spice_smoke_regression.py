from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.clean_top_export import parse_spice_text, parse_subckt_instances  # noqa: E402


DOCS_DIR = REPO_ROOT / "docs"
SIM_ROOT = REPO_ROOT / "simulation"
SPICE_DIR = SIM_ROOT / "spice"
TB_DIR = SPICE_DIR / "testbenches"
LOG_DIR = SPICE_DIR / "logs"
NETLIST_DIR = SPICE_DIR / "netlists"
TOP_NETLIST = REPO_ROOT / "outputs/M12N2_clean_openyield_sram_top/current_supported_config/openyield_sram_top_v1_16x16.sp"


@dataclass
class SpiceCase:
    name: str
    module: str
    check_kind: str
    note: str


CASES = [
    SpiceCase("pnand2_inversion", "PNAND2", "invert", "A=1,B=1 should drive Z low"),
    SpiceCase("pnand3_inversion", "PNAND3", "invert3", "A=B=C=1 should drive Z low"),
    SpiceCase("and2_truth", "AND2", "and2", "A=1,B=1 should drive Z high"),
    SpiceCase("and3_truth", "AND3", "and3", "A=B=C=1 should drive Z high"),
    SpiceCase("pdrive_buffer", "pdrive", "buffer", "buffer output should follow input"),
    SpiceCase("wl_pdrive_buffer", "wl_pdrive", "buffer", "WL driver output should follow input"),
    SpiceCase("pdrive2_for_pre_buffer", "pdrive2_for_pre", "buffer", "precharge buffer output should follow input"),
    SpiceCase("delay_chain_polarity", "delay_chain", "delay_invert", "delay chain is a 9-stage loaded inverter chain and should invert after propagation"),
    SpiceCase("dff_capture", "DFF", "dff", "Q should capture D on clock edges"),
    SpiceCase("dff_buf_capture", "DFF_BUF", "dff_buf", "Q/QB should capture complementary state"),
]


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def render_subckt_bundle(parsed, top_name: str) -> str:
    by_name: dict[str, Any] = {}
    for subckt in parsed.subckts:
        by_name.setdefault(subckt.name, subckt)

    ordered: list[str] = []
    visited: set[str] = set()

    def visit(name: str) -> None:
        if name in visited:
            return
        visited.add(name)
        subckt = by_name.get(name)
        if subckt is None:
            return
        for inst in parse_subckt_instances(subckt):
            if inst.instance_type == "X":
                visit(inst.module_name)
        ordered.append(name)

    visit(top_name)
    lines = []
    for include in parsed.includes:
        if "models_tt.spice" in include.lower():
            lines.append(include)
    for name in ordered:
        subckt = by_name[name]
        lines.append("")
        lines.append(".subckt " + " ".join([subckt.name, *subckt.pins]))
        lines.extend(subckt.body_lines)
        lines.append(f".ends {subckt.name}")
    return "\n".join(lines).strip() + "\n"


def build_tb(case: SpiceCase) -> str:
    if case.check_kind == "invert":
        body = """
VVDD VDD 0 1.0
VVSS VSS 0 0
VA A 0 1.0
VB B 0 1.0
XDUT VDD VSS A B Z PNAND2
.tran 2p 400p
.measure tran z_final FIND v(Z) AT=350p
.measure tran z_max MAX v(Z)
.measure tran z_min MIN v(Z)
"""
    elif case.check_kind == "invert3":
        body = """
VVDD VDD 0 1.0
VVSS VSS 0 0
VA A 0 1.0
VB B 0 1.0
VC C 0 1.0
XDUT VDD VSS A B C Z PNAND3
.tran 2p 400p
.measure tran z_final FIND v(Z) AT=350p
.measure tran z_max MAX v(Z)
.measure tran z_min MIN v(Z)
"""
    elif case.check_kind == "and2":
        body = """
VVDD VDD 0 1.0
VVSS VSS 0 0
VA A 0 1.0
VB B 0 1.0
XDUT VDD VSS A B Z AND2
.tran 2p 400p
.measure tran z_final FIND v(Z) AT=350p
.measure tran z_max MAX v(Z)
.measure tran z_min MIN v(Z)
"""
    elif case.check_kind == "and3":
        body = """
VVDD VDD 0 1.0
VVSS VSS 0 0
VA A 0 1.0
VB B 0 1.0
VC C 0 1.0
XDUT VDD VSS A B C Z AND3
.tran 2p 400p
.measure tran z_final FIND v(Z) AT=350p
.measure tran z_max MAX v(Z)
.measure tran z_min MIN v(Z)
"""
    elif case.check_kind == "buffer":
        subckt = case.module
        body = f"""
VVDD VDD 0 1.0
VVSS VSS 0 0
VA A 0 PULSE(0 1.0 40p 5p 5p 120p 240p)
XDUT VDD VSS A Z {subckt}
.tran 2p 500p
.measure tran z_low MIN v(Z) FROM=0p TO=180p
.measure tran z_high MAX v(Z) FROM=250p TO=460p
"""
    elif case.check_kind == "delay_invert":
        body = """
VVDD VDD 0 1.0
VVSS VSS 0 0
VA A 0 PULSE(0 1.0 40p 5p 5p 120p 240p)
XDUT VDD VSS A Z delay_chain
.tran 1p 700p
.measure tran t_in_rise WHEN v(A)=0.5 RISE=1
.measure tran t_out_fall WHEN v(Z)=0.5 FALL=1
.measure tran tpd_rise_fall PARAM='t_out_fall-t_in_rise'
.measure tran t_in_fall WHEN v(A)=0.5 FALL=1
.measure tran t_out_rise WHEN v(Z)=0.5 RISE=1
.measure tran tpd_fall_rise PARAM='t_out_rise-t_in_fall'
.measure tran z_after_first_rise FIND v(Z) AT=300p
.measure tran z_after_first_fall FIND v(Z) AT=430p
.measure tran z_min MIN v(Z) FROM=0p TO=700p
.measure tran z_max MAX v(Z) FROM=0p TO=700p
"""
    elif case.check_kind == "dff":
        body = """
VVDD VDD 0 1.0
VVSS VSS 0 0
VCLK CLK 0 PULSE(0 1.0 20p 5p 5p 80p 160p)
VD D 0 PWL(0p 0 70p 0 90p 1.0 230p 1.0 250p 0)
XDUT VDD VSS D Q CLK DFF
.tran 2p 420p
.measure tran q_first FIND v(Q) AT=150p
.measure tran q_second FIND v(Q) AT=310p
"""
    elif case.check_kind == "dff_buf":
        body = """
VVDD VDD 0 1.0
VVSS VSS 0 0
VCLK CLK 0 PULSE(0 1.0 20p 5p 5p 80p 160p)
VD D 0 PWL(0p 0 70p 0 90p 1.0 230p 1.0 250p 0)
XDUT VDD VSS D Q QB CLK DFF_BUF
.tran 2p 420p
.measure tran q_first FIND v(Q) AT=150p
.measure tran qb_first FIND v(QB) AT=150p
.measure tran q_second FIND v(Q) AT=310p
.measure tran qb_second FIND v(QB) AT=310p
"""
    else:
        raise ValueError(case.check_kind)
    return f".title {case.name}\n{body}\n.end\n"


def parse_measures(log_text: str) -> dict[str, float]:
    values: dict[str, float] = {}
    for line in log_text.splitlines():
        match = re.search(r"^\s*([A-Za-z0-9_]+)\s*=\s*([-+0-9.eE]+)", line)
        if match:
            try:
                values[match.group(1)] = float(match.group(2))
            except ValueError:
                pass
    return values


def evaluate(case: SpiceCase, measures: dict[str, float]) -> tuple[bool, str]:
    if case.check_kind == "invert":
        ok = measures.get("z_final", 1.0) < 0.2
        return ok, f"z_final={measures.get('z_final')}"
    if case.check_kind == "invert3":
        ok = measures.get("z_final", 1.0) < 0.2
        return ok, f"z_final={measures.get('z_final')}"
    if case.check_kind in {"and2", "and3"}:
        ok = measures.get("z_final", 0.0) > 0.8
        return ok, f"z_final={measures.get('z_final')}"
    if case.check_kind == "buffer":
        ok = measures.get("z_low", 1.0) < 0.2 and measures.get("z_high", 0.0) > 0.8
        return ok, f"z_low={measures.get('z_low')} z_high={measures.get('z_high')}"
    if case.check_kind == "delay_invert":
        tpd_rise_fall = measures.get("tpd_rise_fall")
        tpd_fall_rise = measures.get("tpd_fall_rise")
        ok = (
            measures.get("z_after_first_rise", 1.0) < 0.2
            and measures.get("z_after_first_fall", 0.0) > 0.8
            and tpd_rise_fall is not None
            and tpd_fall_rise is not None
            and tpd_rise_fall > 0.0
            and tpd_fall_rise > 0.0
        )
        return ok, (
            f"z_after_first_rise={measures.get('z_after_first_rise')} "
            f"z_after_first_fall={measures.get('z_after_first_fall')} "
            f"tpd_rise_fall={tpd_rise_fall} tpd_fall_rise={tpd_fall_rise}"
        )
    if case.check_kind == "dff":
        ok = measures.get("q_first", 1.0) < 0.2 and measures.get("q_second", 0.0) > 0.8
        return ok, f"q_first={measures.get('q_first')} q_second={measures.get('q_second')}"
    if case.check_kind == "dff_buf":
        ok = (
            measures.get("q_first", 1.0) < 0.2
            and measures.get("qb_first", 0.0) > 0.8
            and measures.get("q_second", 0.0) > 0.8
            and measures.get("qb_second", 1.0) < 0.2
        )
        return ok, (
            f"q_first={measures.get('q_first')} qb_first={measures.get('qb_first')} "
            f"q_second={measures.get('q_second')} qb_second={measures.get('qb_second')}"
        )
    return False, "unsupported check"


def main() -> None:
    TB_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    NETLIST_DIR.mkdir(parents=True, exist_ok=True)

    parsed = parse_spice_text(TOP_NETLIST.read_text(encoding="utf-8"))
    by_name = {subckt.name: subckt for subckt in parsed.subckts}

    rows: list[dict[str, Any]] = []
    blockers: list[str] = []

    for case in CASES:
        if case.module not in by_name:
            rows.append(
                {
                    "level": "SPICE",
                    "test_id": case.name,
                    "target": case.module,
                    "tool": "ngspice",
                    "status": "BLOCKED",
                    "artifact": "",
                    "notes": "subckt not found in authoritative clean-top netlist",
                }
            )
            blockers.append(f"{case.module}: subckt not present in authoritative clean-top netlist")
            continue

        bundle_path = NETLIST_DIR / f"{case.module}.inc"
        tb_path = TB_DIR / f"{case.name}.sp"
        log_path = LOG_DIR / f"{case.name}.log"
        write_text(bundle_path, render_subckt_bundle(parsed, case.module))
        write_text(tb_path, f'.include "{bundle_path}"\n' + build_tb(case))

        proc = subprocess.run(
            ["ngspice", "-b", "-o", str(log_path), str(tb_path)],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        log_text = ""
        if log_path.exists():
            log_text = log_path.read_text(encoding="utf-8", errors="replace")
        else:
            log_text = (proc.stdout or "") + (proc.stderr or "")
        measures = parse_measures(log_text)
        passed, note = evaluate(case, measures) if proc.returncode == 0 else (False, f"ngspice rc={proc.returncode}")
        rows.append(
            {
                "level": "SPICE",
                "test_id": case.name,
                "target": case.module,
                "tool": "ngspice",
                "status": "PASS" if passed else "FAIL",
                "artifact": str(log_path.relative_to(REPO_ROOT)) if log_path.exists() else "",
                "notes": note,
            }
        )

    logic_blocker = (
        "Level 1 digital logic regression is asset-blocked: current project audit found no authoritative `.v/.sv` files for the requested control modules."
    )
    top_level_blocker = (
        "Level 2 representative SRAM functional simulation remains blocked by lack of a reviewed standalone SRAM functional testbench and unresolved TIME-role ambiguity in OpenYield clean-top evidence."
    )
    post_layout_blocker = (
        "Post-layout simulation remains NOT_AVAILABLE_WITH_CURRENT_EVIDENCE because current repo lacks refreshed extraction-rule provenance and fresh LVS/PEX binding for a new regression loop."
    )
    blockers.extend([logic_blocker, top_level_blocker, post_layout_blocker])

    results = {
        "generated_at": "2026-07-30",
        "spice_source_netlist": str(TOP_NETLIST.relative_to(REPO_ROOT)),
        "tool_used": "ngspice",
        "test_rows": rows,
        "blockers": blockers,
    }
    write_json(SPICE_DIR / "spice_regression_results.json", results)

    with (DOCS_DIR / "SIMULATION_TEST_MATRIX.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["level", "test_id", "target", "tool", "status", "artifact", "notes"])
        writer.writeheader()
        writer.writerows(rows)

    summary_lines = [
        "# Simulation Results Summary",
        "",
        f"- source_netlist: `{TOP_NETLIST.relative_to(REPO_ROOT)}`",
        "- formal_spice_basis: `authoritative clean-top extracted netlist`, not planning-only candidate SPICE",
        "",
        "## Level 3 SPICE Results",
        "",
    ]
    for row in rows:
        summary_lines.append(f"- {row['test_id']} / {row['target']}: `{row['status']}` | {row['notes']}")
    write_text(DOCS_DIR / "SIMULATION_RESULTS_SUMMARY.md", "\n".join(summary_lines) + "\n")

    audit_lines = [
        "# Simulation Capability Audit",
        "",
        "- logic_level_1_status: `BLOCKED_BY_MISSING_TRUSTED_VERILOG_ASSETS`",
        "- sram_function_level_2_status: `BLOCKED_BY_MISSING_REVIEWED_FUNCTIONAL_TESTBENCH_AND_TIME_ROLE_AMBIGUITY`",
        "- spice_level_3_status: `ADVANCED_WITH_REAL_SERVER_EVIDENCE`",
        "- spice_primary: `ngspice`",
        "- spice_secondary_candidate: `Xyce`",
        "- post_layout_status: `NOT_AVAILABLE_WITH_CURRENT_EVIDENCE`",
        "",
        "## Notes",
        "",
        "- Current SPICE regressions are grounded on `outputs/M12N2_clean_openyield_sram_top/current_supported_config/openyield_sram_top_v1_16x16.sp`.",
        "- `docs/candidate_spice/*` was not used for formal pass/fail evidence.",
        "- Current logic-level closure is blocked by missing trusted Verilog assets, not by simulator availability.",
    ]
    write_text(DOCS_DIR / "SIMULATION_CAPABILITY_AUDIT.md", "\n".join(audit_lines) + "\n")
    write_text(
        DOCS_DIR / "SIMULATION_BLOCKERS.md",
        "# Simulation Blockers\n\n" + "\n".join(f"- {item}" for item in blockers) + "\n",
    )


if __name__ == "__main__":
    main()
