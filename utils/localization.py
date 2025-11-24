import json
import os
from typing import Dict

class Localizer:
    def __init__(self, locales_dir: str = "locales", default_lang: str = "en"):
        self.locales_dir = locales_dir
        self.default_lang = default_lang
        self.translations: Dict[str, Dict[str, str]] = {}
        self.load_translations()

    def load_translations(self):
        """Loads all translation files from the locales directory."""
        for filename in os.listdir(self.locales_dir):
            if filename.endswith(".json"):
                lang_code = filename.split(".")[0]
                filepath = os.path.join(self.locales_dir, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    self.translations[lang_code] = json.load(f)

    def get_text(self, key: str, lang: str) -> str:
        """
        Gets a translated string for a given key and language.
        Falls back to the default language if the key is not found for the requested language.
        """
        lang_dict = self.translations.get(lang, {})
        text = lang_dict.get(key)

        if text is None:
            lang_dict = self.translations.get(self.default_lang, {})
            text = lang_dict.get(key)

        return text if text is not None else key

translator = Localizer()
