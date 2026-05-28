"""Extract OpenRAM-generated substructures as replacement macro GDS files.

This is a bridge for the lightweight standalone flow: OpenRAM remains the
trusted source for generated peripheral layout, while this package keeps a
small replacement manifest that can later point to better custom macros.
"""

from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sram_layoutgen.gds_writer import (  # noqa: E402
    GDSWriter,
    _gds_xy_scale,
    _read_gds_structures,
    _structure_dependency_closure,
)


DEFAULT_SUFFIX_MAP = {
    "gen_inv": "pinv",
    "gen_delay_inv": "pinv_16",
    "gen_nand2": "pnand2",
    "gen_wl_driver": "wordline_driver",
    "gen_precharge": "precharge_0",
    "gen_col_mux": "column_mux",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-gds", type=Path, required=True, help="OpenRAM generated GDS to mine for structures")
    parser.add_argument("--manifest", type=Path, default=ROOT / "technology" / "freepdk45" / "replacement_macros.json")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "technology" / "freepdk45" / "gds_lib" / "openram_replacements")
    parser.add_argument("--force", action="store_true", help="overwrite existing extracted macro GDS files")
    parser.add_argument(
        "--map",
        action="append",
        default=[],
        metavar="MACRO=STRUCTURE_OR_SUFFIX",
        help="override or add a macro-to-OpenRAM-structure mapping",
    )
    args = parser.parse_args()

    mapping = dict(DEFAULT_SUFFIX_MAP)
    for item in args.map:
        if "=" not in item:
            raise SystemExit(f"invalid --map item {item!r}; expected MACRO=STRUCTURE_OR_SUFFIX")
        macro, source = item.split("=", 1)
        mapping[macro.strip()] = source.strip()

    # Preserve OpenRAM geometry in the output library's 0.0005um DBU. Older
    # versions assumed a 0.001um source DBU and doubled coordinates; real
    # FreePDK45 OpenRAM GDS already uses 0.0005um here.
    structures = _read_gds_structures(args.source_gds, grid_dbu=5, scale_xy=_gds_xy_scale(args.source_gds, 2000))
    available = sorted(structures)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    macro_entries = {entry["name"]: entry for entry in manifest.get("macros", [])}
    extracted: dict[str, dict[str, object]] = {}
    skipped: dict[str, str] = {}

    for macro_name, source_query in sorted(mapping.items()):
        if macro_name not in macro_entries:
            skipped[macro_name] = "macro not present in manifest"
            continue
        source_name = _resolve_structure(source_query, available)
        if source_name is None:
            skipped[macro_name] = f"no OpenRAM structure matched {source_query!r}"
            continue
        out_path = args.out_dir / f"{macro_name}.gds"
        if out_path.exists() and not args.force:
            skipped[macro_name] = f"{out_path} already exists; use --force to overwrite"
            continue

        closure = _structure_dependency_closure(structures, {source_name})
        renamed = _rename_root_structure(closure, source_name, macro_name)
        _write_gds_library(out_path, renamed)
        rel = out_path.relative_to(args.manifest.parent).as_posix()
        macro_entries[macro_name]["role"] = "replacement_macro"
        macro_entries[macro_name]["gds"] = rel
        macro_entries[macro_name]["source"] = {
            "kind": "openram_generated_gds",
            "source_gds": str(args.source_gds),
            "source_structure": source_name,
        }
        extracted[macro_name] = {
            "source_structure": source_name,
            "out": str(out_path),
            "structure_count": len(renamed),
        }

    manifest["macros"] = [macro_entries[entry["name"]] for entry in manifest.get("macros", [])]
    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"extracted": extracted, "skipped": skipped}, indent=2))
    return 0 if extracted else 1


def _resolve_structure(query: str, structures: Iterable[str]) -> str | None:
    names = list(structures)
    if query in names:
        return query
    suffix = "_" + query
    matches = [name for name in names if name.endswith(suffix)]
    if not matches:
        matches = [name for name in names if name.endswith(query)]
    if not matches:
        return None
    return sorted(matches, key=lambda name: (len(name), name))[0]


def _rename_root_structure(structures: dict[str, bytes], old: str, new: str) -> dict[str, bytes]:
    result = dict(structures)
    if old not in result:
        return result
    root = _replace_strings_in_structure(result.pop(old), {old: new}, rename_structure=True)
    result[new] = root
    return result


def _replace_strings_in_structure(data: bytes, replacements: dict[str, str], rename_structure: bool = False) -> bytes:
    out = bytearray()
    offset = 0
    in_sref = False
    seen_strname = False
    while offset + 4 <= len(data):
        size, record_type, data_type = struct.unpack(">HBB", data[offset : offset + 4])
        if size < 4 or offset + size > len(data):
            out += data[offset:]
            break
        payload = data[offset + 4 : offset + size]
        replace = False
        if record_type == 0x06 and rename_structure and not seen_strname:
            replace = True
            seen_strname = True
        elif record_type == 0x0A:
            in_sref = True
        elif record_type == 0x12 and in_sref:
            replace = True
        elif record_type == 0x11:
            in_sref = False

        if replace:
            text = payload.rstrip(b"\0").decode("ascii", errors="ignore")
            if text in replacements:
                out += _string_record(record_type, data_type, replacements[text])
            else:
                out += data[offset : offset + size]
        else:
            out += data[offset : offset + size]
        offset += size
    return bytes(out)


def _write_gds_library(path: Path, structures: dict[str, bytes]) -> None:
    stamp = GDSWriter.DEFAULT_TIMESTAMP
    data = bytearray()
    data += GDSWriter._record(0x00, 0x02, b"".join(struct.pack(">h", value) for value in [600]))
    data += GDSWriter._record(0x01, 0x02, b"".join(struct.pack(">h", value) for value in [*stamp, *stamp]))
    data += _string_record(0x02, 0x06, "OPENRAM_REPLACEMENT")
    data += GDSWriter._record(
        0x03,
        0x05,
        GDSWriter._gds_real8(0.0005) + GDSWriter._gds_real8(5e-10),
    )
    for _name, structure in sorted(structures.items()):
        data += structure
    data += GDSWriter._record(0x04, 0x00, b"")
    path.write_bytes(data)


def _string_record(record_type: int, data_type: int, value: str) -> bytes:
    payload = value.encode("ascii", errors="ignore")
    if len(payload) % 2:
        payload += b"\0"
    return GDSWriter._record(record_type, data_type, payload)


if __name__ == "__main__":
    raise SystemExit(main())
