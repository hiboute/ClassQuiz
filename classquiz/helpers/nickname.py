# SPDX-License-Identifier: MPL-2.0
"""Player nickname validation and random friendly nicknames."""

import re
import secrets
import unicodedata

from classquiz.helpers.profanity import contains_profanity

NICKNAME_MIN_LENGTH = 2
NICKNAME_MAX_LENGTH = 20


class NicknameError(ValueError):
    """A nickname was refused. `code` is stable and meant for the frontend."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def _char_allowed(c: str) -> bool:
    """Letters (any script, with their combining accents), digits, space, - _ . ' (or ’)."""
    if c in " -_.'’":
        return True
    cat = unicodedata.category(c)
    return cat.startswith("L") or cat == "Nd" or cat.startswith("M")


def clean_nickname(raw: object) -> str:
    """Trim and validate a nickname; return the cleaned value or raise NicknameError."""
    if not isinstance(raw, str):
        raise NicknameError("invalid_type", "The nickname must be text.")
    # NFC so "é" typed as e + accent counts as one character.
    name = unicodedata.normalize("NFC", raw).strip()
    name = re.sub(r"\s+", " ", name)
    if len(name) < NICKNAME_MIN_LENGTH:
        raise NicknameError("too_short", f"The nickname must be at least {NICKNAME_MIN_LENGTH} characters.")
    if len(name) > NICKNAME_MAX_LENGTH:
        raise NicknameError("too_long", f"The nickname must be at most {NICKNAME_MAX_LENGTH} characters.")
    if not all(_char_allowed(c) for c in name):
        raise NicknameError(
            "invalid_characters",
            "The nickname may only contain letters, digits, spaces and - _ . '",
        )
    if not any(unicodedata.category(c).startswith("L") or unicodedata.category(c) == "Nd" for c in name):
        raise NicknameError("invalid_characters", "The nickname must contain a letter or a digit.")
    if contains_profanity(name):
        raise NicknameError("profanity", "Please choose another nickname.")
    return name


ADJECTIVES = (
    "Happy",
    "Brave",
    "Clever",
    "Swift",
    "Sunny",
    "Lucky",
    "Mighty",
    "Calm",
    "Bright",
    "Bold",
    "Cheerful",
    "Curious",
    "Daring",
    "Eager",
    "Fancy",
    "Gentle",
    "Jolly",
    "Kind",
    "Lively",
    "Merry",
    "Nimble",
    "Noble",
    "Plucky",
    "Quick",
    "Quiet",
    "Rapid",
    "Shiny",
    "Smart",
    "Snappy",
    "Speedy",
    "Spicy",
    "Steady",
    "Super",
    "Witty",
    "Zesty",
    "Cosmic",
    "Golden",
    "Silver",
    "Turbo",
    "Epic",
)
NOUNS = (
    "Panda",
    "Otter",
    "Falcon",
    "Tiger",
    "Koala",
    "Dolphin",
    "Fox",
    "Owl",
    "Penguin",
    "Rocket",
    "Comet",
    "Lynx",
    "Badger",
    "Beaver",
    "Bison",
    "Cheetah",
    "Eagle",
    "Gecko",
    "Hedgehog",
    "Jaguar",
    "Lemur",
    "Llama",
    "Moose",
    "Narwhal",
    "Octopus",
    "Parrot",
    "Puffin",
    "Raccoon",
    "Seal",
    "Squirrel",
    "Toucan",
    "Walrus",
    "Wombat",
    "Yak",
    "Zebra",
    "Meteor",
    "Pixel",
    "Wizard",
    "Ninja",
    "Captain",
)


def random_nickname() -> str:
    """Adjective + noun, e.g. "Swift Otter" (at most 20 characters, always valid)."""
    while True:
        name = f"{secrets.choice(ADJECTIVES)} {secrets.choice(NOUNS)}"
        if len(name) <= NICKNAME_MAX_LENGTH:
            return name
