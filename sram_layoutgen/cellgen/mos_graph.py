from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


MosType = Literal["NMOS", "PMOS"]


@dataclass(frozen=True)
class MosDevice:
    instance: str
    type: MosType
    model: str
    w_nm: int
    l_nm: int
    g: str
    s: str
    d: str
    b: str
    source_file: str
    source_line: int | str


@dataclass(frozen=True)
class TopologyLock:
    module: str
    pins: list[str]
    devices: list[MosDevice]
    authority_level: str

    @property
    def mos_count(self) -> int:
        return len(self.devices)

