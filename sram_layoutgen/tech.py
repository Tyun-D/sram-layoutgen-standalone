"""Technology rule model with a FreePDK45 default."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .gds_util import measure_gds_bbox
from .stdcell import GENERATED_CELLS


@dataclass(frozen=True)
class LayerRule:
    name: str
    lef_name: str
    gds_layer: int
    datatype: int = 0
    direction: str = "H"
    min_width: float = 0.07
    min_space: float = 0.07
    pitch: float = 0.14
    routable: bool = True


@dataclass(frozen=True)
class ViaRule:
    name: str
    lower: str
    upper: str
    size: float
    enclosure: float
    cost: float = 4.0


@dataclass(frozen=True)
class CellAbstract:
    name: str
    width: float
    height: float
    gds_path: Optional[str] = None
    spice_path: Optional[str] = None
    role: str = ""
    bbox_x0: float = 0.0
    bbox_y0: float = 0.0
    bbox_x1: float = 0.0
    bbox_y1: float = 0.0
    measured_from_gds: bool = False
    bbox_source: str = "default"
    geometry_bbox: Optional[Dict[str, object]] = None
    marker_bbox: Optional[Dict[str, object]] = None

    @property
    def area(self) -> float:
        return self.width * self.height

    def to_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "role": self.role,
            "width": self.width,
            "height": self.height,
            "gds_path": self.gds_path,
            "spice_path": self.spice_path,
            "bbox": {
                "x0": self.bbox_x0,
                "y0": self.bbox_y0,
                "x1": self.bbox_x1,
                "y1": self.bbox_y1,
            },
            "measured_from_gds": self.measured_from_gds,
            "bbox_source": self.bbox_source,
            "geometry_bbox": self.geometry_bbox,
            "marker_bbox": self.marker_bbox,
        }


class Tech:
    """Serializable subset of process rules needed by the generator."""

    def __init__(
        self,
        name: str,
        layers: Iterable[LayerRule],
        vias: Iterable[ViaRule],
        cells: Optional[Iterable[CellAbstract]] = None,
        reference_files: Optional[Dict[str, List[str]]] = None,
        manufacturing_grid: float = 0.0025,
    ) -> None:
        self.name = name
        self.layers: Dict[str, LayerRule] = {layer.name: layer for layer in layers}
        self.vias: Dict[str, ViaRule] = {via.name: via for via in vias}
        self.cells: Dict[str, CellAbstract] = {cell.name: cell for cell in cells or []}
        self.reference_files: Dict[str, List[str]] = reference_files or {}
        self.manufacturing_grid = manufacturing_grid

    @classmethod
    def freepdk45(cls, root: Optional[Path] = None) -> "Tech":
        layer_map = _default_layer_map()
        if root is not None:
            map_path = root / "technology" / "freepdk45" / "layers.map"
            if map_path.exists():
                layer_map.update(_read_layer_map(map_path))

        def layer(
            name: str,
            lef_name: str,
            direction: str,
            width: float,
            space: float,
            routable: bool = True,
        ) -> LayerRule:
            gds_layer, datatype = layer_map[lef_name]
            return LayerRule(
                name=name,
                lef_name=lef_name,
                gds_layer=gds_layer,
                datatype=datatype,
                direction=direction,
                min_width=width,
                min_space=space,
                pitch=max(width + space, 0.0025),
                routable=routable,
            )

        layers = [
            layer("boundary", "text", "H", 0.01, 0.01, False),
            layer("active", "active", "V", 0.09, 0.08, False),
            layer("pwell", "pwell", "H", 0.20, 0.135, False),
            layer("nwell", "nwell", "H", 0.20, 0.135, False),
            layer("nimplant", "nimplant", "H", 0.045, 0.045, False),
            layer("pimplant", "pimplant", "H", 0.045, 0.045, False),
            layer("vtg", "vtg", "H", 0.045, 0.045, False),
            layer("vth", "vth", "H", 0.045, 0.045, False),
            layer("thkox", "thkox", "H", 0.045, 0.045, False),
            layer("poly", "poly", "V", 0.05, 0.14, False),
            layer("contact", "contact", "H", 0.065, 0.075, False),
            layer("m1", "metal1", "H", 0.065, 0.065),
            layer("via1", "via1", "H", 0.065, 0.075, False),
            layer("m2", "metal2", "V", 0.070, 0.070),
            layer("via2", "via2", "H", 0.065, 0.085, False),
            layer("m3", "metal3", "H", 0.070, 0.070),
            layer("via3", "via3", "H", 0.070, 0.085, False),
            layer("m4", "metal4", "V", 0.140, 0.140),
        ]
        vias = [
            ViaRule("via1", "m1", "m2", 0.065, 0.035, 4.0),
            ViaRule("via2", "m2", "m3", 0.065, 0.035, 4.4),
            ViaRule("via3", "m3", "m4", 0.070, 0.035, 4.8),
        ]
        cells = _freepdk45_cells(root, layer_map)
        refs = _freepdk45_reference_files(root)
        return cls("freepdk45", layers, vias, cells, refs)

    def layer(self, name: str) -> LayerRule:
        return self.layers[name]

    def routable_layers(self, names: Optional[Iterable[str]] = None) -> List[LayerRule]:
        if names is None:
            return [layer for layer in self.layers.values() if layer.routable]
        return [self.layers[name] for name in names if self.layers[name].routable]

    def via_between(self, a: str, b: str) -> Optional[ViaRule]:
        names = {a, b}
        for via in self.vias.values():
            if {via.lower, via.upper} == names:
                return via
        return None

    def snap(self, value: float) -> float:
        grid = self.manufacturing_grid
        return round(value / grid) * grid

    def cell(self, name: str) -> CellAbstract:
        return self.cells[name]


def load_tech(name: str, root: Optional[Path] = None) -> Tech:
    normalized = name.lower()
    if normalized != "freepdk45":
        raise ValueError(f"unsupported technology '{name}', only freepdk45 is implemented")
    return Tech.freepdk45(root)


def _read_layer_map(path: Path) -> Dict[str, tuple[int, int]]:
    result: Dict[str, tuple[int, int]] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) >= 4:
            result[parts[0]] = (int(parts[2]), int(parts[3]))
    return result


def _default_layer_map() -> Dict[str, tuple[int, int]]:
    return {
        "active": (1, 0),
        "pwell": (2, 0),
        "nwell": (3, 0),
        "nimplant": (4, 0),
        "pimplant": (5, 0),
        "vtg": (6, 0),
        "vth": (7, 0),
        "thkox": (8, 0),
        "poly": (9, 0),
        "contact": (10, 0),
        "metal1": (11, 0),
        "via1": (12, 0),
        "metal2": (13, 0),
        "via2": (14, 0),
        "metal3": (15, 0),
        "via3": (16, 0),
        "metal4": (17, 0),
        "text": (239, 0),
    }


def _freepdk45_cells(root: Optional[Path], layer_map: Dict[str, tuple[int, int]]) -> List[CellAbstract]:
    tech_root = root / "technology" / "freepdk45" if root is not None else None
    text_layer = layer_map["text"][0]

    def ref(
        name: str,
        width: float,
        height: float,
        role: str,
        gds_relpath: Optional[str] = None,
        spice_relpath: Optional[str] = None,
        abstract_bbox_source: str = "default",
    ) -> CellAbstract:
        gds_path = None
        spice_path = None
        bbox_x0 = 0.0
        bbox_y0 = 0.0
        bbox_x1 = width
        bbox_y1 = height
        measured = False
        bbox_source = "default"
        geometry_bbox = None
        marker_bbox = None
        if tech_root is not None:
            gds = None
            spice = None
            if gds_relpath is None:
                gds = tech_root / f"gds_lib/{name}.gds"
            elif gds_relpath:
                gds = tech_root / gds_relpath
            if spice_relpath is None:
                spice = tech_root / f"sp_lib/{name}.sp"
            elif spice_relpath:
                spice = tech_root / spice_relpath
            gds_path = str(gds) if gds is not None and gds.exists() else None
            spice_path = str(spice) if spice is not None and spice.exists() else None
            if gds is not None and gds.exists():
                geometry = measure_gds_bbox(gds, ignored_layers={text_layer})
                marker = measure_gds_bbox(gds, boundary_layers={text_layer})
                bbox = geometry or marker or measure_gds_bbox(gds)
                if bbox is not None:
                    width = bbox.width
                    height = bbox.height
                    bbox_x0 = bbox.x0
                    bbox_y0 = bbox.y0
                    bbox_x1 = bbox.x1
                    bbox_y1 = bbox.y1
                    measured = True
                    bbox_source = "physical_geometry_excluding_text_layer" if geometry is not None else "text_marker_fallback"
                    geometry_bbox = geometry.to_dict() if geometry is not None else None
                    marker_bbox = marker.to_dict() if marker is not None else None
                    if marker is not None and geometry is not None:
                        # OpenRAM's text-marker rectangle records the module
                        # placement pitch/origin, while drawn geometry may
                        # intentionally extend outside that logical boundary
                        # for legal abutment. Keep both: width/height drive
                        # placement, bbox_* drives physical overlap/audit.
                        width = marker.x1 if marker.x1 > 0 else marker.width
                        height = marker.y1 if marker.y1 > 0 else marker.height
                        bbox_source = "logical_text_marker_with_physical_geometry"
        if not measured and abstract_bbox_source != "default":
            bbox_source = abstract_bbox_source
        return CellAbstract(
            name,
            width,
            height,
            gds_path,
            spice_path,
            role,
            bbox_x0,
            bbox_y0,
            bbox_x1,
            bbox_y1,
            measured,
            bbox_source,
            geometry_bbox,
            marker_bbox,
        )

    cells = [
        ref("cell_1rw", 0.46, 1.12, "bitcell"),
        ref("dummy_cell_1rw", 0.46, 1.12, "dummy_bitcell"),
        ref("replica_cell_1rw", 0.46, 1.12, "replica_bitcell"),
        ref("sense_amp", 1.80, 2.20, "sense_amp"),
        ref("write_driver", 1.80, 2.20, "write_driver"),
        ref("tri_gate", 1.40, 1.80, "tri_gate"),
        ref("dff", 1.80, 2.40, "control"),
    ]
    for macro in _replacement_macro_specs(tech_root):
        cells.append(ref(
            str(macro["name"]),
            float(macro["width"]),
            float(macro["height"]),
            str(macro.get("role") or "abstract_macro"),
            gds_relpath=str(macro["gds"]) if macro.get("gds") else "",
            spice_relpath=str(macro["spice"]) if macro.get("spice") else "",
            abstract_bbox_source="replacement_macro_manifest",
        ))
    return cells


def _replacement_macro_specs(tech_root: Optional[Path]) -> List[Dict[str, object]]:
    manifest = tech_root / "replacement_macros.json" if tech_root is not None else None
    if manifest is not None and manifest.exists():
        data = json.loads(manifest.read_text(encoding="utf-8"))
        macros = data.get("macros", [])
        if not isinstance(macros, list):
            raise ValueError(f"replacement macro manifest has invalid macros list: {manifest}")
        result: List[Dict[str, object]] = []
        for macro in macros:
            if not isinstance(macro, dict):
                raise ValueError(f"replacement macro entry is not an object in {manifest}")
            for key in ("name", "width", "height"):
                if key not in macro:
                    raise ValueError(f"replacement macro entry missing {key!r} in {manifest}")
            result.append(macro)
        return result

    result = []
    for name, (width, height, _role) in GENERATED_CELLS.items():
        result.append({
            "name": name,
            "width": width,
            "height": height,
            "role": "abstract_macro",
            "gds": None,
            "spice": None,
        })
    return result


def _freepdk45_reference_files(root: Optional[Path]) -> Dict[str, List[str]]:
    if root is None:
        return {}
    tech_root = root / "technology" / "freepdk45"
    refs: Dict[str, List[str]] = {
        "gds_lib": [str(path) for path in sorted((tech_root / "gds_lib").glob("*.gds"))],
        "sp_lib": [str(path) for path in sorted((tech_root / "sp_lib").glob("*.sp"))],
        "klayout": [str(path) for path in sorted((tech_root / "tech").glob("*.ly*"))],
        "replacement_macros": [str(tech_root / "replacement_macros.json")]
        if (tech_root / "replacement_macros.json").exists()
        else [],
    }
    return {key: value for key, value in refs.items() if value}
