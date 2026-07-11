from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


def bootstrap_openram_adapter(openram_root: Path) -> dict[str, Any]:
    license_path = openram_root / "LICENSE"
    readme_path = openram_root / "README.md"
    compiler_root = openram_root / "compiler"
    config_path = openram_root / "macros/sram_configs/example_config_freepdk45.py"

    in_process = _attempt_in_process_bootstrap(openram_root, compiler_root, config_path)
    subprocess_result = _attempt_subprocess_bootstrap(openram_root, compiler_root, config_path)
    mode = "NOT_CALLABLE"
    if in_process["passed"]:
        mode = "IN_PROCESS_OPENRAM_BOOTSTRAP"
    elif subprocess_result["passed"]:
        mode = "SUBPROCESS_OPENRAM_CONTEXT"
    return {
        "openram_home_found": compiler_root.exists(),
        "openram_license_found": license_path.exists(),
        "openram_license_type": _detect_license_type(license_path),
        "openram_import_bootstrap_attempted": True,
        "openram_import_bootstrap_passed": in_process["passed"] or subprocess_result["passed"],
        "openram_initialization_required": True,
        "openram_initialization_method": "openram.init_openram(example_config_freepdk45.py, is_unit_test=True) with lowercase openram symlink shim",
        "ptx_import_passed": in_process["ptx_import_passed"] or subprocess_result["ptx_import_passed"],
        "pinv_import_passed": in_process["pinv_import_passed"] or subprocess_result["pinv_import_passed"],
        "contact_import_passed": in_process["contact_import_passed"] or subprocess_result["contact_import_passed"],
        "ptx_signature_extracted": in_process["ptx_signature"] or subprocess_result["ptx_signature"],
        "pinv_signature_extracted": in_process["pinv_signature"] or subprocess_result["pinv_signature"],
        "contact_signature_extracted": in_process["contact_signature"] or subprocess_result["contact_signature"],
        "in_process_adapter_possible": in_process["passed"],
        "subprocess_adapter_possible": subprocess_result["passed"],
        "recommended_adapter_execution_mode": mode,
        "bootstrap_failure_reason": "" if mode != "NOT_CALLABLE" else (in_process["failure_reason"] or subprocess_result["failure_reason"] or "unknown"),
        "readme_path": str(readme_path),
    }


def _detect_license_type(license_path: Path) -> str:
    if not license_path.exists():
        return "UNKNOWN"
    text = license_path.read_text(encoding="utf-8")
    if "BSD 3-Clause License" in text:
        return "BSD-3-Clause"
    return "UNKNOWN"


def _attempt_in_process_bootstrap(openram_root: Path, compiler_root: Path, config_path: Path) -> dict[str, Any]:
    snapshot = {key: os.environ.get(key) for key in ["OPENRAM_HOME", "OPENRAM_TECH", "PYTHONPATH"]}
    original_sys_path = list(sys.path)
    created_modules = set()
    tmpdir = tempfile.TemporaryDirectory()
    try:
        symlink = Path(tmpdir.name) / "openram"
        symlink.symlink_to(openram_root)
        os.environ["OPENRAM_HOME"] = str(compiler_root)
        os.environ["OPENRAM_TECH"] = str(openram_root / "technology")
        sys.path.insert(0, tmpdir.name)
        import openram  # type: ignore

        created_modules.update([name for name in sys.modules if name == "openram" or name.startswith("openram.")])
        openram.init_openram(str(config_path), is_unit_test=True)
        from openram.modules.ptx import ptx  # type: ignore
        from openram.modules.pinv import pinv  # type: ignore
        from openram.base.contact import contact  # type: ignore
        signatures = {
            "ptx_signature": str(__import__("inspect").signature(ptx.__init__)),
            "pinv_signature": str(__import__("inspect").signature(pinv.__init__)),
            "contact_signature": str(__import__("inspect").signature(contact.__init__)),
        }
        ptx(width=0.09, tx_type="nmos")
        pinv(name="pinv_test", size=1)
        contact(layer_stack=("active", "contact", "m1"), dimensions=(1, 1))
        try:
            openram.end_openram()
        except Exception:
            pass
        return {
            "passed": True,
            "ptx_import_passed": True,
            "pinv_import_passed": True,
            "contact_import_passed": True,
            **signatures,
            "failure_reason": "",
        }
    except Exception as exc:
        return {
            "passed": False,
            "ptx_import_passed": False,
            "pinv_import_passed": False,
            "contact_import_passed": False,
            "ptx_signature": "",
            "pinv_signature": "",
            "contact_signature": "",
            "failure_reason": f"{type(exc).__name__}: {exc}",
        }
    finally:
        for name in [key for key in list(sys.modules) if key == "openram" or key.startswith("openram.")]:
            sys.modules.pop(name, None)
        sys.path[:] = original_sys_path
        for key, value in snapshot.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        tmpdir.cleanup()


def _attempt_subprocess_bootstrap(openram_root: Path, compiler_root: Path, config_path: Path) -> dict[str, Any]:
    script = f"""
import inspect
import json
import os
import tempfile
from pathlib import Path
tmpdir = tempfile.TemporaryDirectory()
symlink = Path(tmpdir.name) / "openram"
symlink.symlink_to(Path({str(openram_root)!r}))
os.environ["OPENRAM_HOME"] = {str(compiler_root)!r}
os.environ["OPENRAM_TECH"] = {str(openram_root / 'technology')!r}
import sys
sys.path.insert(0, tmpdir.name)
import openram
openram.init_openram({str(config_path)!r}, is_unit_test=True)
from openram.modules.ptx import ptx
from openram.modules.pinv import pinv
from openram.base.contact import contact
ptx(width=0.09, tx_type="nmos")
pinv(name="pinv_test", size=1)
contact(layer_stack=("active", "contact", "m1"), dimensions=(1, 1))
print(json.dumps({{
  "ptx_signature": str(inspect.signature(ptx.__init__)),
  "pinv_signature": str(inspect.signature(pinv.__init__)),
  "contact_signature": str(inspect.signature(contact.__init__)),
  "ptx_import_passed": True,
  "pinv_import_passed": True,
  "contact_import_passed": True
}}))
"""
    proc = subprocess.run([sys.executable, "-c", script], text=True, capture_output=True)
    if proc.returncode != 0:
        return {
            "passed": False,
            "ptx_import_passed": False,
            "pinv_import_passed": False,
            "contact_import_passed": False,
            "ptx_signature": "",
            "pinv_signature": "",
            "contact_signature": "",
            "failure_reason": proc.stderr.strip() or proc.stdout.strip(),
        }
    payload = json.loads(proc.stdout.strip().splitlines()[-1])
    return {
        "passed": True,
        "failure_reason": "",
        **payload,
    }
