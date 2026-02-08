"""Test configuration - set env vars before any app imports."""

import os

# Override DATABASE_URL to use async sqlite for tests
# Must happen before any app module is imported
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./data/test.db"
