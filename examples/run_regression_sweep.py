#!/usr/bin/env python3
"""Run a parameter sweep for the standalone SRAM generator."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sram_layoutgen import StandaloneSpec, write_standalone


PROFILE_CASES: dict[str, list[tuple[int, int, int]]] = {
    "smoke": [
        (4, 32, 2),
    ],
    "quick": [
        (4, 32, 1),
        (4, 32, 2),
        (8, 64, 4),
    ],
    "stress": [
        (16, 128, 2),
        (16, 128, 8),
    ],
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-root", type=Path, default=ROOT / "build" / "regression_sweep")
    parser.add_argument(
        "--profile",
        choices=["smoke", "quick", "stress", "full"],
        default="full",
        help=(
            "test tier to run: smoke is the fixed small visual case, quick covers "
            "small representative cases, stress covers large congested cases, full "
            "runs the parameter sweep"
        ),
    )
    parser.add_argument("--word-sizes", default="1,2,4,8,16")
    parser.add_argument("--num-words", default="16,32,64,128")
    parser.add_argument("--default-wpr-only", action="store_true", help="run only the generator's default words_per_row")
    parser.add_argument("--keep-going", action="store_true", default=True, help="continue after a failed case")
    args = parser.parse_args()

    word_sizes = _parse_int_list(args.word_sizes)
    num_words_values = _parse_int_list(args.num_words)
    out_root = args.out_root
    out_root.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    started = time.time()
    for word_size, num_words, wpr in _iter_cases(args.profile, word_sizes, num_words_values, args.default_wpr_only):
        case_name = f"{word_size}x{num_words}_wpr{wpr}"
        case_out = out_root / case_name
        print(f"==> {case_name}")
        row = _run_case(word_size, num_words, wpr, case_out)
        rows.append(row)
        if row["status"] != "pass" and not args.keep_going:
            _write_summaries(out_root, rows, started, args.profile)
            return 1

    _write_summaries(out_root, rows, started, args.profile)
    failed = [row for row in rows if row["status"] != "pass"]
    print(f"Summary: {out_root / 'summary.md'}")
    print(f"JSON: {out_root / 'summary.json'}")
    return 1 if failed else 0


def _parse_int_list(text: str) -> list[int]:
    values = [int(item.strip()) for item in text.split(",") if item.strip()]
    if not values:
        raise ValueError("empty integer list")
    return values


def _iter_cases(
    profile: str,
    word_sizes: Iterable[int],
    num_words_values: Iterable[int],
    default_wpr_only: bool,
) -> Iterable[tuple[int, int, int]]:
    if profile in PROFILE_CASES:
        yield from PROFILE_CASES[profile]
        return

    for word_size in word_sizes:
        for num_words in num_words_values:
            base_spec = StandaloneSpec(word_size=word_size, num_words=num_words)
            wprs = [base_spec.resolved_words_per_row()] if default_wpr_only else base_spec.legal_words_per_row()
            for wpr in wprs:
                yield word_size, num_words, wpr


def _run_case(word_size: int, num_words: int, wpr: int, out_dir: Path) -> dict[str, object]:
    row: dict[str, object] = {
        "word_size": word_size,
        "num_words": num_words,
        "words_per_row": wpr,
        "case": f"{word_size}x{num_words}_wpr{wpr}",
        "out_dir": str(out_dir),
        "status": "fail",
    }
    try:
        spec = StandaloneSpec(word_size=word_size, num_words=num_words, words_per_row=wpr)
        metrics = write_standalone(spec, out_dir)
        promotion = metrics.get("route_guide_promotion", {})
        route_only = metrics.get("route_only_connectivity_audit", {})
        layer_audit = metrics.get("layer_audit", {})
        architecture_quality = metrics.get("architecture_quality", {})
        geometry_audit = metrics.get("geometry_audit", {})
        geometry_clean = geometry_audit.get("clean")
        row.update(
            {
                "status": (
                    "pass"
                    if metrics.get("drc_clean")
                    and route_only.get("all_generated_roles_touched_by_routes")
                    and geometry_clean is not False
                    else "fail"
                ),
                "name": metrics.get("name"),
                "gds": metrics.get("gds"),
                "presentation_gds": metrics.get("presentation_gds"),
                "debug_gds": metrics.get("debug_gds"),
                "integration_gds": metrics.get("integration_gds"),
                "architecture_gds": metrics.get("architecture_gds"),
                "architecture_svg": metrics.get("architecture_svg"),
                "route_guide_gds": metrics.get("route_guide_gds"),
                "report_md": metrics.get("report_md"),
                "report_json": str(out_dir / f"{metrics.get('name')}.report.json"),
                "area_um2": metrics.get("macro_area_um2"),
                "utilization": metrics.get("utilization"),
                "drc_clean": metrics.get("drc_clean"),
                "drc_violation_count": metrics.get("drc_violation_count"),
                "route_only_connected": route_only.get("all_generated_roles_touched_by_routes"),
                "initial_route_guides": promotion.get("initial_route_guides"),
                "promoted_to_routes": promotion.get("promoted_to_routes"),
                "remaining_route_guides": promotion.get("remaining_route_guides"),
                "remaining_by_layer": promotion.get("remaining_by_layer"),
                "blocked_by_reason": promotion.get("blocked_by_reason"),
                "layers_match_freepdk45": layer_audit.get("matches_bundled_freepdk45_layers"),
                "sample_like_floorplan": architecture_quality.get("sample_like_floorplan"),
                "missing_architecture_modules": architecture_quality.get("missing_modules"),
                "featured_module_overlap_count": architecture_quality.get("featured_module_overlap_count"),
                "geometry_clean": geometry_clean,
                "objects_outside_pr_boundary_count": geometry_audit.get("objects_outside_pr_boundary_count"),
                "data_periphery_overhang_count": geometry_audit.get("data_periphery_overhang_count"),
                "signoff_ready": metrics.get("signoff_ready"),
            }
        )
    except Exception as exc:  # noqa: BLE001 - regression report should capture generator failures.
        row["error"] = str(exc)
    return row


def _write_summaries(out_root: Path, rows: Iterable[dict[str, object]], started: float, profile: str) -> None:
    rows = list(rows)
    elapsed = time.time() - started
    payload = {
        "profile": profile,
        "elapsed_s": elapsed,
        "case_count": len(rows),
        "pass_count": sum(1 for row in rows if row.get("status") == "pass"),
        "fail_count": sum(1 for row in rows if row.get("status") != "pass"),
        "rows": rows,
    }
    (out_root / "summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (out_root / "summary.md").write_text(_format_markdown(payload), encoding="utf-8")


def _format_markdown(payload: dict[str, object]) -> str:
    rows = list(payload["rows"])  # type: ignore[index]
    lines = [
        "# SRAM Regression Sweep",
        "",
        f"- Profile: {payload.get('profile', 'full')}",
        f"- Cases: {payload['case_count']}",
        f"- Pass: {payload['pass_count']}",
        f"- Fail: {payload['fail_count']}",
        f"- Elapsed: {float(payload['elapsed_s']):.2f}s",
        "",
        "| case | status | floorplan | geometry | area(um^2) | util | DRC | route-only | promoted | remaining guides | remaining by layer | report |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for row in rows:
        if row.get("area_um2") is not None:
            area = f"{float(row['area_um2']):.3f}" if row.get("area_um2") is not None else "n/a"
            util = f"{float(row['utilization']) * 100.0:.2f}%" if row.get("utilization") is not None else "n/a"
            drc = str(row.get("drc_violation_count"))
            route_only = str(row.get("route_only_connected"))
            floorplan = str(row.get("sample_like_floorplan"))
            geometry = str(row.get("geometry_clean"))
            promoted = str(row.get("promoted_to_routes"))
            remaining = str(row.get("remaining_route_guides"))
            remaining_by_layer = _compact_dict(row.get("remaining_by_layer"))
            report = Path(str(row.get("report_md"))).name
        else:
            area = util = drc = route_only = floorplan = geometry = promoted = remaining = "n/a"
            remaining_by_layer = str(row.get("error", "failed"))
            report = ""
        lines.append(
            f"| {row['case']} | {row['status']} | {floorplan} | {geometry} | {area} | {util} | {drc} | {route_only} | "
            f"{promoted} | {remaining} | `{remaining_by_layer}` | `{report}` |"
        )
    lines.append("")
    return "\n".join(lines)


def _compact_dict(value: object) -> str:
    if not isinstance(value, dict):
        return "n/a"
    return ", ".join(f"{key}:{val}" for key, val in sorted(value.items()))


if __name__ == "__main__":
    raise SystemExit(main())
