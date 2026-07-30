#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.teamb_composite_helper import write_csv, write_json, write_text


def main() -> int:
    contract = {
        "scope": "project_sram_control_timing_contract",
        "classification": "PROJECT_ADAPTATION_CONTRACT",
        "dut_subckt": "OPENYIELD_SRAM_TOP_V1",
        "time_subckt": "TIME",
        "fields": [
            {"field": "clk", "status": "CURRENT_TOP_INTERFACE", "source": "openyield_sram_top_v1_16x16.sp .subckt OPENYIELD_SRAM_TOP_V1", "meaning": "external clock input"},
            {"field": "csb", "status": "UPSTREAM_EXACT", "source": "sram_6t_core_testbench.py create_time_circuit + OPENYIELD_SRAM_TOP_V1", "meaning": "active-low chip select driven by TB then translated by TIME"},
            {"field": "web", "status": "UPSTREAM_EXACT", "source": "sram_6t_core_testbench.py create_time_circuit + OPENYIELD_SRAM_TOP_V1", "meaning": "active-low write enable driven by TB then translated by TIME"},
            {"field": "wl_en", "status": "CURRENT_TOP_INTERFACE", "source": "TIME subckt pin list", "meaning": "generated internal wordline enable"},
            {"field": "s_en", "status": "CURRENT_TOP_INTERFACE", "source": "TIME subckt pin list", "meaning": "generated internal sense enable"},
            {"field": "w_en", "status": "CURRENT_TOP_INTERFACE", "source": "TIME subckt pin list", "meaning": "generated internal write enable"},
            {"field": "PRE", "status": "CURRENT_TOP_INTERFACE", "source": "TIME subckt pin list", "meaning": "generated internal precharge control"},
            {"field": "TIME_schedule", "status": "UNRESOLVED", "source": "no project-owned frozen write/read schedule", "meaning": "exact cycle-by-cycle project sampling contract still missing"},
            {"field": "read_sample_point", "status": "UPSTREAM_EXACT", "source": "sram_6t_core_testbench.py read measurements on WL/BL/SA_Q", "meaning": "upstream uses transient triggers on WL, BL/BLB, SA outputs"},
            {"field": "write_sample_point", "status": "UNRESOLVED", "source": "project has no reviewed readback oracle sequence yet", "meaning": "write success to later readback sampling remains unfrozen"},
            {"field": "disabled_hold_semantics", "status": "UNRESOLVED", "source": "project lacks reviewed top-level hold oracle", "meaning": "hold/disabled mode is not yet frozen as project evidence"},
        ],
    }
    out_json = REPO_ROOT / "docs" / "PROJECT_SRAM_CONTROL_TIMING_CONTRACT.json"
    out_md = REPO_ROOT / "docs" / "PROJECT_SRAM_CONTROL_TIMING_CONTRACT.md"
    out_gap = REPO_ROOT / "docs" / "PROJECT_SRAM_TB_BINDING_GAP.csv"
    write_json(out_json, contract)
    write_text(
        out_md,
        "\n".join(
            [
                "# Project SRAM Control Timing Contract",
                "",
                "- classification: `PROJECT_ADAPTATION_CONTRACT`",
                "- dut_subckt: `OPENYIELD_SRAM_TOP_V1`",
                "- time_subckt: `TIME`",
                "",
                "## Field Status",
                "",
            ]
            + [f"- `{row['field']}`: `{row['status']}` from `{row['source']}`" for row in contract["fields"]]
            + ["", "## Decision", "", "- Project-adapted SRAM functional TB remains blocked until unresolved scheduling/oracle fields are frozen as reviewed project evidence.", ""]
        ),
    )
    write_csv(
        out_gap,
        [
            {"field": row["field"], "status": row["status"], "source": row["source"], "meaning": row["meaning"]}
            for row in contract["fields"]
        ],
    )
    write_text(
        REPO_ROOT / "docs" / "PROJECT_SRAM_TB_BINDING_DECISION.md",
        "\n".join(
            [
                "# Project SRAM TB Binding Decision",
                "",
                "- decision: `BLOCKED_BY_SPECIFIC_INTERFACE_GAPS`",
                "- selected_reference: `OpenYield upstream TB source contract`",
                "- current_project_authority: `outputs/M12N2_clean_openyield_sram_top/current_supported_config/openyield_sram_top_v1_16x16.sp`",
                "",
                "## Conclusion",
                "",
                "- The project now has a project-owned control/timing contract draft, but it still contains unresolved schedule/oracle fields.",
                "- `clk/csb/web` and internal `TIME` outputs are interface-bound; exact project pass/fail timing for SRAM write/read remains unresolved.",
                "- A project-adapted SRAM TB must stay blocked until those unresolved fields are frozen.",
                "",
                "## Specific Field Blockers",
                "",
                "- `TIME_schedule`: no reviewed project cycle contract for write/read sequencing.",
                "- `write_sample_point`: no project-owned readback oracle timing after write.",
                "- `disabled_hold_semantics`: no reviewed hold-mode oracle for this top.",
                "",
            ]
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
