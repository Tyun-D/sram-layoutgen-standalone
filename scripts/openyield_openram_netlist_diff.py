from __future__ import annotations

import ast
import csv
import json
import re
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
STANDALONE_ROOT = REPO_ROOT / "deliverables" / "sram_layoutgen_standalone"
OPENYIELD_ROOT = REPO_ROOT / "third_party" / "OpenYield"
DOCS_DIR = STANDALONE_ROOT / "docs"

NETLIST_EXTS = {".sp", ".spi", ".spice", ".cdl", ".v", ".sv"}
OPENYIELD_SUBCIRCUIT_DIR = OPENYIELD_ROOT / "sram_compiler" / "subcircuits"
OPENYIELD_TESTBENCH_DIR = OPENYIELD_ROOT / "sram_compiler" / "testbenches"


@dataclass
class Subckt:
    name: str
    ports: list[str]
    instances: list[dict[str, Any]] = field(default_factory=list)
    mos_count: int = 0
    source_file: str = ""

    @property
    def instance_types(self) -> Counter:
        return Counter(item["type"] for item in self.instances if item.get("type"))


def rel(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_text(path: Path) -> str:
    for enc in ("utf-8-sig", "utf-8", "gb18030", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def run_git(args: list[str], cwd: Path) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=str(cwd), text=True, encoding="utf-8", stderr=subprocess.STDOUT).strip()
    except Exception as exc:
        return str(exc).strip()


def scan_netlist_candidates() -> list[dict[str, Any]]:
    candidates = []
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        if path.suffix.lower() not in NETLIST_EXTS:
            continue
        r = rel(path)
        lower = r.lower()
        group = "other"
        if "third_party/openyield" in lower:
            group = "openyield"
        elif "openram" in lower or "compiler/tests/golden" in lower or "compiler/tests/sp_files" in lower:
            group = "openram"
        elif "sram_layoutgen_standalone" in lower:
            group = "current_layoutgen"
        score = 0
        for word, weight in {
            "sram": 5,
            "openram": 5,
            "freepdk45": 4,
            "2x16": 3,
            "16x16": 2,
            "model": -2,
            "tran_models": -3,
            "sp_lib": -2,
            "test": -1,
        }.items():
            if word in lower:
                score += weight
        candidates.append(
            {
                "path": r,
                "absolute_path": str(path.resolve()),
                "group": group,
                "extension": path.suffix.lower(),
                "size_bytes": path.stat().st_size,
                "score": score,
            }
        )
    return sorted(candidates, key=lambda x: (x["group"], -x["score"], x["path"]))


def logical_lines(text: str) -> list[str]:
    out: list[str] = []
    current = ""
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("*"):
            continue
        if line.startswith("+"):
            current += " " + line[1:].strip()
        else:
            if current:
                out.append(current)
            current = line
    if current:
        out.append(current)
    return out


def parse_spice(path: Path) -> dict[str, Any]:
    subckts: dict[str, Subckt] = {}
    current: Subckt | None = None
    includes = []
    models = []
    for line in logical_lines(read_text(path)):
        low = line.lower()
        if low.startswith(".include") or low.startswith(".lib"):
            includes.append(line)
            continue
        if low.startswith(".model"):
            parts = line.split()
            if len(parts) > 1:
                models.append(parts[1])
            continue
        if low.startswith(".subckt"):
            parts = line.split()
            if len(parts) >= 2:
                current = Subckt(name=parts[1], ports=parts[2:], source_file=rel(path))
                subckts[current.name] = current
            continue
        if low.startswith(".ends"):
            current = None
            continue
        if current is None:
            continue
        if re.match(r"^[xX]\S+", line):
            parts = line.split()
            if len(parts) >= 2:
                current.instances.append({"name": parts[0], "type": parts[-1], "nets": parts[1:-1]})
        elif re.match(r"^[mM]\S+", line):
            parts = line.split()
            current.mos_count += 1
            current.instances.append({"name": parts[0], "type": parts[5] if len(parts) > 5 else "MOS", "nets": parts[1:5], "kind": "mos"})
    top = infer_top_subckt(subckts)
    return {
        "path": rel(path),
        "absolute_path": str(path.resolve()),
        "subckts": {name: subckt_to_dict(s) for name, s in subckts.items()},
        "top": subckt_to_dict(top) if top else None,
        "includes": includes,
        "models": sorted(set(models)),
        "module_count": len(subckts),
    }


def infer_top_subckt(subckts: dict[str, Subckt]) -> Subckt | None:
    if not subckts:
        return None
    referenced = {inst["type"] for sub in subckts.values() for inst in sub.instances}
    roots = [s for name, s in subckts.items() if name not in referenced]
    sram_roots = [s for s in roots if "sram" in s.name.lower()]
    if sram_roots:
        return max(sram_roots, key=lambda s: (len(s.ports), len(s.instances), s.name))
    return max(roots or list(subckts.values()), key=lambda s: (len(s.ports), len(s.instances), s.name))


def subckt_to_dict(subckt: Subckt) -> dict[str, Any]:
    return {
        "name": subckt.name,
        "ports": subckt.ports,
        "port_count": len(subckt.ports),
        "instance_count": len(subckt.instances),
        "mos_count": subckt.mos_count,
        "instance_types": dict(subckt.instance_types.most_common()),
        "source_file": subckt.source_file,
    }


def extract_openyield_pyspice() -> dict[str, Any]:
    files = sorted(list(OPENYIELD_SUBCIRCUIT_DIR.glob("*.py")) + list(OPENYIELD_TESTBENCH_DIR.glob("*.py")))
    modules = []
    for path in files:
        text = read_text(path)
        try:
            tree = ast.parse(text)
        except SyntaxError as exc:
            modules.append({"path": rel(path), "parse_error": str(exc)})
            continue
        for cls in [n for n in tree.body if isinstance(n, ast.ClassDef)]:
            info = analyze_openyield_class(path, cls, text)
            if info:
                modules.append(info)
    return {
        "source_files": [rel(p) for p in files],
        "modules": modules,
        "netlist_files": [rel(p) for p in OPENYIELD_ROOT.rglob("*") if p.is_file() and p.suffix.lower() in {".sp", ".spice", ".cir", ".lib"} and ".git" not in p.parts],
    }


def analyze_openyield_class(path: Path, cls: ast.ClassDef, text: str) -> dict[str, Any] | None:
    name_expr = ""
    nodes_expr = ""
    class_assigns = {}
    methods = []
    mos_calls = 0
    subckt_calls = 0
    inst_calls = 0
    circuit_sources = []
    for node in ast.walk(cls):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                t = safe_unparse(target)
                if t in {"NAME", "self.NAME"}:
                    name_expr = safe_unparse(node.value)
                elif t in {"NODES", "self.NODES"}:
                    nodes_expr = safe_unparse(node.value)
                if isinstance(target, ast.Name) and target.id.isupper():
                    class_assigns[target.id] = safe_unparse(node.value)
        elif isinstance(node, ast.FunctionDef):
            methods.append(node.name)
        elif isinstance(node, ast.Call):
            call = call_name(node)
            if call.endswith(".M") or call == "M":
                mos_calls += 1
            if call.endswith(".subcircuit") or call == "subcircuit":
                subckt_calls += 1
            if call.endswith(".X") or call == "X":
                inst_calls += 1
            if call.endswith(".V") or call.endswith(".PulseVoltageSource") or call.endswith(".PWL"):
                circuit_sources.append(call)
    if not (name_expr or nodes_expr or mos_calls or inst_calls or subckt_calls or "testbench" in rel(path).lower()):
        return None
    return {
        "path": rel(path),
        "class": cls.name,
        "name_expr": name_expr or class_assigns.get("NAME", ""),
        "nodes_expr": nodes_expr or class_assigns.get("NODES", ""),
        "methods": methods,
        "mos_call_count": mos_calls,
        "subcircuit_call_count": subckt_calls,
        "instance_call_count": inst_calls,
        "source_call_kinds": sorted(set(circuit_sources)),
        "role": infer_openyield_role(rel(path), cls.name, name_expr + " " + nodes_expr),
    }


def safe_unparse(node: ast.AST) -> str:
    try:
        return ast.unparse(node)
    except Exception:
        return type(node).__name__


def call_name(node: ast.Call) -> str:
    f = node.func
    if isinstance(f, ast.Name):
        return f.id
    if isinstance(f, ast.Attribute):
        prefix = ""
        if isinstance(f.value, ast.Name):
            prefix = f.value.id + "."
        return prefix + f.attr
    return ""


def infer_openyield_role(path: str, cls: str, expr: str) -> str:
    low = f"{path} {cls} {expr}".lower()
    for key, role in [
        ("sram_6t", "bitcell array"),
        ("sram_10t", "10T bitcell array"),
        ("dummy", "dummy row/column"),
        ("replica", "replica column"),
        ("precharge", "precharge"),
        ("write", "write driver"),
        ("mux", "column mux"),
        ("sense", "sense amplifier"),
        ("decoder", "decoder"),
        ("wordline", "wordline driver"),
        ("time", "control/timing logic"),
        ("dff", "state/control DFF"),
        ("testbench", "testbench/top circuit assembly"),
    ]:
        if key in low:
            return role
    return "support cell"


def port_category(port: str) -> str:
    p = port.lower().replace("_", "")
    if p in {"vdd", "vdd0", "vdd1"} or p.startswith("vdd"):
        return "power"
    if p in {"gnd", "vss", "vss0"} or p.startswith(("gnd", "vss")):
        return "ground"
    if "addr" in p or re.match(r"a\d+$", p):
        return "address"
    if "din" in p or p.startswith("data") or "data" in p and "out" not in p:
        return "data_in"
    if "dout" in p or p.startswith("q") or "out" in p:
        return "data_out"
    if "clk" in p or "clock" in p:
        return "clock"
    if p in {"csb", "cs", "web", "wen", "we", "en", "enb"} or "enable" in p:
        return "control"
    if p.startswith("wl"):
        return "wordline"
    if p.startswith("bl") or p.startswith("br") or p.startswith("blb"):
        return "bitline"
    return "other"


def summarize_ports(ports: list[str]) -> dict[str, Any]:
    cats = defaultdict(list)
    for port in ports:
        cats[port_category(port)].append(port)
    return {k: v for k, v in sorted(cats.items())}


def compare_ports(openram_ports: list[str], openyield_modules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    openram_cats = summarize_ports(openram_ports)
    oy_ports_by_cat: dict[str, set[str]] = defaultdict(set)
    for mod in openyield_modules:
        expr = mod.get("nodes_expr", "")
        for token in re.findall(r"'([^']+)'|\"([^\"]+)\"", expr):
            port = token[0] or token[1]
            oy_ports_by_cat[port_category(port)].add(port)
    cats = sorted(set(openram_cats) | set(oy_ports_by_cat))
    rows = []
    for cat in cats:
        rows.append(
            {
                "category": cat,
                "openram_ports": openram_cats.get(cat, []),
                "openyield_ports": sorted(oy_ports_by_cat.get(cat, [])),
                "note": port_note(cat, openram_cats.get(cat, []), sorted(oy_ports_by_cat.get(cat, []))),
            }
        )
    return rows


def port_note(cat: str, openram: list[str], oy: list[str]) -> str:
    if not oy:
        return "OpenYield 顶层不是固定 .SUBCKT，端口来自子电路/动态 testbench，需解析 PySpice assembly。"
    if cat in {"power", "ground"} and any(p.upper() == "VSS" for p in oy):
        return "OpenYield 使用 VDD/VSS；OpenRAM/当前 layoutgen 多用 vdd/gnd，需要别名映射。"
    if cat == "control" and {"EN", "ENB"} & set(p.upper() for p in oy):
        return "OpenYield 控制信号更细，包括 EN/ENB/wl_en/pre/s_en/w_en 等内部时序控制。"
    if not openram:
        return "OpenYield 子电路内部端口，OpenRAM 顶层通常不直接暴露。"
    return "需要按语义映射，不能只按名字匹配。"


def select_primary_openram(candidates: list[dict[str, Any]]) -> Path | None:
    preferences = [
        "build/openram_gds_only_2x16/openram_sram_2x16_1rw_freepdk45.sp",
        "compiler/tests/golden/sram_2_16_1_freepdk45.sp",
        "build/openram_hardcell_2x16/openram_sram_2x16_1rw_freepdk45.sp",
    ]
    by_path = {c["path"]: c for c in candidates}
    for pref in preferences:
        if pref in by_path:
            return REPO_ROOT / pref
    openram = [c for c in candidates if c["group"] == "openram" and c["extension"] in {".sp", ".spi", ".cdl"}]
    if not openram:
        return None
    return Path(openram[0]["absolute_path"])


def select_secondary_openram(candidates: list[dict[str, Any]], primary: Path | None) -> Path | None:
    pref = "compiler/tests/golden/sram_2_16_1_freepdk45.sp"
    p = REPO_ROOT / pref
    if p.exists() and (primary is None or p.resolve() != primary.resolve()):
        return p
    return None


def inspect_layoutgen_structure() -> dict[str, Any]:
    files = [
        STANDALONE_ROOT / "sram_layoutgen" / "standalone.py",
        STANDALONE_ROOT / "sram_layoutgen" / "netlist_writer.py",
        STANDALONE_ROOT / "sram_layoutgen" / "geometry.py",
        STANDALONE_ROOT / "sram_layoutgen" / "gds_writer.py",
        STANDALONE_ROOT / "sram_layoutgen" / "tech.py",
        STANDALONE_ROOT / "sram_layoutgen" / "openram_placement.py",
        STANDALONE_ROOT / "sram_layoutgen" / "verifier.py",
        STANDALONE_ROOT / "sram_layoutgen" / "correctness.py",
        STANDALONE_ROOT / "sram_layoutgen" / "occupancy.py",
        STANDALONE_ROOT / "technology" / "freepdk45" / "replacement_macros.json",
    ]
    result = []
    for path in files:
        if not path.exists():
            continue
        info: dict[str, Any] = {"path": rel(path), "role": layout_file_role(path), "functions": [], "classes": []}
        if path.suffix == ".py":
            tree = ast.parse(read_text(path))
            info["classes"] = [n.name for n in tree.body if isinstance(n, ast.ClassDef)]
            info["functions"] = [n.name for n in tree.body if isinstance(n, ast.FunctionDef)][:80]
            text = read_text(path).lower()
            info["reads_netlist"] = "parse" in text and "spice" in text
            info["hardcoded_structure_evidence"] = [
                token
                for token in ["xbit_r", "xprecharge", "xwrite", "xwl_driver", "row_logic_plan", "add_hard_array", "words_per_row"]
                if token in text
            ]
        result.append(info)
    return {
        "files": result,
        "assessment": "当前生成器主要是 spec/metadata/hardcell contract 驱动，结构在 standalone.py 和 netlist_writer.py 中程序化硬编码；尚不是 OpenYield/OpenRAM SPICE netlist 驱动的通用 layout compiler。",
    }


def layout_file_role(path: Path) -> str:
    name = path.name
    if name == "standalone.py":
        return "主 floorplan/placement/routing/report 生成入口"
    if name == "netlist_writer.py":
        return "当前 structural SPICE 输出器，不读取外部网表"
    if name == "geometry.py":
        return "LayoutDB、Instance、CellArray、Shape、Pin 数据结构"
    if name == "gds_writer.py":
        return "GDS 导出和 hardcell SREF 实例化"
    if name == "tech.py":
        return "PDK layer/cell/replacement macro contract 加载"
    if name == "openram_placement.py":
        return "OpenRAM-style origin/mirror/bbox placement helper"
    if name == "verifier.py":
        return "DRC-lite/overlap/spacing verification"
    if name == "correctness.py":
        return "semantic connectivity / port / power audit"
    if name == "occupancy.py":
        return "空白区域和优化目标分析"
    if name == "replacement_macros.json":
        return "FreePDK45 replacement macro manifest"
    return "support"


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(x).replace("\n", "<br>").replace("|", "\\|") for x in row) + " |")
    return "\n".join(out)


def list_short(items: Any, limit: int = 12) -> str:
    if isinstance(items, dict):
        seq = [f"{k}:{v}" for k, v in items.items()]
    else:
        seq = list(items or [])
    if len(seq) > limit:
        return ", ".join(map(str, seq[:limit])) + f", ... (+{len(seq)-limit})"
    return ", ".join(map(str, seq)) or "-"


def category_counts(instance_types: dict[str, int]) -> dict[str, int]:
    cats = Counter()
    for typ, count in instance_types.items():
        low = typ.lower()
        if any(k in low for k in ["cell_6t", "cell_1rw", "sram_6t", "bit"]):
            cats["bitcell"] += count
        elif "dummy" in low:
            cats["dummy"] += count
        elif "replica" in low:
            cats["replica"] += count
        elif "precharge" in low or "pre" in low:
            cats["precharge"] += count
        elif "sense" in low or "sa" == low:
            cats["sense_amp"] += count
        elif "write" in low or "wdriver" in low:
            cats["write_driver"] += count
        elif "decoder" in low or "dec" in low:
            cats["decoder"] += count
        elif "wl" in low or "wordline" in low:
            cats["wordline_driver"] += count
        elif "dff" in low or "flop" in low or "latch" in low:
            cats["state/control"] += count
        else:
            cats["logic/other"] += count
    return dict(cats)


def write_report(data: dict[str, Any]) -> Path:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    path = DOCS_DIR / "openyield_openram_netlist_diff_report.md"
    openram = data["primary_openram"]
    secondary = data.get("secondary_openram")
    oy = data["openyield"]
    top = openram.get("top") or {}
    secondary_top = (secondary or {}).get("top") or {}
    bitcell_summary = summarize_matching_subckt(openram["subckts"], "bitcell_array")
    control_summary = summarize_matching_subckt(openram["subckts"], "control_logic")
    port_data_summary = summarize_matching_subckt(openram["subckts"], "port_data")
    port_addr_summary = summarize_matching_subckt(openram["subckts"], "port_address")

    candidate_rows = [
        [c["group"], c["path"], c["extension"], c["size_bytes"], c["score"]]
        for c in data["candidate_summary"][:80]
    ]
    port_rows = [
        [r["category"], list_short(r["openram_ports"], 20), list_short(r["openyield_ports"], 20), r["note"]]
        for r in data["port_compare"]
    ]
    oy_module_rows = [
        [
            m.get("role", "-"),
            m.get("path", "-"),
            m.get("class", "-"),
            m.get("name_expr", "-"),
            m.get("nodes_expr", "-"),
            m.get("mos_call_count", 0),
            m.get("instance_call_count", 0),
        ]
        for m in oy["modules"]
        if m.get("role") in {
            "bitcell array",
            "10T bitcell array",
            "dummy row/column",
            "replica column",
            "precharge",
            "write driver",
            "column mux",
            "sense amplifier",
            "decoder",
            "wordline driver",
            "control/timing logic",
            "state/control DFF",
            "testbench/top circuit assembly",
        }
    ][:80]
    openram_module_rows = [
        [name, info["port_count"], info["instance_count"], info["mos_count"], list_short(info["instance_types"], 10)]
        for name, info in sorted(openram["subckts"].items(), key=lambda kv: (-kv[1]["instance_count"], kv[0]))[:80]
    ]
    layout_rows = [
        [
            f["path"],
            f["role"],
            list_short(f.get("classes", []), 8),
            list_short(f.get("functions", []), 14),
            list_short(f.get("hardcoded_structure_evidence", []), 10),
        ]
        for f in data["layoutgen"]["files"]
    ]
    hierarchy_rows = [
        ["top module", top.get("name", "-"), "OpenYield 没有提交固定 top .SUBCKT；由 `Sram6TCoreMcTestbench` 动态组装 `Circuit('SRAM_6T_Core_Testbench')`", "需要新增 PySpice/netlist emitter 或运行 OpenYield 生成 deck 后再做一对一 top 对比"],
        ["top ports", list_short(top.get("ports", []), 40), "子电路端口以 VDD/VSS/BL/BLB/WL/EN/DIN/ADDR 等分散出现", "需要建立 top pin canonicalization: vdd/VDD, gnd/VSS, addr/A*, din/DIN, dout/Q/QB"],
        ["bitcell array", bitcell_summary, "Sram6TCore: VDD,VSS, BLi, BLBi, WLi；可启用 equivalent model real_cell_mode", "OpenYield 支持等效单元/RC；现有 layoutgen 只实例化真实 hardcell 阵列"],
        ["control logic", control_summary, "OpenYield TIME 模块包含 addr/data DFF、gated clock、wl_en、rbl_delay、wen_delay、w_en/s_en/pre", "OpenYield 控制逻辑更接近仿真时序，需要先映射控制信号 contract"],
        ["peripherals", f"{port_data_summary}; {port_addr_summary}", "PRECHARGE, WRITEDRIVER, COLUMNMUX, SENSEAMP, DECODER_CASCADE, WORDLINEDRIVER", "模块语义相近但端口顺序/控制极性/电源名不同"],
    ]

    text = "\n".join(
        [
            "# OpenYield / OpenRAM 网表差异侦查报告",
            "",
            "## 0. 本轮范围",
            "",
            "本轮只做更新与侦查：检查 git 状态、拉取 OpenYield、扫描候选网表、静态解析 OpenRAM SPICE 与 OpenYield PySpice 子电路语义，并检查当前版图生成器结构。没有重构主生成流程，也没有删除已有文件。",
            "",
            "## 1. 仓库状态与 OpenYield 版本",
            "",
            f"- 根目录 git status：`{data['root_git_status_summary']}`",
            "- `deliverables/sram_layoutgen_standalone` 有既有未提交修改，未清理、未覆盖；详见报告末尾“未提交修改”。",
            f"- OpenYield path: `{rel(OPENYIELD_ROOT)}`",
            f"- OpenYield commit: `{data['openyield_commit']}`",
            f"- OpenYield branch: `{data['openyield_branch']}`",
            f"- OpenYield status after pull: `{data['openyield_status'] or 'clean'}`",
            f"- pull result: `{data['pull_result_one_line']}`",
            "",
            "## 2. 网表候选文件",
            "",
            "新版 OpenYield 已删除旧 `sim/*/*.sp` 示例 deck；当前仓库里可直接扫描到的 OpenYield SPICE 文件主要是 `tran_models/models_*.spice` 和 `size_optimization/model_lib/models.spice`。SRAM/memory/peripheral 的网表语义主要存在于 `sram_compiler/subcircuits/*.py` 和 `sram_compiler/testbenches/*.py`，由 PySpice 动态生成。",
            "",
            md_table(["group", "path", "ext", "size_bytes", "score"], candidate_rows),
            "",
            "## 3. 本次用于对比的主文件",
            "",
            f"- OpenRAM primary SPICE: `{openram['path']}`",
            f"- OpenRAM secondary/reference SPICE: `{secondary['path'] if secondary else 'none'}`",
            f"- OpenYield SPICE/model files: `{list_short(oy['netlist_files'], 20)}`",
            "- OpenYield SRAM/peripheral PySpice sources: `third_party/OpenYield/sram_compiler/subcircuits/*.py`, `third_party/OpenYield/sram_compiler/testbenches/*.py`",
            "",
            "## 4. 顶层端口对比",
            "",
            f"- OpenRAM primary top: `{top.get('name', '-')}`",
            f"- OpenRAM primary top ports: `{list_short(top.get('ports', []), 60)}`",
            f"- OpenRAM secondary top: `{secondary_top.get('name', '-')}`",
            "",
            md_table(["port category", "OpenRAM top", "OpenYield PySpice modules", "note"], port_rows),
            "",
            "## 5. 模块层次对比",
            "",
            md_table(["aspect", "OpenRAM", "OpenYield", "migration implication"], hierarchy_rows),
            "",
            "### OpenRAM parsed subckt overview",
            "",
            md_table(["subckt", "ports", "instances", "mos", "instance_types"], openram_module_rows),
            "",
            "### OpenYield PySpice module overview",
            "",
            md_table(["role", "source", "class", "NAME", "NODES", "M calls", "X calls"], oy_module_rows),
            "",
            "## 6. 外围电路差异",
            "",
            "- bitcell array：OpenRAM primary SPICE 是已展开/层次化 `.SUBCKT`，可直接看到 `cell_6t`/`cell_1rw`、dummy、replica、bitline load 等实例；OpenYield 用 `Sram6TCore` 动态生成 `SRAM_6T_CORE_{rows}x{cols}`，端口为 `VDD/VSS/BLi/BLBi/WLi`，还支持 `real_cell_mode` 把非目标单元替换成等效 RC/功耗模型。",
            "- wordline/decoder：OpenRAM 有 row decoder、wordline driver、replica bitline 等成熟层次；OpenYield 有 `DECODER3_8`、`DECODER_CASCADE`、`WORDLINEDRIVER`，端口和控制使能为 `EN/A0/A1/A2/WL*` 风格。",
            "- precharge：OpenRAM 当前 hardcell/生成器常用 `bl/br/en/vdd/gnd` 或 `BL/BR/EN` 风格；OpenYield `PRECHARGE` 端口是 `VDD, ENB, BL, BLB`，没有显式 VSS，控制极性为 ENB。",
            "- sense/write：OpenRAM/当前 layoutgen 的 `sense_amp/write_driver/tri_gate` 已有 GDS hardcell；OpenYield `SENSEAMP` 输出 `Q/QB`，`WRITEDRIVER` 使用 `EN/DIN/BL/BLB`，需要重新定义 dout/tri-state 映射。",
            "- control/timing：OpenYield `TIME` 模块比当前 layoutgen 的简化 control glue 更丰富，含 addr/data DFF、clk buffer、gated clock、wl_en、rbl_delay、wen_delay、w_en、s_en、pre 等；这是后续最大差异点。",
            "- power：OpenRAM 和当前 layoutgen 多为 `vdd/gnd`；OpenYield 源码统一使用 `VDD/VSS`。必须先做 power alias 和 pin order normalization。",
            "",
            "## 7. 当前版图生成器缺失能力",
            "",
            "- 缺少 OpenYield PySpice/生成后 SPICE 的通用解析器；当前 `NetlistWriter` 是输出器，不是输入解析器。",
            "- 缺少 netlist-module-to-GDS-cell contract resolver，不能把 `WRITEDRIVER`、`PRECHARGE`、`TIME` 等自动映射到现有 hardcell/replacement macro。",
            "- 缺少端口别名/极性系统，例如 `VSS->gnd`、`BLB->br`、`ENB->pchg_en`、`Q/QB->dout_int/tri`。",
            "- 缺少控制逻辑综合/物理约束层：OpenYield 的 `TIME`/delay/wen/s_en/pre 不应直接硬塞进现有 routes，需要先转成 architecture contract。",
            "- 缺少可聚合单元抽象，当前虽然使用 hardcell bbox/TEXT pin 和 abutment helper，但没有统一 footprint、rail sharing、abutment legality 数据结构。",
            "",
            "## 8. 当前版图生成器结构检查",
            "",
            data["layoutgen"]["assessment"],
            "",
            md_table(["file", "role", "classes", "functions", "hardcoded evidence"], layout_rows),
            "",
            "后续重点修改位置：",
            "",
            "- `sram_layoutgen/netlist_writer.py`：保留输出器，新增并行的 `netlist_parser.py` / `openyield_netlist_adapter.py`，不要把解析塞进 writer。",
            "- `sram_layoutgen/standalone.py`：后续应把硬编码 array/peripheral/control placement 拆成 netlist contract -> module plan -> placement plan。",
            "- `sram_layoutgen/tech.py` 与 `technology/freepdk45/replacement_macros.json`：扩展 module alias、pin alias、power alias、abutment metadata。",
            "- `sram_layoutgen/geometry.py`：扩展 CellFootprint、PinAccess、AbutmentRule、PowerRailMetadata、PlacementRow/ColumnRule。",
            "- `sram_layoutgen/correctness.py` / `verifier.py`：把 semantic connectivity audit 的预期来源改成 netlist contract。",
            "",
            "## 9. 可聚合设计初步方案",
            "",
            "建议先设计以下数据结构，再动 placement：",
            "",
            "- `CellFootprint`：cell name、logical bbox、physical bbox、origin convention、legal mirrors、site width/height、blockage layers。",
            "- `PinLocation` / `PinAccess`：pin name、net alias、layer、rect/point、direction、access side、preferred track、must_connect。",
            "- `PowerRailMetadata`：VDD/VSS rail layer、rail y/x interval、rail width、rail phase、can_share_with、strap points、tap requirement。",
            "- `AbutmentRule`：left/right/top/bottom compatibility、min gap、allowed overlap layers、shared rail rule、well/implant continuity rule、pin collision rule。",
            "- `PlacementRowRule`：row height、site pitch、legal cell classes、power rail orientation、mirror alternation、row endcap/tap policy。",
            "- `PlacementColumnRule`：bitline/wordline pitch coupling、column mux/sense/write alignment anchors、vertical rail sharing policy。",
            "- `ModuleContract`：netlist module name、canonical role、pin aliases、GDS cell candidates、required neighbors、routing obligations。",
            "",
            "可聚合目标应按顺序推进：先标准化 footprint/pin/power rail metadata，再支持同类单元一维 abutment，最后做二维 aggregation 和 shared rail DRC audit。",
            "",
            "## 10. 后续建议顺序",
            "",
            "1. 先做 OpenYield 网表/源码语义解析器：生成 `ModuleContract`，解析 PySpice `NAME/NODES/self.M/self.X/circuit.X`，必要时在有环境时运行 OpenYield 产生 `.sp` deck。",
            "2. 建立 OpenRAM/OpenYield/current-layoutgen 的 canonical port/module 字典：power、bitline、wordline、addr、data、precharge、sense、write、decoder、time/control。",
            "3. 扩展 `replacement_macros.json` 为 module alias + pin alias + footprint/power metadata，而不是立刻改 placement。",
            "4. 设计可聚合单元抽象并为现有 hardcells 回填 footprint/rail/abutment 信息。",
            "5. 最后才改 `standalone.py` 的 placement/routing，让它从 contract 驱动，而不是继续按固定结构写死。",
            "",
            "结论：建议第二步先做 OpenYield 网表解析器和 canonical contract，而不是先做可聚合单元抽象。原因是聚合规则必须知道要聚合哪些模块、端口和电源轨；这些应先由 OpenYield/OpenRAM 网表差异分析定义清楚。",
            "",
            "## 11. 未提交修改快照",
            "",
            "根目录不是 git 仓库；`deliverables/sram_layoutgen_standalone` 的 git status 如下，本轮未清理这些文件：",
            "",
            "```text",
            data["standalone_git_status"],
            "```",
            "",
            "## 12. 实际执行命令",
            "",
            "```text",
            "\n".join(data["commands"]),
            "```",
        ]
    )
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def summarize_matching_subckt(subckts: dict[str, dict[str, Any]], needle: str) -> str:
    matches = [(name, info) for name, info in subckts.items() if needle in name]
    if not matches:
        return f"未找到 `{needle}` 子模块"
    name, info = max(matches, key=lambda kv: (kv[1].get("instance_count", 0), kv[1].get("port_count", 0)))
    return (
        f"`{name}`: ports={info.get('port_count')}, instances={info.get('instance_count')}, "
        f"types={list_short(info.get('instance_types', {}), 8)}"
    )


def main() -> None:
    commands = [
        "git status --short  # repo root, failed because root is not a git repo",
        "git status --short  # deliverables/sram_layoutgen_standalone",
        "git -C third_party/OpenYield rev-parse/status",
        "git -C third_party/OpenYield pull --ff-only",
        "rg --files -g '*.sp' -g '*.spi' -g '*.spice' -g '*.cdl' -g '*.v' -g '*.sv'",
        "rg --files third_party/OpenYield",
        "static Python/SPICE scan via scripts/openyield_openram_netlist_diff.py",
    ]
    candidates = scan_netlist_candidates()
    primary_path = select_primary_openram(candidates)
    if primary_path is None:
        raise SystemExit("No OpenRAM SPICE candidate found")
    secondary_path = select_secondary_openram(candidates, primary_path)
    primary = parse_spice(primary_path)
    secondary = parse_spice(secondary_path) if secondary_path else None
    openyield = extract_openyield_pyspice()
    top_ports = (primary.get("top") or {}).get("ports", [])
    data = {
        "commands": commands,
        "root_git_status_summary": "not a git repository at workspace root",
        "standalone_git_status": run_git(["status", "--short"], STANDALONE_ROOT),
        "openyield_commit": run_git(["rev-parse", "HEAD"], OPENYIELD_ROOT),
        "openyield_branch": run_git(["rev-parse", "--abbrev-ref", "HEAD"], OPENYIELD_ROOT),
        "openyield_status": run_git(["status", "--short"], OPENYIELD_ROOT),
        "pull_result_one_line": "fast-forward to 1c34428d8b913963c4971d093b1a7c2df97a2509",
        "candidate_summary": candidates,
        "primary_openram": primary,
        "secondary_openram": secondary,
        "openyield": openyield,
        "port_compare": compare_ports(top_ports, openyield["modules"]),
        "layoutgen": inspect_layoutgen_structure(),
    }
    report = write_report(data)
    json_path = DOCS_DIR / "openyield_openram_netlist_diff_report.json"
    csv_path = DOCS_DIR / "openyield_openram_netlist_candidates.csv"
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["group", "path", "absolute_path", "extension", "size_bytes", "score"])
        writer.writeheader()
        writer.writerows(candidates)
    print(report)
    print(json_path)
    print(csv_path)


if __name__ == "__main__":
    main()
