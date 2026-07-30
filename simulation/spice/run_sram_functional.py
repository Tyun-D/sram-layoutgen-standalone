from __future__ import annotations

import json
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
TB = REPO / "simulation/spice/testbenches/sram_basic_write_read_exploratory.sp"
OUT = REPO / "outputs/PROJECT_exploratory_sram_tb"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    log_path = OUT / "ngspice_exploratory.log"
    report = {
        "classification": "PROJECT_EXPLORATORY_TB",
        "claim_allowed": "engineering_debug_only",
        "testbench_path": str(TB),
        "simulator": "ngspice",
        "executed": False,
        "passed": False,
        "notes": [
            "This runner is intentionally exploratory and must not be used as final SRAM functional signoff.",
            "Write success is observed only through later SA_Q/SA_QB readback because internal cell Q/QB is not exported by the current top.",
        ],
    }
    try:
        completed = subprocess.run(
            ["ngspice", "-b", "-o", str(log_path), str(TB)],
            cwd=REPO,
            text=True,
            capture_output=True,
            check=False,
        )
        report["executed"] = True
        report["returncode"] = completed.returncode
        report["stdout"] = completed.stdout[-4000:]
        report["stderr"] = completed.stderr[-4000:]
        report["log_path"] = str(log_path)
        report["passed"] = completed.returncode == 0
    except FileNotFoundError:
        report["notes"].append("ngspice executable not found in PATH during this invocation.")
    (OUT / "PROJECT_EXPLORATORY_TB_REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
