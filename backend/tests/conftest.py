"""Test configuration - set env vars before any app imports."""

import os
from pathlib import Path

# Override DATABASE_URL to use async sqlite for tests
# Must happen before any app module is imported
Path("./data").mkdir(parents=True, exist_ok=True)
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./data/test.db"
