from pathlib import Path

import pytest

from repoatlas.project_config import (
    CONFIG_FILENAME,
    ProjectConfigError,
    load_project_config,
    write_project_config,
)
from repoatlas.semantic.languages import SUPPORTED_LANGUAGES


def test_init_template_excludes_api_key(tmp_path: Path):
    config_path = write_project_config(tmp_path)
    content = config_path.read_text(encoding="utf-8")

    assert config_path.name == CONFIG_FILENAME
    assert 'provider = "openai-compatible"' in content
    assert 'model = ""' in content
    assert 'base_url = ""' in content
    assert 'language = "en"' in content
    assert "api_key =" not in content
    assert "# Output language." in content
    assert "# Supported values:" in content
    for code, name in SUPPORTED_LANGUAGES.items():
        assert code in content
        assert name in content


def test_init_refuses_overwrite_without_force(tmp_path: Path):
    config_path = tmp_path / CONFIG_FILENAME
    config_path.write_text("original\n", encoding="utf-8")

    with pytest.raises(FileExistsError):
        write_project_config(tmp_path)

    assert config_path.read_text(encoding="utf-8") == "original\n"


def test_init_force_overwrites_existing_config(tmp_path: Path):
    config_path = tmp_path / CONFIG_FILENAME
    config_path.write_text("original\n", encoding="utf-8")

    write_project_config(tmp_path, force=True)

    assert "[llm]" in config_path.read_text(encoding="utf-8")


def test_load_project_config(tmp_path: Path):
    (tmp_path / CONFIG_FILENAME).write_text(
        """[llm]
provider = "custom"
model = "test-model"
base_url = "https://example.test/v1"
language = "zh-CN"
""",
        encoding="utf-8",
    )

    config = load_project_config(tmp_path)

    assert config.provider == "custom"
    assert config.model == "test-model"
    assert config.base_url == "https://example.test/v1"
    assert config.language == "zh-CN"


def test_config_rejects_api_key(tmp_path: Path):
    (tmp_path / CONFIG_FILENAME).write_text(
        '[llm]\napi_key = "secret"\n',
        encoding="utf-8",
    )

    with pytest.raises(ProjectConfigError, match="REPOATLAS_API_KEY"):
        load_project_config(tmp_path)
