# RepoAtlas V0.1 支持的自然语言及其显示名称
SUPPORTED_LANGUAGES = {
    "en": "English",
    "zh-CN": "简体中文",
    "ja": "日本語",
    "ko": "한국어",
    "de": "Deutsch",
    "it": "Italiano",
    "pt": "Português",
    "es": "Español",
}


_LANGUAGE_ALIASES = {
    "en": ("english",),
    "zh-CN": ("zh", "chinese", "simplified chinese", "中文", "简体中文"),
    "ja": ("japanese", "日本語", "日语"),
    "ko": ("korean", "한국어", "韩语"),
    "de": ("german", "deutsch", "德语"),
    "it": ("italian", "italiano", "意大利语"),
    "pt": ("portuguese", "português", "葡萄牙语"),
    "es": ("spanish", "español", "西班牙语"),
}


def format_supported_languages() -> str:
    """生成包含 canonical code 和可读名称的帮助文字。"""
    return "\n".join(
        f"  {code:<5}  {name}"
        for code, name in SUPPORTED_LANGUAGES.items()
    )


def _unsupported_language_error(language: str) -> ValueError:
    value = language.strip()
    return ValueError(
        f"Unsupported language: {value}\n\n"
        f"Supported languages:\n{format_supported_languages()}"
    )


def normalize_language(language: str) -> str:
    """把常见语言代码或名称规范化为 RepoAtlas canonical code。"""
    normalized = language.strip().casefold()

    aliases = {
        code.casefold(): code
        for code in SUPPORTED_LANGUAGES
    }
    for code, names in _LANGUAGE_ALIASES.items():
        aliases.update(
            (name.casefold(), code)
            for name in names
        )

    try:
        return aliases[normalized]
    except KeyError as error:
        raise _unsupported_language_error(language) from error


# 检查用户指定的语言是否受到 RepoAtlas 支持
def validate_language(language: str) -> str:
    if language not in SUPPORTED_LANGUAGES:
        raise _unsupported_language_error(language)

    return language
