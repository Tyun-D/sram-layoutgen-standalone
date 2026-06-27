"""Server-side ngspice syntax smoke report helpers for candidate delay-chain SPICE."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any


EXPECTED_HEAD = "e76b52ef1e8d5eadce2003cbb4ef6f112ceb43fe"


def build_server_ngspice_syntax_smoke_report(
    repo_root: str | Path,
    candidate_dir: str | Path,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    candidate = _resolve_path(root, candidate_dir)
    include_file = candidate / "local_model_include_nom_server.inc"
    smoke_file = candidate / "delay_chain_syntax_smoke_ngspice.sp"
    log_file = candidate / "delay_chain_syntax_smoke_ngspice.log"

    head = _run_text(["git", "rev-parse", "HEAD"], cwd=root)
    ngspice_path = _which("ngspice")
    ngspice_version = _run_text(["ngspice", "-v"], cwd=root) if ngspice_path else None

    model_paths = _parse_include_paths(include_file)
    smoke_attempted = log_file.exists()
    smoke_text = smoke_file.read_text(encoding="utf-8") if smoke_file.exists() else ""
    log_text = log_file.read_text(encoding="utf-8", errors="replace") if log_file.exists() else ""
    log_excerpt = _build_log_excerpt(log_text)
    findings = _extract_findings(log_text)
    syntax_smoke_pass = _classify_smoke_pass(log_text, findings)
    failure_classification = None if syntax_smoke_pass else _classify_failure(log_text, findings)

    audit_summary = {
        "server_ngspice_syntax_smoke_available": True,
        "server_repo_head_matches_expected": head == EXPECTED_HEAD,
        "ngspice_found": ngspice_path is not None,
        "server_model_include_generated": include_file.exists(),
        "ngspice_smoke_deck_generated": smoke_file.exists(),
        "syntax_smoke_attempted": smoke_attempted,
        "syntax_smoke_pass": syntax_smoke_pass,
        "can_enter_delay_chain_smoke_simulation": syntax_smoke_pass,
        "can_claim_delay_proof_now": False,
        "can_claim_timing_closure_now": False,
        "can_enter_physical_timing_closure_now": False,
        "can_enter_physical_routing_now": False,
        "can_enter_physical_placement_now": False,
        "can_generate_time_control_gds_now": False,
        "can_modify_standalone_now": False,
    }

    report = {
        "scope": "server_ngspice_syntax_smoke",
        "repo_root": str(root),
        "repo_head": head,
        "expected_head": EXPECTED_HEAD,
        "candidate_dir": str(candidate),
        "ngspice": {
            "path": ngspice_path,
            "version": ngspice_version,
        },
        "freepdk45_model_paths": model_paths,
        "generated_server_include": {
            "path": str(include_file),
            "exists": include_file.exists(),
            "contents": include_file.read_text(encoding="utf-8") if include_file.exists() else None,
        },
        "generated_ngspice_smoke_deck": {
            "path": str(smoke_file),
            "exists": smoke_file.exists(),
            "contents": smoke_text,
        },
        "syntax_smoke_attempted": smoke_attempted,
        "syntax_smoke_pass": syntax_smoke_pass,
        "log_path": str(log_file),
        "key_log_excerpt": log_excerpt,
        "log_findings": findings,
        "failure_classification": failure_classification,
        "what_codex_can_fix": _what_codex_can_fix(failure_classification),
        "what_needs_user_or_teacher": _what_needs_user_or_teacher(failure_classification),
        "boundary_assertions": {
            "syntax_smoke_is_not_delay_proof": True,
            "timing_closure_not_claimed": True,
            "physical_timing_closure_not_claimed": True,
            "physical_routing_not_claimed": True,
            "physical_placement_not_claimed": True,
            "time_control_gds_not_claimed": True,
            "standalone_modified": False,
            "routing_modified": False,
            "gds_writer_modified": False,
        },
        "audit_summary": audit_summary,
    }
    return report


def format_server_ngspice_syntax_smoke_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OpenYield Server ngspice Syntax Smoke Report",
        "",
        f"- Scope: `{report['scope']}`",
        f"- Repo root: `{report['repo_root']}`",
        f"- Repo HEAD: `{report['repo_head']}`",
        f"- Expected HEAD: `{report['expected_head']}`",
        f"- Candidate dir: `{report['candidate_dir']}`",
        "",
        "## Audit Summary",
        "",
        "```json",
        json.dumps(report["audit_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Server Environment",
        "",
        "```json",
        json.dumps(report["ngspice"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## FreePDK45 Model Paths",
        "",
        "```json",
        json.dumps(report["freepdk45_model_paths"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Generated Server Include",
        "",
        "```json",
        json.dumps(report["generated_server_include"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Generated ngspice Smoke Deck",
        "",
        "```json",
        json.dumps(report["generated_ngspice_smoke_deck"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Syntax Smoke Result",
        "",
        "```json",
        json.dumps(
            {
                "syntax_smoke_attempted": report["syntax_smoke_attempted"],
                "syntax_smoke_pass": report["syntax_smoke_pass"],
                "log_path": report["log_path"],
                "failure_classification": report["failure_classification"],
            },
            ensure_ascii=False,
            indent=2,
        ),
        "```",
        "",
        "## Key Log Excerpt",
        "",
        "```text",
        report["key_log_excerpt"] or "",
        "```",
        "",
        "## Log Findings",
        "",
        "```json",
        json.dumps(report["log_findings"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## What Codex Can Fix",
        "",
        _list_block(report["what_codex_can_fix"]),
        "",
        "## What Needs User / Teacher",
        "",
        _list_block(report["what_needs_user_or_teacher"]),
        "",
        "## Boundary Assertions",
        "",
        "```json",
        json.dumps(report["boundary_assertions"], ensure_ascii=False, indent=2),
        "```",
    ]
    return "\n".join(lines)


def _resolve_path(root: Path, value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (root / path).resolve()


def _run_text(cmd: list[str], cwd: Path) -> str | None:
    try:
        result = subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or result.stderr.strip() or None


def _which(tool: str) -> str | None:
    return _run_text(["which", tool], cwd=Path.cwd())


def _parse_include_paths(include_file: Path) -> dict[str, Any]:
    if not include_file.exists():
        return {"include_file_missing": str(include_file)}
    includes: list[str] = []
    for line in include_file.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text.lower().startswith(".include"):
            continue
        match = re.search(r'"([^"]+)"', text)
        if match:
            includes.append(match.group(1))
    return {
        "include_file": str(include_file),
        "includes": includes,
    }


def _build_log_excerpt(log_text: str, line_limit: int = 40) -> str:
    if not log_text:
        return ""
    lines = log_text.splitlines()
    selected = [line for line in lines if re.search(r"error|fatal|warning|failed|unknown|undefined", line, re.I)]
    if selected:
        return "\n".join(selected[:line_limit])
    return "\n".join(lines[-line_limit:])


def _extract_findings(log_text: str) -> list[str]:
    if not log_text:
        return []
    findings = []
    for line in log_text.splitlines():
        if re.search(r"error|fatal|warning|failed|unknown|undefined", line, re.I):
            findings.append(line.strip())
    return findings[:80]


def _classify_smoke_pass(log_text: str, findings: list[str]) -> bool:
    if not log_text:
        return False
    low = log_text.lower()
    fatal_tokens = (
        "fatal",
        "error:",
        "simulation interrupted due to error",
        "unknown parameter",
        "failed",
        "undefined",
    )
    if any(token in low for token in fatal_tokens):
        return False
    if any("error" in item.lower() or "fatal" in item.lower() for item in findings):
        return False
    return "total analysis time" in low or "ngspice done" in low


def _classify_failure(log_text: str, findings: list[str]) -> dict[str, str]:
    joined = "\n".join(findings) if findings else log_text
    low = joined.lower()
    if any(token in low for token in ["unknown parameter", "unimplemented", "unsupported", "too many parameters", "bsim4"]):
        return {"code": "A", "label": "ngspice 不兼容 HSPICE model 语法"}
    if any(token in low for token in ["could not find include file", "no such file", "can't open", "cannot open"]):
        return {"code": "B", "label": "include 路径错误"}
    if any(token in low for token in ["unknown subckt", "parse error", "syntax error", "too few nodes", "too many nodes"]):
        return {"code": "C", "label": "candidate subckt 语法错误"}
    if any(token in low for token in ["unknown model", "unable to find definition of model", "undefined", "no model named"]):
        return {"code": "D", "label": "node / model name 未定义"}
    if any(token in low for token in ["tran", "time step", "tstep", "tstop", "tstart", "bad real value"]):
        return {"code": "E", "label": "transient deck 参数错误"}
    return {"code": "F", "label": "其他"}


def _what_codex_can_fix(failure: dict[str, str] | None) -> list[str]:
    base = [
        "Generate a server-local nominal include that uses Linux paths.",
        "Generate a minimal ngspice syntax smoke deck for parse/elaboration only.",
        "Collect ngspice logs and classify failures without claiming timing proof.",
        "Regenerate JSON/Markdown evidence after reruns.",
    ]
    if failure and failure["code"] in {"B", "C", "D", "E"}:
        base.append("Adjust the smoke deck or include wiring when the failure is outside the PDK model contents.")
    return base


def _what_needs_user_or_teacher(failure: dict[str, str] | None) -> list[str]:
    base = [
        "Formal VDD/PVT/slew thresholds for any real simulation remain undefined.",
        "Timing proof, timing closure, and physical closure require separate validated flows.",
    ]
    if failure and failure["code"] == "A":
        base.append("A simulator/model combination that supports the provided HSPICE-oriented FreePDK45 model syntax may be required.")
        base.append("If ngspice must be used, the PDK model bundle likely needs an ngspice-compatible conversion provided by the project owner or teacher.")
    return base


def _list_block(items: list[str]) -> str:
    if not items:
        return "- None"
    return "\n".join(f"- {item}" for item in items)
