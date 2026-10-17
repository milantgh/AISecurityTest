# -*- coding: utf-8 -*-
"""
Generic loader: safely scan directories and load Python modules or YAML files.
Shared by registry (cases) and plugins (future extensions).
"""
import importlib
import pkgutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def discover_python_modules(pkg) -> List[str]:
    """List all module names in the package that do not start with underscore (excluding subpackages)."""
    names = []
    for _, name, is_pkg in pkgutil.iter_modules(pkg.__path__):
        if is_pkg or name.startswith("_"):
            continue
        names.append(name)
    return sorted(names)


def safe_import(module_path: str) -> Tuple[Optional[Any], Optional[str]]:
    """Safely import a module, returns (module, error)."""
    try:
        return importlib.import_module(module_path), None
    except SyntaxError as e:
        return None, "Syntax error: %s" % e
    except ImportError as e:
        return None, "Import failed: %s" % e
    except Exception as e:
        return None, "Load error: %s: %s" % (type(e).__name__, e)


def load_yaml(path: Path) -> Tuple[Optional[Dict], Optional[str]]:
    """Load one YAML file."""
    if not HAS_YAML:
        return None, "PyYAML not installed, cannot load YAML cases"
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if data is None:
            return None, "File is empty"
        if not isinstance(data, dict):
            return None, "YAML top level must be dict, got %s" % type(data).__name__
        return data, None
    except yaml.YAMLError as e:
        return None, "YAML parse error: %s" % e
    except Exception as e:
        return None, "Read failed: %s: %s" % (type(e).__name__, e)


def discover_yaml_files(directory: Path, skip_prefix: str = "_") -> List[Path]:
    """List all .yaml/.yml files under a directory, recursively.

    Files whose name starts with `skip_prefix` are skipped. Directories
    starting with `skip_prefix` (e.g. `_legacy/`) are also skipped.
    Recursion is needed because the case library is organized as
    one-directory-per-category (direct/, indirect/, encoded/, ...).
    """
    if not directory.is_dir():
        return []
    files = []
    for p in sorted(directory.rglob("*")):
        if not p.is_file():
            continue
        # Skip files/dirs under any path component starting with skip_prefix.
        if any(part.startswith(skip_prefix) for part in p.relative_to(directory).parts):
            continue
        if p.suffix.lower() not in (".yaml", ".yml"):
            continue
        files.append(p)
    return files