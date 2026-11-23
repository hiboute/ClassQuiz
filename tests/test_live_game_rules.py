# SPDX-License-Identifier: MPL-2.0
"""Pure unit tests of the live game rules: no Postgres, no Redis server.

Run with: python -m pytest tests/test_live_game_rules.py
(Kept outside classquiz/tests, whose package __init__ builds the whole app
against Postgres.) Importing classquiz still needs the settings env, set here.
"""

import os
import tempfile

for _k, _v in {
    "mail_address": "test@example.com",
    "mail_password": "x",
    "mail_username": "x",
    "mail_server": "localhost",
    "mail_port": "25",
    "secret_key": "test-secret",
    "storage_backend": "local",
    "storage_path": tempfile.gettempdir(),
}.items():
    os.environ.setdefault(_k, _v)

import pytest  # noqa: E402
from pydantic import ValidationError  # noqa: E402

from classquiz.db.models import QuestionPoints, QuizQuestion  # noqa: E402
from classquiz.helpers.nickname import NicknameError, clean_nickname, random_nickname  # noqa: E402
from classquiz.helpers.profanity import contains_profanity  # noqa: E402
from classquiz.socket_server.models import JoinGameData  # noqa: E402
from classquiz.socket_server.scoring import (  # noqa: E402
    base_points_for,
    build_podium,
    build_rank_updates,
    calculate_score,
    streak_bonus,
)

# --- calculate_score ---


def test_instant_answer_gets_max():
    assert calculate_score(0, 20) == 1000
    assert calculate_score(499, 20) == 1000


def test_curve():
    # t = T/2 -> 1000 * (1 - 0.25) = 750
    assert calculate_score(10_000, 20) == 750
    # t = T -> 500
    assert calculate_score(20_000, 20) == 500
    assert calculate_score(5_000, "20") == 875


def test_clamped_and_never_negative():
    assert calculate_score(60_000, 20) == 500  # late answer floors at base/2
    assert calculate_score(-300, 20) == 1000
    assert calculate_score(10_000, 0) == 1000  # no time limit
    assert calculate_score(10_000, 20, base=0) == 0


def test_double_points():
    assert calculate_score(0, 20, base=2000) == 2000
    assert calculate_score(10_000, 20, base=2000) == 1500
    assert calculate_score(40_000, 20, base=2000) == 1000


def test_points_setting():
    assert base_points_for("standard") == 1000
    assert base_points_for(QuestionPoints.DOUBLE) == 2000
    assert base_points_for("none") == 0
    assert base_points_for(None) == 1000


def test_question_points_field_is_optional():
    q = QuizQuestion(question="?", time="20", answers=[{"right": True, "answer": "a"}])
    assert q.points == QuestionPoints.STANDARD
    assert (
        QuizQuestion(question="?", time="20", answers=[{"right": True, "answer": "a"}], points=None).points
        == "standard"
    )
    assert (
        QuizQuestion(question="?", time="20", answers=[{"right": True, "answer": "a"}], points="DOUBLE").points
        == "double"
    )
    assert q.model_dump(mode="json")["points"] == "standard"


# --- streak bonus ---


def test_streak_bonus():
    assert streak_bonus(0) == 0
    assert streak_bonus(1) == 0
    assert streak_bonus(2) == 100
    assert streak_bonus(3) == 200
    assert streak_bonus(6) == 500
    assert streak_bonus(20) == 500
    assert streak_bonus(5, base=0) == 0  # question awards no points


# --- leaderboard ---


def test_rank_updates():
    scores = {"ann": 2500, "bob": 1800, "cid": 1800, "dan": 0}
    top5, updates = build_rank_updates(scores, {"ann": 900, "bob": 0}, {"ann": 3})
    assert [p["username"] for p in top5] == ["ann", "bob", "cid", "dan"]
    assert top5[0] == {"username": "ann", "score": 2500, "gained": 900}
    assert updates["ann"] == {
        "rank": 1,
        "total_players": 4,
        "total": 2500,
        "gained": 900,
        "streak": 3,
        "behind_username": None,
        "behind_gap": None,
    }
    assert updates["bob"]["behind_username"] == "ann" and updates["bob"]["behind_gap"] == 700
    assert updates["cid"]["rank"] == 3 and updates["cid"]["behind_gap"] == 0
    assert updates["dan"]["gained"] == 0 and updates["dan"]["streak"] == 0


def test_top5_limit_and_podium():
    scores = {f"p{i}": i * 10 for i in range(10)}
    top5, _ = build_rank_updates(scores, {}, {})
    assert len(top5) == 5 and top5[0]["username"] == "p9"
    top3, own = build_podium(scores)
    assert [p["username"] for p in top3] == ["p9", "p8", "p7"]
    assert top3[0]["rank"] == 1
    assert own["p0"] == {"rank": 10, "total": 0}


# --- nicknames ---


@pytest.mark.parametrize(
    "name", ["Jo", "Élodie", "Jean-Luc", "o'neil", "Team_42", "A.B", "李雷", "Zoë M", "Dominique", "Conrad"]
)
def test_valid_nicknames(name):
    assert clean_nickname(name) == name


def test_trim():
    assert clean_nickname("   Swift   Otter  ") == "Swift Otter"


@pytest.mark.parametrize(
    "name,code",
    [
        ("a", "too_short"),
        ("   ", "too_short"),
        ("x" * 21, "too_long"),
        ("<script>", "invalid_characters"),
        ("bob!", "invalid_characters"),
        ("----", "invalid_characters"),
        ("Fuck", "profanity"),
        ("f u c k", "profanity"),
        ("PUTAIN", "profanity"),
        ("Enculé", "profanity"),
        ("m3rd3", "profanity"),
        ("5al0pe", "profanity"),
        ("grosconnard", "profanity"),
        ("Le con", "profanity"),
        (42, "invalid_type"),
    ],
)
def test_invalid_nicknames(name, code):
    with pytest.raises(NicknameError) as exc:
        clean_nickname(name)
    assert exc.value.code == code


def test_profanity_no_false_positives():
    for name in ("Conrad", "Dominique", "Véronique", "Pascal", "Scunthorpe", "Bordelais"):
        assert not contains_profanity(name), name


def test_join_game_data_validator():
    assert JoinGameData(username="  Léa ", game_pin="123").username == "Léa"
    with pytest.raises(ValidationError) as exc:
        JoinGameData(username="salope", game_pin="123")
    err = exc.value.errors()[0]["ctx"]["error"]
    assert isinstance(err, NicknameError) and err.code == "profanity"


def test_random_nickname_is_valid():
    for _ in range(200):
        name = random_nickname()
        assert clean_nickname(name) == name
        assert " " in name
