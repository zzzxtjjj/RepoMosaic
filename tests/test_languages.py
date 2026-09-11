import pytest

from repoatlas.semantic.languages import (
    SUPPORTED_LANGUAGES,
    validate_language,
)


# 验证 RepoAtlas V0.1 支持预定的八种自然语言
def test_supported_languages():
    assert set(SUPPORTED_LANGUAGES) == {
        "zh-CN",
        "en",
        "ja",
        "ko",
        "de",
        "it",
        "pt",
        "es",
    }


# 验证受支持的语言代码能够正常通过检查
def test_validate_supported_language():
    assert validate_language("zh-CN") == "zh-CN"
    assert validate_language("en") == "en"
    assert validate_language("ja") == "ja"


# 验证不支持的语言会得到明确错误
def test_validate_unsupported_language():
    with pytest.raises(ValueError):
        validate_language("ru")