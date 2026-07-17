"""Pytest configuration for the api test suite.

Adds the api/ directory to sys.path so `from app.main import ...` works
without packaging boilerplate.
"""
from __future__ import annotations

import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parent.parent
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))
