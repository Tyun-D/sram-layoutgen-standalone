from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def json_dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def md_table(columns: list[str], rows: list[dict[str, Any]]) -> str:
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in rows:
        vals = []
        for c in columns:
            v = row.get(c, "")
            if isinstance(v, (dict, list)):
                v = json.dumps(v, ensure_ascii=False)
            vals.append(str(v).replace("\n", "<br>"))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines) + "\n"
