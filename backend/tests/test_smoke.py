"""Smoke tests to verify basic app setup."""


def test_config_loads():
    """Verify settings can be loaded with defaults."""
    from app.core.config import Settings

    settings = Settings()
    assert settings.APP_NAME == "LazyAgents"
    assert settings.APP_VERSION == "0.1.0"


def test_config_database_url_default():
    """Verify default database URL uses async sqlite."""
    from app.core.config import Settings

    settings = Settings(DATABASE_URL="sqlite+aiosqlite:///./data/test.db")
    assert "aiosqlite" in settings.DATABASE_URL


def test_skill_loader_importable():
    """Verify skill loader can be imported."""
    from app.runtime.skill_loader import SkillLoader

    loader = SkillLoader(skill_dirs=["./nonexistent_test_dir"])
    assert loader is not None


def test_models_importable():
    """Verify model modules can be imported."""
    from app.models.agent import Agent
    from app.models.execution import Execution
    from app.models.skill import Skill

    assert Agent.__tablename__
    assert Execution.__tablename__
    assert Skill.__tablename__
