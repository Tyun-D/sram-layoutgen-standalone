from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any


def compute_source_fingerprint(paths: list[Path]) -> str:
    payload = hashlib.sha256()
    for path in paths:
        payload.update(str(path).encode("utf-8"))
        payload.update(path.read_bytes())
    return payload.hexdigest()[:24]


@dataclass
class OpenRamRuntimeReport:
    openram_home: str
    openram_bootstrap_passed: bool
    openram_initialization_method: str
    openram_technology: str
    openram_worktree_modified: bool
    ptx_adapter_loaded: bool
    pinv_adapter_loaded: bool
    contact_adapter_loaded: bool
    gds_export_available: bool
    cleanup_passed: bool
    runtime_failure_reason: str
    openram_license_type: str
    openram_source_fingerprint: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "openram_home": self.openram_home,
            "openram_bootstrap_passed": self.openram_bootstrap_passed,
            "openram_initialization_method": self.openram_initialization_method,
            "openram_technology": self.openram_technology,
            "openram_worktree_modified": self.openram_worktree_modified,
            "ptx_adapter_loaded": self.ptx_adapter_loaded,
            "pinv_adapter_loaded": self.pinv_adapter_loaded,
            "contact_adapter_loaded": self.contact_adapter_loaded,
            "gds_export_available": self.gds_export_available,
            "cleanup_passed": self.cleanup_passed,
            "runtime_failure_reason": self.runtime_failure_reason,
            "openram_license_type": self.openram_license_type,
            "openram_source_fingerprint": self.openram_source_fingerprint,
        }


class OpenRamBackendContext:
    def __init__(self, openram_root: Path) -> None:
        self.openram_root = openram_root.resolve()
        self.compiler_root = (self.openram_root / "compiler").resolve()
        self.config_path = self.openram_root / "macros/sram_configs/example_config_freepdk45.py"
        self._tmpdir: tempfile.TemporaryDirectory[str] | None = None
        self._snapshot_env: dict[str, str | None] = {}
        self._snapshot_sys_path: list[str] = []
        self._pre_modules: set[str] = set()
        self._openram: ModuleType | None = None
        self._started = False
        self._cleanup_passed = False
        self._failure_reason = ""
        self._git_status_before = self._git_status()
        self.source_fingerprint = compute_source_fingerprint(
            [
                self.openram_root / "__init__.py",
                self.openram_root / "compiler/globals.py",
                self.openram_root / "compiler/modules/ptx.py",
                self.openram_root / "compiler/modules/pinv.py",
                self.openram_root / "compiler/base/contact.py",
                self.openram_root / "technology/freepdk45/tech/tech.py",
            ]
        )

    def __enter__(self) -> "OpenRamBackendContext":
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _git_status(self) -> str:
        try:
            proc = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.openram_root,
                text=True,
                capture_output=True,
                check=False,
            )
            return proc.stdout.strip()
        except Exception:
            return ""

    def start(self) -> None:
        if self._started:
            return
        self._snapshot_env = {key: os.environ.get(key) for key in ["OPENRAM_HOME", "OPENRAM_TECH", "PYTHONPATH"]}
        self._snapshot_sys_path = list(sys.path)
        self._pre_modules = set(sys.modules)
        self._tmpdir = tempfile.TemporaryDirectory(prefix="m12c3a_openram_")
        shim = Path(self._tmpdir.name) / "openram"
        shim.symlink_to(self.openram_root)
        os.environ["OPENRAM_HOME"] = str(self.compiler_root)
        os.environ["OPENRAM_TECH"] = str(self.openram_root / "technology")
        sys.path.insert(0, self._tmpdir.name)
        import openram  # type: ignore

        self._openram = openram
        openram.init_openram(str(self.config_path), is_unit_test=True)
        from openram import OPTS  # type: ignore

        OPTS.check_lvsdrc = False
        OPTS.inline_lvsdrc = False
        OPTS.netlist_only = False
        OPTS.is_unit_test = True
        self._started = True

    def set_output_name(self, output_name: str) -> None:
        if not self._started:
            raise RuntimeError("OpenRAM context not started")
        from openram import OPTS  # type: ignore

        OPTS.output_name = output_name

    def import_handles(self) -> dict[str, Any]:
        if not self._started:
            raise RuntimeError("OpenRAM context not started")
        from openram import OPTS, debug, verify  # type: ignore
        from openram.base import design, vector  # type: ignore
        from openram.base.contact import contact  # type: ignore
        from openram.modules.pgate import pgate  # type: ignore
        from openram.modules.pinv import pinv  # type: ignore
        from openram.modules.ptx import ptx  # type: ignore
        from openram.sram_factory import factory  # type: ignore
        from openram.tech import drc, layer  # type: ignore

        return {
            "OPTS": OPTS,
            "debug": debug,
            "verify": verify,
            "design": design,
            "vector": vector,
            "contact": contact,
            "pgate": pgate,
            "pinv": pinv,
            "ptx": ptx,
            "factory": factory,
            "drc": drc,
            "layer": layer,
        }

    def close(self) -> None:
        if not self._started:
            return
        try:
            if self._openram is not None and hasattr(self._openram, "end_openram"):
                self._openram.end_openram()
            self._cleanup_passed = True
        except Exception as exc:
            self._failure_reason = f"{type(exc).__name__}: {exc}"
            self._cleanup_passed = False
        finally:
            for module_name in [name for name in list(sys.modules) if name not in self._pre_modules and (name == "openram" or name.startswith("openram."))]:
                sys.modules.pop(module_name, None)
            sys.path[:] = self._snapshot_sys_path
            for key, value in self._snapshot_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
            if self._tmpdir is not None:
                self._tmpdir.cleanup()
            self._started = False

    def runtime_report(self) -> OpenRamRuntimeReport:
        license_text = (self.openram_root / "LICENSE").read_text(encoding="utf-8")
        license_type = "BSD-3-Clause" if "BSD 3-Clause License" in license_text else "UNKNOWN"
        return OpenRamRuntimeReport(
            openram_home=str(self.openram_root),
            openram_bootstrap_passed=self._openram is not None,
            openram_initialization_method="in-process openram.init_openram(example_config_freepdk45.py, is_unit_test=True) with temporary lowercase package symlink shim",
            openram_technology="FreePDK45",
            openram_worktree_modified=self._git_status_before != self._git_status(),
            ptx_adapter_loaded=self._started,
            pinv_adapter_loaded=self._started,
            contact_adapter_loaded=self._started,
            gds_export_available=self._started,
            cleanup_passed=self._cleanup_passed,
            runtime_failure_reason=self._failure_reason,
            openram_license_type=license_type,
            openram_source_fingerprint=self.source_fingerprint,
        )

