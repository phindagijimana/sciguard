"""A pip install must find schema/contracts/rules without a source checkout."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

import validation.check as check

ROOT = Path(__file__).resolve().parents[1]


def test_source_checkout_uses_repo_data() -> None:
    assert check.SCHEMA_PATH.is_file()
    assert (check.CONTRACTS_DIR / "map_labels_to_diffusion.yaml").is_file()
    assert (check.RULES_DIR / "RULE-SPACE-002.yaml").is_file()


def test_env_override_points_at_data(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SCIGUARD_DATA", str(ROOT))
    reloaded = importlib.reload(check)
    try:
        assert reloaded.DATA_ROOT == ROOT
        assert reloaded.SCHEMA_PATH.is_file()
    finally:
        monkeypatch.delenv("SCIGUARD_DATA")
        importlib.reload(check)


def test_pyproject_ships_data_packages() -> None:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    for name in ("sciguard_data.schema", "sciguard_data.contracts", "sciguard_data.rules"):
        assert f'"{name}"' in text
    assert (ROOT / "sciguard_data" / "__init__.py").is_file()
