import importlib.util
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / ".claude" / "scripts"


def _load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS_DIR / filename)
    assert spec is not None, f"Could not find {SCRIPTS_DIR / filename}"
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def pytest_configure():
    """Load law_db, law_db_lookup, law_db_query, and utils
    as importable modules."""
    _load_module("law_db", "law-db.py")
    _load_module("law_db_lookup", "law-db-lookup.py")
    _load_module("law_db_query", "law-db-query.py")
    _load_module("utils", "utils.py")
