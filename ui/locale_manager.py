import json
import os

TRANSLATIONS_DIR = os.path.join(os.path.dirname(__file__), "translations")
DEFAULT_LOCALE = "ru"


class LocaleManager:
    _translations = {}
    _current_locale = DEFAULT_LOCALE
    _supported_locales = []

    @classmethod
    def init(cls, locale=None):
        cls._load_available_locales()
        locale = locale or DEFAULT_LOCALE
        if locale not in cls._supported_locales:
            locale = DEFAULT_LOCALE
        cls._current_locale = locale
        cls._load_translations()

    @classmethod
    def _load_available_locales(cls):
        cls._supported_locales = []
        if not os.path.exists(TRANSLATIONS_DIR):
            return
        for filename in os.listdir(TRANSLATIONS_DIR):
            if filename.endswith(".json"):
                locale = filename[:-5]
                cls._supported_locales.append(locale)
        cls._supported_locales.sort()

    @classmethod
    def _load_translations(cls):
        cls._translations = {}
        for locale in cls._supported_locales:
            json_file = os.path.join(TRANSLATIONS_DIR, f"{locale}.json")
            if os.path.exists(json_file):
                with open(json_file, encoding="utf-8") as f:
                    cls._translations[locale] = json.load(f)

    @classmethod
    def set_locale(cls, locale):
        if locale in cls._supported_locales:
            cls._current_locale = locale
            from utils.config import set_language

            set_language(locale)
            return True
        return False

    @classmethod
    def get_locale(cls):
        return cls._current_locale

    @classmethod
    def get_supported_locales(cls):
        return cls._supported_locales.copy()

    @classmethod
    def t(cls, key):
        translations = cls._translations.get(cls._current_locale, {})
        return translations.get(key, key)


locale_manager = LocaleManager()
