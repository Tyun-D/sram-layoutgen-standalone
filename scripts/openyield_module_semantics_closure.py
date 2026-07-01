from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.module_semantics import (
    CONNECTION_COLUMNS,
    LAYOUTGEN_MAPPING_COLUMNS,
    MODULE_COLUMNS,
    PARAMETER_COLUMNS,
    VARIATION_COLUMNS,
    build_l0_semantics_report,
    render_markdown_table,
    write_csv,
    write_text,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate OpenYield L0 module-semantics closure artifacts.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--openyield-root", required=True)
    parser.add_argument("--out-semantics-csv", required=True)
    parser.add_argument("--out-semantics-md", required=True)
    parser.add_argument("--out-parameters-csv", required=True)
    parser.add_argument("--out-parameters-md", required=True)
    parser.add_argument("--out-connections-csv", required=True)
    parser.add_argument("--out-connections-md", required=True)
    parser.add_argument("--out-connection-graph", required=True)
    parser.add_argument("--out-variation-csv", required=True)
    parser.add_argument("--out-variation-md", required=True)
    parser.add_argument("--out-layoutgen-map-csv", required=True)
    parser.add_argument("--out-layoutgen-map-md", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-report", required=True)
    args = parser.parse_args()

    payload = build_l0_semantics_report(args.repo_root, args.openyield_root)
    report = payload["report"]
    module_rows = payload["module_rows"]
    parameter_rows = payload["parameter_rows"]
    connection_rows = payload["connection_rows"]
    variation_rows = payload["variation_rows"]
    mapping_rows = payload["layoutgen_mapping_rows"]
    connection_graph = payload["connection_graph"]

    write_csv(args.out_semantics_csv, module_rows, MODULE_COLUMNS)
    write_text(args.out_semantics_md, _matrix_md("OpenYield Module Semantics Matrix", module_rows, MODULE_COLUMNS))
    write_csv(args.out_parameters_csv, parameter_rows, PARAMETER_COLUMNS)
    write_text(args.out_parameters_md, _matrix_md("OpenYield Parameter Dependency Matrix", parameter_rows, PARAMETER_COLUMNS))
    write_csv(args.out_connections_csv, connection_rows, CONNECTION_COLUMNS)
    write_text(args.out_connections_md, _matrix_md("OpenYield Module Connection Matrix", connection_rows, CONNECTION_COLUMNS))
    write_csv(args.out_variation_csv, variation_rows, VARIATION_COLUMNS)
    write_text(args.out_variation_md, _matrix_md("OpenYield SRAM Config Variation Matrix", variation_rows, VARIATION_COLUMNS))
    write_csv(args.out_layoutgen_map_csv, mapping_rows, LAYOUTGEN_MAPPING_COLUMNS)
    write_text(args.out_layoutgen_map_md, _matrix_md("OpenYield to Layoutgen Semantic Mapping", mapping_rows, LAYOUTGEN_MAPPING_COLUMNS))

    out_graph = Path(args.out_connection_graph)
    out_graph.parent.mkdir(parents=True, exist_ok=True)
    out_graph.write_text(json.dumps(connection_graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_text(args.out_report, _report_md(report, module_rows, parameter_rows, connection_rows, variation_rows, mapping_rows))
    return 0


def _matrix_md(title: str, rows: list[dict[str, object]], columns: list[str]) -> str:
    return "\n".join(
        [
            f"# {title}",
            "",
            f"- row count: `{len(rows)}`",
            "",
            render_markdown_table(rows, columns),
            "",
        ]
    )


def _report_md(
    report: dict[str, object],
    module_rows: list[dict[str, object]],
    parameter_rows: list[dict[str, object]],
    connection_rows: list[dict[str, object]],
    variation_rows: list[dict[str, object]],
    mapping_rows: list[dict[str, object]],
) -> str:
    module_by_name = {str(row["module"]): row for row in module_rows}
    param_by_name = {str(row["parameter"]): row for row in parameter_rows}
    status = report["status_buckets"]
    return "\n".join(
        [
            "# OpenYield Module Semantics Closure Report",
            "",
            "This is the L0 netlist-semantics closure report. It is source-backed and intentionally stops before physical primitive or GDS closure.",
            "",
            "## Scope Summary",
            "",
            f"- modules covered: `{report['module_count']}`",
            f"- parameters covered: `{report['parameter_count']}`",
            f"- connections covered: `{report['connection_count']}`",
            f"- config-variation rows: `{report['variation_count']}`",
            f"- layoutgen mapping rows: `{report['layoutgen_mapping_count']}`",
            "",
            "## Required Answers",
            "",
            "1. OpenYield SRAM 的模块层次是什么？",
            "OpenYield 当前没有显式 `SRAM_TOP`/`BANK` 类，真实层次来自 `Sram6TCoreTestbench.create_testbench()`：`bitcell_array` + `replica_array` + 可选 `dummy_array` + `CONTROL_LOGIC(TIME)` + `row_decoder` + `wordline_driver` + `precharge/column_mux/sense_amp/write_driver`。",
            "",
            "2. 哪些模块是所有 SRAM 规格都需要的？",
            f"`{', '.join(report['key_questions_answered']['always_required_modules'])}`。",
            "",
            "3. 哪些模块是参数相关或可选的？",
            f"`{', '.join(report['key_questions_answered']['parameter_or_config_dependent_modules'])}`。",
            "",
            "4. 不同 word_size / num_words / words_per_row 下，哪些模块数量或结构变化？",
            "OpenYield 源码没有命名的 `word_size` / `num_words` / `words_per_row` 参数，当前只有 `num_rows` / `num_cols` / `choose_columnmux`。因此这三类逻辑规格变化在 L0 只能标记为“需要额外语义约定”，不能假设为源码内建规则。",
            "",
            "5. 地址如何进入 decoder？",
            "地址 `A[i]` 先进入 `ADDR_DFF`，形成 `A_dff[i]`，然后由 `create_decoder()` 把 `A_dff[i]` 送入 `DECODER_CASCADE`。",
            "",
            "6. decoder 如何驱动 wordline driver？",
            "`DECODER_CASCADE` 输出 `DEC_WL[i]`，`create_wl_driver()` 把该信号接到 `WORDLINEDRIVER.A`，同时把 `WL_EN` 接到 `WORDLINEDRIVER.B`，最终输出 `WL[i]`。",
            "",
            "7. bitcell array、precharge、column mux、sense amp、write driver 之间如何连接？",
            "读路径：`precharge -> BL/BLB -> column_mux(optional) -> sense_amp`。写路径：`DIN -> DATA_DFF -> write_driver -> BL/BLB -> bitcell_array`。当 `choose_columnmux=False` 时，`sense_amp` 直接接 `BL/BLB`。",
            "",
            "8. control logic、delay chain、replica、DFF row、gated clock 的语义关系是什么？",
            "`CONTROL_LOGIC(TIME)` 负责地址/数据 DFF、片选与写使能寄存、门控时钟、WL 使能，以及从 `replica_array` 的 `RBL` 经 `DELAY_CHAIN` 导出的 `rbl_delay/rbl_delay_bar`，进一步生成 `PRE/s_en/w_en`。",
            "",
            "9. OpenYield 中的模块语义与当前 layoutgen 的模块对应关系是什么？",
            "存储阵列、dummy、replica、wordline_driver、column_mux、sense_amp、write_driver 都有本地 counterpart。`TIME/control paths/decoder composite` 仍以 metadata/proxy/adapter 形式存在，未变成真正可摆放的统一本地模块。",
            "",
            "10. 进入下一层 physical primitive closure 前，还缺哪些 L0 语义信息？",
            "缺口主要在三个地方：一是逻辑规格参数和 OpenYield 行列参数之间的正式映射；二是 `TIME` 复合控制块的稳定分解边界；三是 decoder/control-path/local-routing 的 canonical naming contract。",
            "",
            "## Module Status",
            "",
            f"- SEMANTICS_CLOSED modules: `{', '.join(status.get('SEMANTICS_CLOSED', [])) or 'none'}`",
            f"- SOURCE_FOUND_PORTS_KNOWN modules: `{', '.join(status.get('SOURCE_FOUND_PORTS_KNOWN', [])) or 'none'}`",
            f"- SOURCE_FOUND_CONNECTIONS_UNRESOLVED modules: `{', '.join(status.get('SOURCE_FOUND_CONNECTIONS_UNRESOLVED', [])) or 'none'}`",
            f"- PARAMETER_RULE_UNRESOLVED modules: `{', '.join(status.get('PARAMETER_RULE_UNRESOLVED', [])) or 'none'}`",
            f"- LOCAL_MAPPING_UNRESOLVED modules: `{', '.join(status.get('LOCAL_MAPPING_UNRESOLVED', [])) or 'none'}`",
            f"- NOT_FOUND_IN_OPENYIELD modules: `{', '.join(status.get('NOT_FOUND_IN_OPENYIELD', [])) or 'none'}`",
            "",
            "## L0 Blocking Gaps",
            "",
            *[f"- {item}" for item in report["l0_blocking_gaps"]],
            "",
            "## Recommended Next Step After L0",
            "",
            report["recommended_next_step_after_l0"],
            "",
            "## Key Derived Rules",
            "",
            f"- `num_rows`: `{param_by_name['num_rows']['derivation_rule']}`",
            f"- `num_cols`: `{param_by_name['num_cols']['derivation_rule']}`",
            f"- `addr_size`: `{param_by_name['addr_size']['derivation_rule']}`",
            f"- `column_mux_ratio`: `{param_by_name['column_mux_ratio']['derivation_rule']}`",
            f"- `delay_chain_related_parameters`: `{param_by_name['delay_chain_related_parameters']['derivation_rule']}`",
            "",
            "## Representative Module Rows",
            "",
            render_markdown_table(
                [
                    module_by_name["SRAM_TOP"],
                    module_by_name["bitcell_array"],
                    module_by_name["row_decoder"],
                    module_by_name["wordline_driver"],
                    module_by_name["column_mux"],
                    module_by_name["sense_amp"],
                    module_by_name["write_driver"],
                    module_by_name["CONTROL_LOGIC"],
                ],
                MODULE_COLUMNS,
            ),
            "",
            "## Connection Coverage Snapshot",
            "",
            render_markdown_table(connection_rows[:12], CONNECTION_COLUMNS),
            "",
            "## Variation Coverage Snapshot",
            "",
            render_markdown_table(variation_rows, VARIATION_COLUMNS),
            "",
            "## Layoutgen Mapping Snapshot",
            "",
            render_markdown_table(mapping_rows[:12], LAYOUTGEN_MAPPING_COLUMNS),
            "",
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
