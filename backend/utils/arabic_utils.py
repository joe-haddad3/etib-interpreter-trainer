"""
Arabic Language Utilities
==========================
Helper functions for Arabic text processing used across all modules.

Arabic is the primary language of this project and its primary challenge.
All Arabic-specific handling lives here so it is easy to find and improve.

Reference: Cahier des charges — "La spécificité de cet outil réside dans la
prise en charge des différentes tâches en langue arabe"
"""
import re


def is_arabic_text(text: str) -> bool:
    """Return True if the text contains Arabic characters."""
    arabic_range = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+')
    return bool(arabic_range.search(text))


def count_arabic_words(text: str) -> int:
    """
    Count words in Arabic text.
    Arabic tokenization is non-trivial — this is a simple whitespace split.
    For production use, consider using CAMeL Tools.
    """
    return len(text.strip().split())


def remove_diacritics(text: str) -> str:
    """
    Remove Arabic diacritics (تشكيل / harakat) from text.
    Useful for normalization before comparison.
    Diacritics range: U+064B – U+065F
    """
    diacritics_pattern = re.compile(r'[\u064B-\u065F\u0670]')
    return diacritics_pattern.sub('', text)


def normalize_arabic(text: str) -> str:
    """
    Normalize common Arabic character variants for comparison.
    - ا أ إ آ → ا
    - ة → ه
    - ى → ي
    Also removes diacritics.
    """
    text = remove_diacritics(text)
    text = re.sub(r'[أإآ]', 'ا', text)
    text = re.sub(r'ة', 'ه', text)
    text = re.sub(r'ى', 'ي', text)
    return text


def extract_arabic_numbers(text: str) -> list:
    """
    Extract numbers written in Arabic-Indic numerals (٠١٢٣٤٥٦٧٨٩)
    and convert them to Western numerals for comparison.
    """
    arabic_indic = {'٠':'0','١':'1','٢':'2','٣':'3','٤':'4',
                    '٥':'5','٦':'6','٧':'7','٨':'8','٩':'9'}
    # Find Arabic-Indic number sequences
    pattern = re.compile(r'[٠-٩]+')
    results = []
    for match in pattern.finditer(text):
        arabic_num = match.group()
        western_num = ''.join(arabic_indic.get(c, c) for c in arabic_num)
        results.append({'arabic': arabic_num, 'western': western_num})
    return results


def detect_language_mixing(text: str) -> dict:
    """
    Detect if the text mixes Arabic with Latin-script languages.
    Common in Lebanese Arabic (code-switching with French/English).
    Returns counts of Arabic and Latin word segments.
    """
    arabic_words = re.findall(r'[\u0600-\u06FF]+', text)
    latin_words = re.findall(r'[a-zA-Z]+', text)
    return {
        'arabic_word_count': len(arabic_words),
        'latin_word_count': len(latin_words),
        'mixing_ratio': round(len(latin_words) / max(len(arabic_words), 1), 3),
        'has_mixing': len(latin_words) > 0 and len(arabic_words) > 0
    }
