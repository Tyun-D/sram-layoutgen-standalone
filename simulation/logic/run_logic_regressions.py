from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "simulation" / "logic"


def main() -> None:
    verilog_files = sorted(
        str(path.relative_to(REPO_ROOT))
        for path in REPO_ROOT.rglob("*")
        if path.suffix.lower() in {".v", ".sv", ".vh"} and ".git" not in path.parts
    )
    trusted = [path for path in verilog_files if "/work/external/" not in path and "My_OpenYield" not in path]
    report = {
        "logic_simulator_preference": "iverilog+vvp",
        "trusted_verilog_count": len(trusted),
        "all_verilog_count": len(verilog_files),
        "status": "BLOCKED_BY_MISSING_TRUSTED_VERILOG_ASSETS" if not trusted else "READY_FOR_IMPLEMENTATION",
        "blocking_reason": "No authoritative project Verilog assets were discovered in the current worktree audit."
        if not trusted
        else "",
        "trusted_verilog_files": trusted[:100],
        "all_discovered_verilog_files": verilog_files[:200],
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "logic_regression_status.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
