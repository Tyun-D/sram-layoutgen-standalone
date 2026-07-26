from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
STANDALONE_ROOT = SCRIPT_DIR.parent
REPO_ROOT = STANDALONE_ROOT.parents[1]
if str(STANDALONE_ROOT) not in sys.path:
    sys.path.insert(0, str(STANDALONE_ROOT))

from sram_layoutgen.openyield_adapter.source_linked_timing_metadata import (  # noqa: E402
    build_control_timing_mapping,
    build_control_timing_mapping_review_report,
    build_source_linked_timing_metadata_audit,
    build_source_provenance_linking_report,
    discover_openyield_root,
    format_control_timing_mapping_review_markdown,
    format_mapping_markdown,
    format_source_linked_timing_metadata_audit_markdown,
    format_source_provenance_linking_markdown,
    write_csv,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate OpenYield source-linking, control mapping, and source-linked timing metadata audit artifacts.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--timing-json", required=True)
    parser.add_argument("--source-json", required=True)
    parser.add_argument("--mapping-csv", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()

    repo_root = resolve_input(args.repo_root)
    timing_json = resolve_input(args.timing_json)
    source_json = resolve_output(args.source_json)
    source_md = source_json.with_suffix(".md")
    mapping_csv = resolve_output(args.mapping_csv)
    mapping_md = mapping_csv.with_suffix(".md")
    mapping_review_json = resolve_output("docs/openyield_control_timing_mapping_review_report.json")
    mapping_review_md = resolve_output("docs/openyield_control_timing_mapping_review_report.md")
    out_json = resolve_output(args.out_json)
    out_md = resolve_output(args.out_md)

    timing_report = json.loads(timing_json.read_text(encoding="utf-8"))
    openyield_root = discover_openyield_root(repo_root)
    source_report = build_source_provenance_linking_report(repo_root, openyield_root, timing_json)
    mapping_rows = build_control_timing_mapping(timing_report, source_report)
    mapping_review = build_control_timing_mapping_review_report(repo_root, source_report, mapping_rows)
    audit_report = build_source_linked_timing_metadata_audit(repo_root, timing_report, source_report, mapping_rows)

    write_json(source_json, source_report)
    write_text(source_md, format_source_provenance_linking_markdown(source_report))
    write_csv(mapping_rows, mapping_csv)
    write_text(mapping_md, format_mapping_markdown(mapping_rows))
    write_json(mapping_review_json, mapping_review)
    write_text(mapping_review_md, format_control_timing_mapping_review_markdown(mapping_review))
    write_json(out_json, audit_report)
    write_text(out_md, format_source_linked_timing_metadata_audit_markdown(audit_report))

    smoke_assertions(source_report, mapping_rows, audit_report)

    print(f"Wrote {source_json}")
    print(f"Wrote {source_md}")
    print(f"Wrote {mapping_csv}")
    print(f"Wrote {mapping_md}")
    print(f"Wrote {mapping_review_json}")
    print(f"Wrote {mapping_review_md}")
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    print(f"openyield_head={source_report['openyield_head']}")
    print(f"source_to_candidate_spice_consistent={source_report['local_cross_validation']['source_to_candidate_spice_consistent']}")
    print(f"source_to_timing_metadata_consistent={source_report['local_cross_validation']['source_to_timing_metadata_consistent']}")
    for key, value in audit_report['gates'].items():
        print(f"{key}={value}")
    return 0


def smoke_assertions(source_report: dict, mapping_rows: list[dict], audit_report: dict) -> None:
    assert source_report['gates']['delay_chain_source_found'] is True
    assert source_report['gates']['pinv_source_found'] is True
    assert source_report['local_cross_validation']['source_to_candidate_spice_consistent'] is True
    assert source_report['local_cross_validation']['source_to_timing_metadata_consistent'] is True
    assert any(row['openyield_object'] == 'DELAY_CHAIN' for row in mapping_rows)
    assert audit_report['gates']['source_linked_timing_metadata_available'] is True
    assert audit_report['gates']['delay_chain_source_linked'] is True
    assert audit_report['gates']['delay_chain_timing_metadata_available'] is True
    assert audit_report['gates']['control_mapping_table_available'] is True
    assert audit_report['gates']['delay_chain_ready_for_metadata_consumption'] is True
    assert audit_report['gates']['any_control_path_ready_for_physical_integration'] is False
    assert audit_report['gates']['can_enter_metadata_consumer_adapter'] is True
    assert audit_report['gates']['can_modify_standalone_now'] is False
    assert audit_report['gates']['can_generate_time_control_gds_now'] is False
    assert audit_report['gates']['can_claim_openyield_full_integration_now'] is False


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8', newline='\n')


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8', newline='\n')


def resolve_input(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    for base in (Path.cwd(), STANDALONE_ROOT, REPO_ROOT):
        candidate = base / value
        if candidate.exists():
            return candidate
    return Path.cwd() / value


def resolve_output(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    if Path.cwd().resolve() == REPO_ROOT.resolve():
        return STANDALONE_ROOT / value
    return Path.cwd() / value


if __name__ == '__main__':
    raise SystemExit(main())
