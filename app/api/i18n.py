import json
from pathlib import Path

from fastapi import APIRouter, HTTPException


router = APIRouter(prefix="/i18n", tags=["i18n"])


LOCALES_DIR = Path(__file__).resolve().parent.parent / "locales"
ALLOWED_LANGS = {"en", "ru", "ar"}


def load_locale(lang: str) -> dict:
    code = lang.lower()
    print("Check language code for /api/v1/i18n/{lang}")
    print(code)
    if code not in ALLOWED_LANGS:
        print("Language code is not allowed")
        code = "en"
    locale_file = LOCALES_DIR / f"{code}.json"
    if not locale_file.exists():
        print("Files not found", locale_file)
        raise HTTPException(status_code=404, detail="Locale not found")
    with locale_file.open(encoding="utf-8") as f:
        return json.load(f)


@router.get("/{lang}", response_model=dict)
async def get_translations(lang: str):
    """
    Return UI translations for the given language code.
    """
    return load_locale(lang)


I18N_CACHE: dict[str, dict] = {}
BASE_DIR = Path(__file__).resolve().parent.parent
I18N_PATH = BASE_DIR / "locales"

def load_i18n(lang: str) -> dict:
    if lang in I18N_CACHE:
        return I18N_CACHE[lang]

    file_path = I18N_PATH / f"{lang}.json"
    if not file_path.exists():
        file_path = I18N_PATH / "en.json"

    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    I18N_CACHE[lang] = data
    return data
