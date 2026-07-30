from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = REPO_ROOT / "docs"
EXTERNAL_OPENYIELD = Path("/data1/qujh/work/external/OpenYield")
TARGET_DIRS = [REPO_ROOT, EXTERNAL_OPENYIELD]


@dataclass
class ToolSpec:
    tool: str
    absolute_path: str
    version: str
    license_required: bool
    license_detected: bool
    smoke_test: str
    usable: bool
    recommended_role: str
    limitations: str


TOOL_PATH_SPECS = [
    "ngspice",
    "Xyce",
    "xyce",
    "iverilog",
    "vvp",
    "verilator",
    "vcs",
    "simv",
    "xrun",
    "irun",
    "ncsim",
    "vsim",
    "vlog",
    "vlib",
    "hspice",
    "spectre",
    "aps",
    "gtkwave",
    "klayout",
    "magic",
    "netgen",
    "yosys",
    "openroad",
    "python3",
    "make",
    "cmake",
    "gcc",
    "g++",
]

ABSOLUTE_TOOL_CANDIDATES = {
    "Xyce": ["/usr/local/xyce_parallel/bin/Xyce", "/data1/qujh/.conda/envs/openyield/bin/Xyce"],
    "verilator": ["/opt/pdk_klayout_openroad/oss-cad-suite/bin/verilator"],
    "iverilog": ["/opt/pdk_klayout_openroad/oss-cad-suite/bin/iverilog"],
    "vvp": ["/opt/pdk_klayout_openroad/oss-cad-suite/bin/vvp"],
    "ngspice": ["/data1/qujh/.conda/envs/openyield/bin/ngspice"],
}

VERSION_COMMANDS = {
    "ngspice": [["ngspice", "--version"]],
    "Xyce": [["Xyce", "-v"], ["Xyce", "-version"]],
    "xyce": [["xyce", "-v"], ["xyce", "-version"]],
    "iverilog": [["iverilog", "-V"]],
    "vvp": [["vvp", "-V"]],
    "verilator": [["verilator", "--version"]],
    "vcs": [["vcs", "-ID"]],
    "xrun": [["xrun", "-version"]],
    "vsim": [["vsim", "-version"]],
    "hspice": [["hspice", "-v"]],
    "spectre": [["spectre", "-W"]],
    "klayout": [["klayout", "-v"]],
    "magic": [["magic", "--version"]],
    "netgen": [["netgen", "-batch", "version"]],
    "yosys": [["yosys", "-V"]],
    "openroad": [["openroad", "-version"]],
    "gtkwave": [["gtkwave", "--version"]],
    "python3": [["python3", "--version"]],
    "make": [["make", "--version"]],
    "cmake": [["cmake", "--version"]],
    "gcc": [["gcc", "--version"]],
    "g++": [["g++", "--version"]],
}

COMMERCIAL_TOOLS = {"vcs", "simv", "xrun", "irun", "ncsim", "vsim", "vlog", "vlib", "hspice", "spectre", "aps"}
GUI_TOOLS = {"gtkwave", "klayout", "magic"}


def run_command(argv: list[str], env: dict[str, str] | None = None) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            argv,
            cwd=REPO_ROOT,
            env=env,
            text=True,
            capture_output=True,
            timeout=20,
            check=False,
        )
    except FileNotFoundError as exc:
        return 127, str(exc)
    except subprocess.TimeoutExpired:
        return 124, "timeout"
    text = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, text.strip()


def resolve_tool_path(tool: str) -> str:
    path = shutil.which(tool)
    if path:
        return path
    for candidate in ABSOLUTE_TOOL_CANDIDATES.get(tool, []):
        if Path(candidate).exists():
            return candidate
    return ""


def resolve_invocation(path: str, tool: str, cmd: list[str]) -> list[str]:
    if not path:
        return cmd
    argv = cmd[:]
    if argv and argv[0] in {tool, tool.lower(), tool.upper()}:
        argv[0] = path
    return argv


def tool_role(tool: str, usable: bool) -> str:
    if not usable:
        return "not_usable"
    mapping = {
        "ngspice": "primary transistor-level spice smoke and regression",
        "Xyce": "secondary spice cross-check and large-netlist simulation",
        "iverilog": "preferred digital logic regression if trusted Verilog appears",
        "vvp": "Icarus runtime for digital logic regression",
        "verilator": "secondary digital lint / fast compile if trusted Verilog appears",
        "klayout": "layout viewing and possible DRC/LVS/manual inspection",
        "magic": "layout viewing / open-source extraction candidate",
        "netgen": "open-source LVS candidate if decks are available",
        "gtkwave": "waveform viewer (GUI required)",
        "yosys": "netlist inspection / synthesis experiments",
        "openroad": "digital PnR experiments only",
    }
    return mapping.get(tool, "general utility")


def tool_limitations(tool: str, usable: bool, output: str) -> str:
    bits: list[str] = []
    if not usable:
        bits.append("not found or version probe failed")
    if tool in COMMERCIAL_TOOLS:
        bits.append("likely license-gated commercial tool")
    if tool in GUI_TOOLS and ("display" in output.lower() or "authorization required" in output.lower()):
        bits.append("GUI/X11 unavailable in current shell")
    if tool == "gtkwave":
        bits.append("viewer only; current shell lacks DISPLAY")
    if tool == "iverilog":
        bits.append("no trusted Verilog assets discovered in current project audit")
    if tool == "verilator":
        bits.append("not on PATH; only discoverable via absolute install path")
    if tool == "magic":
        bits.append("no project-specific extraction/LVS deck provenance confirmed yet")
    if tool == "netgen":
        bits.append("no project-specific LVS rule deck provenance confirmed yet")
    return "; ".join(bits)


def detect_license(tool: str) -> bool:
    env = os.environ
    if tool in COMMERCIAL_TOOLS:
        patterns = ["LICENSE", "LM_LICENSE", "CDS", "SYNOPSYS", "MENTOR", "QUESTA", "VCS", "HSPICE", "SPECTRE"]
    else:
        patterns = ["XYCE", "NGSPICE", "OPENRAM", "PDK"]
    return any(any(pat in key.upper() for pat in patterns) for key in env)


def probe_tool(tool: str) -> ToolSpec:
    path = resolve_tool_path(tool)
    commands = VERSION_COMMANDS.get(tool, [[tool, "--version"]])
    outputs: list[str] = []
    smoke = "not_run"
    version = ""
    usable = False
    for cmd in commands:
        rc, out = run_command(resolve_invocation(path, tool, cmd))
        outputs.append(f"$ {' '.join(resolve_invocation(path, tool, cmd))}\n{out}".strip())
        if not version and out:
            version = out.splitlines()[0].strip()
        if rc == 0:
            smoke = f"version probe passed via {' '.join(cmd[1:]) or cmd[0]}"
            usable = True
            break
    if not outputs:
        outputs = ["not found"]
    combined = "\n".join(outputs)
    if not path:
        smoke = "not found on PATH or known absolute locations"
        version = ""
    return ToolSpec(
        tool=tool,
        absolute_path=path,
        version=version,
        license_required=tool in COMMERCIAL_TOOLS,
        license_detected=detect_license(tool),
        smoke_test=smoke,
        usable=usable and bool(path),
        recommended_role=tool_role(tool, usable and bool(path)),
        limitations=tool_limitations(tool, usable and bool(path), combined),
    )


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def classify_asset(path: Path) -> str:
    name = path.name.lower()
    suffix = path.suffix.lower()
    if suffix in {".v", ".sv", ".vh"}:
        return "STRUCTURAL_VERILOG" if "golden" in str(path).lower() else "RTL_OR_BEHAVIORAL_NETLIST"
    if suffix in {".sp", ".spi", ".spice", ".cir", ".ckt"}:
        if "candidate_spice" in path.parts:
            return "UNKNOWN"
        if "full_layout_collection" in str(path) or "extracted" in str(path):
            return "EXTRACTED_SPICE"
        return "TRANSISTOR_SPICE"
    if suffix in {".lib", ".model", ".scs"}:
        return "DEVICE_MODEL"
    if "testbench" in name or "_tb" in name or name.startswith("tb_"):
        return "TESTBENCH"
    if suffix in {".raw", ".vcd", ".fst"}:
        return "REFERENCE_RESULT"
    return "UNKNOWN"


def infer_supported_simulator(path: Path) -> str:
    text = str(path).lower()
    if path.suffix.lower() == ".scs":
        return "spectre"
    if "hspice" in text:
        return "hspice/ngspice"
    if path.suffix.lower() in {".sp", ".spi", ".spice", ".cir", ".ckt"}:
        return "ngspice/xyce"
    if path.suffix.lower() in {".v", ".sv"}:
        return "iverilog/verilator"
    return "unknown"


def infer_corner(path: Path) -> str:
    name = path.name.upper()
    for token in ("TT", "FF", "SS", "FS", "SF", "NOM"):
        if token in name:
            return token
    return ""


def infer_voltage(path: Path) -> str:
    name = path.name.lower()
    match = re.search(r"(\d+)p(\d+)v", name)
    if match:
        return f"{match.group(1)}.{match.group(2)}V"
    if "freepdk45" in name or "models_tt" in name:
        return "1.0V_assumed_from_filename_context"
    return ""


def infer_temperature(path: Path) -> str:
    name = path.name.lower()
    match = re.search(r"(-?\d+)c", name)
    if match:
        return f"{match.group(1)}C"
    if "25c" in name:
        return "25C"
    return ""


def infer_provenance(path: Path) -> str:
    text = str(path)
    if text.startswith(str(REPO_ROOT)):
        return "project_repo"
    if text.startswith(str(EXTERNAL_OPENYIELD)):
        return "external_openyield"
    if "freepdk45" in text.lower():
        return "freepdk45_related_external"
    return "other_server_path"


def find_assets() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[Path] = set()
    for base in TARGET_DIRS:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            if path in seen:
                continue
            if path.suffix.lower() not in {".v", ".sv", ".vh", ".sp", ".spi", ".spice", ".cir", ".ckt", ".lib", ".model", ".scs", ".raw", ".vcd", ".fst"} and "testbench" not in path.name.lower() and "_tb" not in path.name.lower():
                continue
            seen.add(path)
            asset_type = classify_asset(path)
            rows.append(
                {
                    "asset_type": asset_type,
                    "source_path": str(path),
                    "file_sha256": sha256_file(path),
                    "model_type": "device_model" if asset_type == "DEVICE_MODEL" else "",
                    "supported_simulator": infer_supported_simulator(path),
                    "corner": infer_corner(path),
                    "temperature": infer_temperature(path),
                    "voltage": infer_voltage(path),
                    "license_provenance": infer_provenance(path),
                }
            )
    rows.sort(key=lambda row: (row["asset_type"], row["source_path"]))
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_tool_audit_md(tool_rows: list[ToolSpec]) -> str:
    lines = [
        "# Server Simulator Capability Audit",
        "",
        "- audit_scope: `PATH tools`, `known absolute tool installs`, `version probes only`, `no package installation`",
        "- current_server_date: `2026-07-30`",
        "",
        "## Tool Summary",
        "",
        "| tool | usable | path | version | role | limitations |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in tool_rows:
        lines.append(
            f"| {row.tool} | {row.usable} | {row.absolute_path or '-'} | {row.version or '-'} | {row.recommended_role} | {row.limitations or '-'} |"
        )
    lines.extend(
        [
            "",
            "## Conclusions",
            "",
            "- `ngspice` is the only clearly usable open-source primary SPICE engine already on `PATH`.",
            "- `Xyce` is usable from `/usr/local/xyce_parallel/bin/Xyce` and is already active in other users' jobs; treat it as a secondary cross-check engine.",
            "- `iverilog`/`vvp` are usable, but no trusted project Verilog assets were discovered in this audit, so digital regressions are asset-blocked rather than tool-blocked.",
            "- `verilator` exists only in an absolute install path and is suitable as a secondary lint/compile engine if trusted Verilog is added later.",
            "- `gtkwave` requires GUI/X11 and is not usable in the current headless shell.",
            "- `magic` and `klayout` are available, but no current-project extraction/LVS rule provenance was found that would justify claiming post-layout extraction closure.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_asset_gap_md(asset_rows: list[dict[str, Any]]) -> str:
    counts: dict[str, int] = {}
    for row in asset_rows:
        counts[row["asset_type"]] = counts.get(row["asset_type"], 0) + 1
    trusted_verilog = [row for row in asset_rows if row["asset_type"] in {"RTL_OR_BEHAVIORAL_NETLIST", "STRUCTURAL_VERILOG"}]
    lines = [
        "# Simulation Input Gap Report",
        "",
        "## Inventory Counts",
        "",
    ]
    for key in sorted(counts):
        lines.append(f"- {key}: `{counts[key]}`")
    lines.extend(
        [
            "",
            "## Gaps",
            "",
            f"- Trusted Verilog assets discovered: `{len(trusted_verilog)}`. Current project worktree does not contain authoritative `.v/.sv` sources for the target control modules, so Icarus/Verilator logic regressions are asset-blocked.",
            "- `docs/candidate_spice/*` exists but is explicitly labeled planning-only and is excluded from formal simulation claims.",
            "- `outputs/M12N2_clean_openyield_sram_top/*` and `outputs/M12N_lock_openyield_authoritative_netlist/*` provide authoritative/generated SPICE sources suitable for limited SPICE regressions.",
            "- `outputs/M7_correct_golden_reference/current_supported_config/extracted/full_layout_collection/*/*.sp` provides extracted SRAM-level SPICE and report collateral, but current repo still lacks a documented extraction-rule provenance chain that would justify new post-layout signoff claims.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_tool_selection(tool_rows: list[ToolSpec], asset_rows: list[dict[str, Any]]) -> dict[str, Any]:
    usable = {row.tool: row for row in tool_rows if row.usable}
    verilog_assets = [row for row in asset_rows if row["asset_type"] in {"RTL_OR_BEHAVIORAL_NETLIST", "STRUCTURAL_VERILOG"}]
    has_trusted_verilog = len(verilog_assets) > 0
    logic_primary = "iverilog+vvp" if "iverilog" in usable and "vvp" in usable and has_trusted_verilog else "NOT_AVAILABLE_WITH_CURRENT_EVIDENCE"
    logic_secondary = "verilator" if resolve_tool_path("verilator") and has_trusted_verilog else "NOT_AVAILABLE_WITH_CURRENT_EVIDENCE"
    spice_primary = "ngspice" if "ngspice" in usable else "NOT_AVAILABLE_WITH_CURRENT_EVIDENCE"
    spice_secondary = "Xyce" if "Xyce" in usable else "NOT_AVAILABLE_WITH_CURRENT_EVIDENCE"
    waveform_viewer = "gtkwave" if "gtkwave" in usable else "NOT_AVAILABLE_WITH_CURRENT_EVIDENCE"
    post_layout_extractor = "NOT_AVAILABLE_WITH_CURRENT_EVIDENCE"
    server_evidence = {
        "usable_tools": sorted(usable),
        "trusted_verilog_asset_count": len(verilog_assets),
        "authoritative_clean_spice_present": any("openyield_sram_top_v1_16x16.sp" in row["source_path"] for row in asset_rows),
        "extracted_spice_asset_count": sum(1 for row in asset_rows if row["asset_type"] == "EXTRACTED_SPICE"),
    }
    blocking = []
    if not has_trusted_verilog:
        blocking.append("No authoritative project Verilog assets for PNAND2/PNAND3/AND2/AND3/DFF/DFF_BUF/control modules were discovered.")
    blocking.append("No current-project post-layout extraction-rule provenance was discovered; pre-layout or historical extracted SPICE must not be relabeled as fresh post-layout simulation.")
    return {
        "logic_primary": logic_primary,
        "logic_secondary": logic_secondary,
        "spice_primary": spice_primary,
        "spice_secondary": spice_secondary,
        "post_layout_extractor": post_layout_extractor,
        "waveform_viewer": waveform_viewer,
        "selection_reason": {
            "logic": "Prefer Icarus only when trusted Verilog exists; current server has Icarus but current project evidence does not.",
            "spice": "Use ngspice as primary because it is available on PATH and matches existing project smoke conventions; use Xyce as secondary cross-check.",
            "post_layout": "Do not claim a post-layout extractor until extraction-rule provenance, layout-netlist binding, and LVS/PEX evidence are all refreshed.",
        },
        "server_evidence": server_evidence,
        "blocking_dependencies": blocking,
    }


def build_selection_md(selection: dict[str, Any]) -> str:
    lines = [
        "# Project Simulation Tool Selection",
        "",
        f"- logic_primary: `{selection['logic_primary']}`",
        f"- logic_secondary: `{selection['logic_secondary']}`",
        f"- spice_primary: `{selection['spice_primary']}`",
        f"- spice_secondary: `{selection['spice_secondary']}`",
        f"- post_layout_extractor: `{selection['post_layout_extractor']}`",
        f"- waveform_viewer: `{selection['waveform_viewer']}`",
        "",
        "## Selection Reason",
        "",
        f"- logic: {selection['selection_reason']['logic']}",
        f"- spice: {selection['selection_reason']['spice']}",
        f"- post_layout: {selection['selection_reason']['post_layout']}",
        "",
        "## Blocking Dependencies",
        "",
    ]
    for item in selection["blocking_dependencies"]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def main() -> None:
    tool_rows = [probe_tool(tool) for tool in TOOL_PATH_SPECS]
    asset_rows = find_assets()
    selection = build_tool_selection(tool_rows, asset_rows)

    tool_dict_rows = [asdict(row) for row in tool_rows]
    write_csv(
        DOCS_DIR / "SERVER_EDA_TOOL_INVENTORY.csv",
        tool_dict_rows,
        [
            "tool",
            "absolute_path",
            "version",
            "license_required",
            "license_detected",
            "smoke_test",
            "usable",
            "recommended_role",
            "limitations",
        ],
    )
    write_json(DOCS_DIR / "SERVER_EDA_TOOL_INVENTORY.json", tool_dict_rows)
    write_text(DOCS_DIR / "SERVER_SIMULATOR_CAPABILITY_AUDIT.md", build_tool_audit_md(tool_rows))

    write_csv(
        DOCS_DIR / "SIMULATION_INPUT_ASSET_INVENTORY.csv",
        asset_rows,
        [
            "asset_type",
            "source_path",
            "file_sha256",
            "model_type",
            "supported_simulator",
            "corner",
            "temperature",
            "voltage",
            "license_provenance",
        ],
    )
    write_json(DOCS_DIR / "SIMULATION_INPUT_ASSET_INVENTORY.json", asset_rows)
    write_text(DOCS_DIR / "SIMULATION_INPUT_GAP_REPORT.md", build_asset_gap_md(asset_rows))

    write_json(DOCS_DIR / "PROJECT_SIMULATION_TOOL_SELECTION.json", selection)
    write_text(DOCS_DIR / "PROJECT_SIMULATION_TOOL_SELECTION.md", build_selection_md(selection))


if __name__ == "__main__":
    main()
