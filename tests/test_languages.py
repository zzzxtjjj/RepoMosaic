import pytest

from repomosaic.semantic.languages import (
    SUPPORTED_LANGUAGES,
    normalize_language,
    validate_language,
)


# 验证 RepoMosaic V0.1 支持预定的八种自然语言
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


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("EN", "en"),
        ("English", "en"),
        ("zh", "zh-CN"),
        ("ZH-CN", "zh-CN"),
        ("中文", "zh-CN"),
        ("简体中文", "zh-CN"),
        ("日本語", "ja"),
        ("日语", "ja"),
        ("Korean", "ko"),
        ("Deutsch", "de"),
        ("Italiano", "it"),
        ("Português", "pt"),
        ("Español", "es"),
        ("  English  ", "en"),
    ],
)
def test_normalize_language_aliases(value, expected):
    assert normalize_language(value) == expected


def test_normalize_language_error_lists_codes_and_names():
    with pytest.raises(ValueError) as caught:
        normalize_language("russian")

    message = str(caught.value)
    assert "Unsupported language: russian" in message
    for code, name in SUPPORTED_LANGUAGES.items():
        assert code in message
        assert name in message
