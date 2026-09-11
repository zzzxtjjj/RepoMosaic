# RepoAtlas V0.1 支持的自然语言及其显示名称
SUPPORTED_LANGUAGES = {
    "zh-CN": "Simplified Chinese",
    "en": "English",
    "ja": "Japanese",
    "ko": "Korean",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "es": "Spanish",
}


# 检查用户指定的语言是否受到 RepoAtlas 支持
def validate_language(language: str) -> str:
    if language not in SUPPORTED_LANGUAGES:
        supported = ", ".join(SUPPORTED_LANGUAGES)

        raise ValueError(
            f"Unsupported language: {language}. "
            f"Supported languages: {supported}"
        )

    return language