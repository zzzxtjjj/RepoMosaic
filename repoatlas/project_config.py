"""Load and create RepoAtlas's local project configuration."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import tomllib

from repoatlas.semantic.languages import SUPPORTED_LANGUAGES


CONFIG_FILENAME = ".repoatlas.toml"
DEFAULT_PROVIDER = "openai-compatible"
DEFAULT_LANGUAGE = "en"

_LANGUAGE_TEMPLATE_LINES = "\n".join(
    f"#   {code:<5} = {name}"
    for code, name in SUPPORTED_LANGUAGES.items()
)


CONFIG_TEMPLATE = f"""# RepoAtlas project configuration
# Use `repoatlas auth set` or REPOATLAS_API_KEY; never put API keys in this file.

[llm]
provider = "openai-compatible"
model = ""
base_url = ""
# Output language.
# Supported values:
{_LANGUAGE_TEMPLATE_LINES}
language = "en"
"""


class ProjectConfigError(ValueError):
    """Raised when a local RepoAtlas configuration is invalid."""


@dataclass(frozen=True)
class ProjectConfig:
    provider: str | None = None
    model: str | None = None
    base_url: str | None = None
    language: str | None = None


def write_project_config(directory: Path, *, force: bool = False) -> Path:
    """Create a safe, human-editable configuration template."""
    config_path = directory / CONFIG_FILENAME

    if config_path.exists() and not force:
        raise FileExistsError(
            f"{config_path} already exists; use --force to overwrite it."
        )

    config_path.write_text(CONFIG_TEMPLATE, encoding="utf-8")
    return config_path


def write_project_config_values(
    directory: Path,
    *,
    model: str,
    base_url: str,
    language: str,
    force: bool = False,
) -> Path:
    """写入交互式初始化收集到的精简项目配置。"""
    config_path = directory / CONFIG_FILENAME

    if config_path.exists() and not force:
        raise FileExistsError(
            f"{config_path} already exists; use --force to overwrite it."
        )

    content = "\n".join(
        [
            "[llm]",
            f'provider = {json.dumps(DEFAULT_PROVIDER, ensure_ascii=False)}',
            f'model = {json.dumps(model.strip(), ensure_ascii=False)}',
            f'base_url = {json.dumps(base_url.strip(), ensure_ascii=False)}',
            f'language = {json.dumps(language, ensure_ascii=False)}',
            "",
        ]
    )
    config_path.write_text(content, encoding="utf-8")
    return config_path


def load_project_config(directory: Path) -> ProjectConfig:
    """Load configuration from *directory*, or return an empty configuration."""
    config_path = directory / CONFIG_FILENAME

    if not config_path.is_file():
        return ProjectConfig()

    try:
        data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as error:
        raise ProjectConfigError(f"cannot read {config_path}: {error}") from error

    llm = data.get("llm", {})
    if not isinstance(llm, dict):
        raise ProjectConfigError("[llm] must be a TOML table.")

    if "api_key" in llm or "api-key" in llm:
        raise ProjectConfigError(
            "API keys are not allowed in .repoatlas.toml; "
            "use `repoatlas auth set` or REPOATLAS_API_KEY instead."
        )

    values: dict[str, str | None] = {}
    for key in ("provider", "model", "base_url", "language"):
        value = llm.get(key)
        if value is not None and not isinstance(value, str):
            raise ProjectConfigError(f"llm.{key} must be a string.")
        values[key] = (value.strip() or None) if value is not None else None

    return ProjectConfig(**values)
