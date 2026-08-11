from __future__ import annotations

import hashlib
import xml.etree.ElementTree as ET
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def lyrdb_marker_count(path: Path) -> int:
    if not path.exists():
        return -1
    root = ET.parse(path).getroot()
    return len(root.findall(".//item"))

