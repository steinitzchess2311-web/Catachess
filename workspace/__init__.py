"""
Workspace package shim for tests.

Aliases `modules.workspace` to `workspace` to avoid duplicate imports.
"""
from __future__ import annotations

import importlib
import sys

_BASE = "modules.workspace"
_workspace = importlib.import_module(_BASE)

# Preload common subpackages used by tests to avoid duplicate table definitions.
for sub in [
    "db",
    "db.tables",
    "db.repos",
    "domain",
    "events",
    "storage",
    "api",
    "pgn",
    "collaboration",
]:
    try:
        importlib.import_module(f"{_BASE}.{sub}")
    except Exception:
        pass

# Map modules.workspace.* -> workspace.*
for name, module in list(sys.modules.items()):
    if name == _BASE or name.startswith(f"{_BASE}."):
        alias = "workspace" + name[len(_BASE):]
        sys.modules.setdefault(alias, module)

# Expose attributes from modules.workspace
globals().update(_workspace.__dict__)
