import json
import os
from typing import Any

LOCALES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "locales")
SUPPORTED_LANGUAGES = ["ru", "en", "kg", "kz", "uz"]
DEFAULT_LANGUAGE = "ru"

_translations: dict[str, dict[str, str]] = {}


def _load_translations() -> None:
    for lang in SUPPORTED_LANGUAGES:
        path = os.path.join(LOCALES_DIR, f"{lang}.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                _translations[lang] = json.load(f)


_load_translations()


def get_text(key: str, lang: str = DEFAULT_LANGUAGE, **kwargs: Any) -> str:
    if lang not in _translations:
        lang = DEFAULT_LANGUAGE
    translations = _translations.get(lang, _translations.get(DEFAULT_LANGUAGE, {}))
    text = translations.get(key, _translations.get(DEFAULT_LANGUAGE, {}).get(key, key))
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    return text


class I18n:
    def __call__(self, key: str, lang: str = DEFAULT_LANGUAGE, **kwargs: Any) -> str:
        return get_text(key, lang, **kwargs)


i18n = I18n()
