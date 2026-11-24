"""Split a full name into tokens and undo the structure of Arabic names.

Handled here, for Arabic, Latin and Hebrew script alike:

* the definite article, separate or attached, including sun-letter
  assimilation:  الرحمن · al-Rahman · ar-Rahman · Elrahman · אל-רחמן
* ``Abd`` compounds, which are *one* name however they are spaced:
  عبدالرحمن · عبد الرحمن · Abdul Rahman · Abdelrahman · Abdurrahman
* patronymic particles (bin / ibn / ben / bint / بن / ابن / בן)
* titles (Dr, Sheikh, الحاج ...), initials, "FAMILY, Given" order
* diacritics, tatweel, bidi marks, presentation forms, Persian letters
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache

from .phonemes import GERESH, clean_latin

__all__ = ["Token", "parse_name"]


@dataclass(frozen=True)
class Token:
    script: str               # 'ar' | 'he' | 'la'
    forms: tuple              # alternative readings; each one is a tuple of parts
    display: str              # the text as the user wrote it
    kind: str = "name"        # 'name' | 'initial'
    compound: bool = False    # an Abd-compound
    full: int = -1            # index of the form that still carries an attached article


_STRIP = re.compile(
    "[ً-ٰٟۖ-ۭـ"      # Arabic diacritics + tatweel
    "֑-ׇֽֿׁׂׅׄ"  # Hebrew niqqud
    "​-‏‪-‮⁦-⁩﻿]"     # zero width / bidi
)
_AR_MAP = str.maketrans({"ک": "ك", "ی": "ي", "ے": "ي", "ۀ": "ه", "ہ": "ه", "ھ": "ه", "ە": "ه"})
_WORD = re.compile(r"[^\s,;:/\\|()\[\]{}<>\"“”«»_\-–—.،؛]+")
_AR_LETTER = re.compile("[ء-يٮ-ۓ]")
_HE_LETTER = re.compile("[א-ת]")

_TITLES = {
    "la": {"dr", "mr", "mrs", "ms", "miss", "prof", "eng", "sheikh", "shaikh", "shaykh",
           "sheik", "cheikh", "haj", "hajj", "hadj", "hajji", "sayyida"},
    "ar": {"د", "م", "دكتور", "الدكتور", "دكتورة", "الدكتورة", "مهندس", "المهندس",
           "الشيخ", "الحاج", "الحاجة", "السيدة", "استاذ", "الاستاذ"},
    "he": {"דר", "מר"},
}
_ARTICLES = {"la": {"al", "el", "il", "ul", "l"}, "ar": {"ال"}, "he": {"אל", "א"}}
_ASSIMILATED = {
    "as": "s", "es": "s", "ash": "sh", "esh": "sh", "ad": "d", "ed": "d", "adh": "dh",
    "an": "n", "en": "n", "ar": "r", "er": "r", "at": "t", "et": "t", "ath": "th",
    "az": "z", "ez": "z",
}
_PARTICLES = {
    "la": {"bin", "ibn", "ben", "bn", "bint", "bent", "binti", "binte", "bnt", "ould"},
    "ar": {"بن", "ابن", "بنت", "ولد"},
    "he": {"בן", "אבן", "בת"},
}
_ALIASES = {"mohd": "muhammad", "muhd": "muhammad", "md": "muhammad", "mhd": "muhammad",
            "mhmd": "muhammad", "mohmd": "muhammad",
            # Turkish forms of the same names
            "mehmet": "muhammad", "mehmed": "muhammad", "ahmet": "ahmad"}

_ALLAH_AR = {"الله", "اللة", "لله"}
_ALLAH_HE = {"אללה", "אלה", "ללה", "אלל", "אללא"}
_ALEF_FOLD = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا"})

_ABD_LINK = re.compile(r"(?:a|e|u|o|ou)(l|r|sh|s|n|z|dh|d|th|t)")
_ABUL = re.compile(r"ab(?:u|ou|o|i)l(.*)".replace("(.*)", "()(.*)"))
_ABD_ALLAH = re.compile(r"l?[aeo]?h?")
_SUN_ATTACHED = re.compile(r"^[ae](?:(sh)sh|([sdnrtz])\2)")


def _script(word: str) -> str:
    if _AR_LETTER.search(word):
        return "ar"
    if _HE_LETTER.search(word):
        return "he"
    return "la"


def _clean(word: str, script: str) -> str:
    if script == "ar":
        return "".join(c for c in word.translate(_AR_MAP) if _AR_LETTER.match(c))
    if script == "he":
        word = word.replace("'", GERESH).replace("’", GERESH).replace("`", GERESH)
        return "".join(c for c in word if _HE_LETTER.match(c) or c == GERESH)
    return clean_latin(word)


def _strip_article(text: str, script: str) -> str:
    """Remove an attached article if the remainder is still a plausible name."""
    if script == "ar":
        if text.translate(_ALEF_FOLD) in _ALLAH_AR:
            return "الله"
        if text.startswith("ال") and len(text) >= 4:
            return text[2:]
    elif script == "he":
        if text in _ALLAH_HE:
            return "אללה"
        if text.startswith("אל") and len(text) >= 4:
            return text[2:]
    return text


def _abd_latin(tok: str):
    """Classify a Latin token starting with "abd".

    Returns ``None`` (not a compound), ``("link", consonant)`` when the second
    half is the next token, or ``("joined", second_half)``.
    """
    r = tok[3:]
    if r == "":
        return ("link", "")
    m = _ABD_LINK.fullmatch(r)
    if m:
        return ("link", m.group(1))
    if re.fullmatch(r"[aeiou]+", r):
        return None  # Abdu, Abdo, Abdi, Abdou are names in their own right
    x = re.sub(r"^[aeiou]{1,2}", "", r)
    if x != r and x.startswith("l"):
        x = x[1:]
        if _ABD_ALLAH.fullmatch(x):
            return ("joined", "allah")
    if len(x) < 3:
        return None
    return ("joined", x)


@lru_cache(maxsize=20_000)
def parse_name(text: str) -> tuple:
    """Parse a full name into a tuple of :class:`Token`."""
    text = unicodedata.normalize("NFKC", text)
    text = _STRIP.sub("", text)
    for comma in (",", "،"):
        if text.count(comma) == 1:   # "FAMILY, Given names"
            family, given = text.split(comma)
            if family.strip() and given.strip():
                text = given + " " + family
            break

    words = []
    for m in _WORD.finditer(text):
        raw = m.group(0)
        script = _script(raw)
        cleaned = _clean(raw, script)
        if cleaned:
            words.append((script, cleaned, raw))

    # titles go first, but never leave the name empty
    kept = [w for w in words if w[1] not in _TITLES[w[0]]]
    if kept:
        words = kept

    tokens = []
    n = len(words)
    i = 0
    had_article = False
    while i < n:
        script, text_, raw = words[i]
        nxt = words[i + 1] if i + 1 < n else None

        # --- separate article ------------------------------------------------
        if nxt is not None and nxt[0] == script:
            if text_ in _ARTICLES[script]:
                had_article = True
                i += 1
                continue
            if script == "la" and text_ in _ASSIMILATED and nxt[1].startswith(_ASSIMILATED[text_]):
                had_article = True
                i += 1
                continue
            # --- patronymic particle: carries no identity -------------------
            if text_ in _PARTICLES[script] and tokens:
                i += 1
                continue

        # --- Abd compounds ---------------------------------------------------
        second = None
        consumed = 1
        if script == "la" and text_.startswith("abd"):
            kind = _abd_latin(text_)
            if kind and kind[0] == "joined":
                second = kind[1]
            elif kind and nxt is not None and nxt[0] == "la":
                j = i + 1
                link = kind[1]
                if words[j][1] in _ARTICLES["la"] and j + 1 < n:
                    j += 1
                    link = ""
                cand = words[j][1]
                if link in ("", "l") or cand.startswith(link):
                    if link in ("", "l") and (cand.startswith(("al", "el")) and len(cand) >= 5
                                               and text_ == "abd"):
                        cand = cand[2:]
                    second = "allah" if re.fullmatch(r"[aeu]?l+a+h?", cand) else cand
                    consumed = j - i + 1
                    raw = " ".join(w[2] for w in words[i:j + 1])
        elif script in ("ar", "he") and text_.startswith("עבד" if script == "he" else "عبد"):
            rest = text_[3:]
            art = "אל" if script == "he" else "ال"
            allah = _ALLAH_HE if script == "he" else _ALLAH_AR
            if rest == "" and nxt is not None and nxt[0] == script:
                j = i + 1
                explicit = False
                if words[j][1] in _ARTICLES[script] and j + 1 < n:
                    j += 1
                    explicit = True
                cand = words[j][1]
                stripped = _strip_article(cand, script)
                if explicit or stripped != cand or cand.translate(_ALEF_FOLD) in allah:
                    second = stripped
                    consumed = j - i + 1
                    raw = " ".join(w[2] for w in words[i:j + 1])
            elif rest.translate(_ALEF_FOLD) in allah:
                second = "אללה" if script == "he" else "الله"
            elif rest.startswith(art) and len(rest) >= 4:
                second = rest[2:]
            elif rest in ("ربه", "رب"):
                second = rest

        if second is not None:
            head = "abd" if script == "la" else text_[:3]
            tokens.append(Token(script, ((head, second),), raw, "name", True))
            had_article = False
            i += consumed
            continue

        # --- Abul / Aboul = Abu + article ------------------------------------
        abul = _ABUL.fullmatch(text_) if script == "la" else None
        if abul and not abul.group(2) and nxt is not None and nxt[0] == "la":
            tokens.append(Token("la", (("abu",),), raw))
            had_article = True
            i += 1
            continue

        # --- ordinary token --------------------------------------------------
        if script == "la":
            text_ = _ALIASES.get(text_, text_)
        if len(text_) == 1 and script != "he" and n > 1:
            tokens.append(Token(script, ((text_,),), raw, "initial"))
        else:
            forms = [(text_,)]
            full = -1
            if not had_article:
                if script == "la":
                    if text_.startswith(("al", "el")) and len(text_) >= 5:
                        forms.append((text_[2:],))
                        full = 0
                    elif abul and len(abul.group(2)) >= 3:
                        forms.append(("abu", abul.group(2)))
                    else:
                        m = _SUN_ATTACHED.match(text_)
                        if m and len(text_) >= 6:
                            forms.append((text_[2:] if not m.group(1) else text_[3:],))
                else:
                    bare = _strip_article(text_, script)
                    if bare != text_:
                        forms.insert(0, (bare,))
                        full = 1
                    else:
                        # article written inside the word: نورالدين = نور + الدين
                        art = "אל" if script == "he" else "ال"
                        k = text_.find(art, 2)
                        if k >= 2:
                            rest = _strip_article(text_[k:], script)
                            if rest != text_[k:] and len(rest) >= 3:
                                forms.append((text_[:k], rest))
            tokens.append(Token(script, tuple(forms), raw, "name", False, full))
        had_article = False
        i += 1
    return tuple(tokens)
