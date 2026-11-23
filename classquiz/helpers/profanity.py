# SPDX-License-Identifier: MPL-2.0
"""Small FR + EN profanity filter for player nicknames.

Nicknames are shown on the big screen at a live event, so the goal is to stop
the obvious cases, not to be a complete moderation system. A nickname is
normalised (case, accents, leetspeak, separators) and then checked:

* every word of the nickname against the list (exact word match), and
* the nickname with all separators removed against the longer entries
  (substring match), so "f.u.c.k" or "grosCONnard" are caught too.

Short entries (4 letters or fewer) are only matched as whole words to avoid
flagging innocent names ("Scunthorpe problem"): "con" must not block "Conrad".
"""

import re
import unicodedata

_LEET = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "@": "a", "$": "s", "7": "t", "!": "i"})

# Kept deliberately small and obvious. Entries are written already normalised
# (lowercase, no accents).
PROFANITY_WORDS: frozenset[str] = frozenset(
    {
        # English
        "fuck",
        "fucker",
        "fucking",
        "motherfucker",
        "shit",
        "bullshit",
        "bitch",
        "bastard",
        "asshole",
        "dick",
        "dickhead",
        "cock",
        "cunt",
        "pussy",
        "whore",
        "slut",
        "wanker",
        "twat",
        "nigger",
        "nigga",
        "faggot",
        "fag",
        "retard",
        "porn",
        "rape",
        "rapist",
        "nazi",
        "hitler",
        "penis",
        "vagina",
        # French
        "merde",
        "putain",
        "pute",
        "salope",
        "salaud",
        "connard",
        "connasse",
        "con",
        "conne",
        "encule",
        "enculer",
        "batard",
        "bite",
        "couille",
        "couilles",
        "chatte",
        "nique",
        "niquer",
        "ntm",
        "fdp",
        "pd",
        "pede",
        "tapette",
        "branleur",
        "branleuse",
        "bordel",
        "foutre",
        "negre",
        "bougnoule",
        "pouffiasse",
        "trouduc",
        "enfoire",
        "cul",
        "zizi",
    }
)

# Words that are part of common innocent names ("Dominique", "Bordelais") are
# only matched as whole words.
_WHOLE_WORD_ONLY = frozenset({"nique", "bordel"})

# Long enough to be matched inside other text without many false positives.
_SUBSTRING_WORDS = tuple(sorted(w for w in PROFANITY_WORDS if len(w) >= 5 and w not in _WHOLE_WORD_ONLY))


def normalize(text: str) -> str:
    """Lowercase, strip accents and undo common leetspeak."""
    text = text.casefold().translate(_LEET)
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c))


def _collapse_repeats(text: str) -> str:
    """'fuuuuck' -> 'fuck' (any run of the same letter becomes one)."""
    return re.sub(r"(.)\1+", r"\1", text)


def contains_profanity(text: str) -> bool:
    norm = normalize(text)
    words = [w for w in re.split(r"[^a-z]+", norm) if w]
    for w in words:
        if w in PROFANITY_WORDS or _collapse_repeats(w) in PROFANITY_WORDS:
            return True
    joined = "".join(words)
    collapsed = _collapse_repeats(joined)
    for bad in _SUBSTRING_WORDS:
        if bad in joined or bad in collapsed:
            return True
    # Spelled-out short words: "c o n", "p.d" -> single-letter tokens joined.
    if len(words) > 1 and all(len(w) == 1 for w in words) and joined in PROFANITY_WORDS:
        return True
    return False
