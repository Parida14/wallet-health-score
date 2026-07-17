"""Pytest configuration for the etl test suite.

Adds ``etl/src`` to ``sys.path`` so ``from wallet_etl...`` imports resolve
without packaging boilerplate. Mirrors ``api/tests/conftest.py``.
"""
from __future__ import annotations

import sys
from pathlib import Path

ETL_SRC = Path(__file__).resolve().parent.parent / "src"
if str(ETL_SRC) not in sys.path:
    sys.path.insert(0, str(ETL_SRC))
