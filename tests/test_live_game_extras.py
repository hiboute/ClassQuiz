# SPDX-License-Identifier: MPL-2.0
"""Get-ready screen, word cloud, pause/resume, end now and captcha, against an
in-memory Redis (fakeredis), in the style of test_live_game_flow.py."""

import importlib
from datetime import datetime, timedelta

import pytest

from tests.test_live_game_flow import ABCD, PIN, Harness, make_game, fakeredis  # noqa: F401

import classquiz.db.models as db_models  # noqa: E402
import classquiz.socket_server as ss  # noqa: E402

ss_helpers = importlib.import_module("classquiz.socket_server.helpers")

WORD_CLOUD = {"question": "One word for Monday?", "time": "30", "type": "WORD_CLOUD", "answers": ""}


async def _setup(h, questions, players=("ann", "bob"), start=None):
    game = make_game(questions)
    await game.save(PIN)
    h.sessions["admin"] = {"game_pin": PIN, "admin": True}
    for name in players:
        h.sessions[name] = {}
        await ss.join_game(name, {"username": name, "game_pin": PIN})
    await ss.start_game("admin", start if start is not None else {})


# --- get ready ---


@pytest.mark.asyncio
async def test_get_ready_delays_the_answer_window(monkeypatch):
    h = Harness(monkeypatch)
    await _setup(h, [{**ABCD, "image": "/img.png", "points": "double"}, ABCD])
    h.gate.clear()
    await ss.set_question_number("admin", "0")

    payload, target = h.events("get_ready")[-1]
    assert target == PIN  # game room: phones and host screens
    assert payload == {
        "question_index": 0,
        "question_count": 2,
        "title": "q",
        "type": "ABCD",
        "points": "double",
        "seconds": 3,
        "image": "/img.png",
    }
    assert not h.events("set_question_number")
    assert await h.r.get(f"game:{PIN}:current_time") is None

    # An answer during the countdown is refused and scores nothing
    await ss.submit_answer("ann", {"question_index": 0, "answer": "a"})
    assert h.events("question_not_active", "ann")[-1][0] == {"question_index": 0, "reason": "get_ready"}
    assert not h.events("player_answer")
    assert not await h.r.sismember(f"game_session:{PIN}:0:answered", "ann")

    # After the countdown the question opens and the answer counts
    h.gate.set()
    await h.drain()
    assert h.sleeps == [3]
    assert h.events("set_question_number", PIN)[-1][0]["question_index"] == 0
    assert await h.r.get(f"game:{PIN}:current_time") is not None
    await ss.submit_answer("ann", {"question_index": 0, "answer": "a"})
    assert h.events("player_answer", f"admin:{PIN}")
    await ss.get_question_results("admin", {"question_number": 0})
    assert h.events("rank_update", "ann")[-1][0]["gained"] == 2000


@pytest.mark.asyncio
async def test_get_ready_skip_ahead_cancels_the_old_countdown(monkeypatch):
    h = Harness(monkeypatch)
    await _setup(h, [ABCD, ABCD])
    h.gate.clear()
    await ss.set_question_number("admin", "0")
    await ss.set_question_number("admin", "1")  # host skips during the countdown
    h.gate.set()
    await h.drain()
    opened = [d["question_index"] for d, _ in h.events("set_question_number")]
    assert opened == [1]
    await ss.submit_answer("ann", {"question_index": 0, "answer": "a"})
    assert h.events("question_not_active", "ann")[-1][0]["reason"] == "closed"


@pytest.mark.asyncio
async def test_get_ready_seconds_configuration(monkeypatch):
    h = Harness(monkeypatch)
    await _setup(
        h,
        [ABCD, ABCD, {"question": "s", "time": "5", "type": "SLIDE", "answers": "<p/>"}],
        start={"get_ready_seconds": 99},
    )
    # per game, clamped to 10
    await ss.set_question_number("admin", "0")
    assert h.events("get_ready")[-1][0]["seconds"] == 10
    await h.drain()
    # per question override, 0 disables: opens at once with no get_ready
    n_ready = len(h.events("get_ready"))
    await ss.set_question_number("admin", {"question_index": 1, "get_ready_seconds": 0})
    assert len(h.events("get_ready")) == n_ready
    assert h.events("set_question_number", PIN)[-1][0]["question_index"] == 1
    assert h.tasks == []
    # slides never get a get-ready screen
    await ss.set_question_number("admin", "2")
    assert len(h.events("get_ready")) == n_ready
    assert h.events("set_question_number", "admin")[-1][0] == {"question_index": 2}
    # a phone cannot set questions; an out-of-range index is an error
    await ss.set_question_number("ann", "0")
    await ss.set_question_number("admin", "7")
    assert h.events("error", "admin")
    # old games stored without the field default to 3
    assert (
        db_models.PlayGame.model_validate_json(
            make_game([ABCD]).model_dump_json(exclude={"get_ready_seconds"})
        ).get_ready_seconds
        == 3
    )


# --- word cloud ---


def test_word_cloud_question_model():
    q = db_models.QuizQuestion(**WORD_CLOUD)
    assert q.type == db_models.QuizQuestionType.WORD_CLOUD and q.answers == []
    assert db_models.QuizQuestion(**{**WORD_CLOUD, "answers": None}).answers == []


def test_clean_word():
    assert ss_helpers.clean_word("  New   York ") == ("New York", "new york")
    assert ss_helpers.clean_word(42) == ("42", "42")
    for bad, code in [
        ("   ", "empty"),
        ("x" * 31, "too_long"),
        ("merde", "profanity"),
        ("F.U.C.K", "profanity"),
        ("a\x00b", "invalid_characters"),
        (None, "invalid_type"),
    ]:
        with pytest.raises(ss_helpers.WordCloudError) as e:
            ss_helpers.clean_word(bad)
        assert e.value.code == code, bad
    assert ss_helpers.clean_word("x" * 30)[0] == "x" * 30


@pytest.mark.asyncio
async def test_word_cloud_flow(monkeypatch):
    h = Harness(monkeypatch)
    await _setup(h, [ABCD, WORD_CLOUD], players=("ann", "bob", "cid"), start={"get_ready_seconds": 0})
    admin = f"admin:{PIN}"
    # Q0: ann builds a streak of 1
    await ss.set_question_number("admin", "0")
    await ss.submit_answer("ann", {"question_index": 0, "answer": "a"})
    await ss.get_question_results("admin", {"question_number": 0})

    await ss.set_question_number("admin", "1")
    assert h.events("set_question_number", PIN)[-1][0]["question"]["type"] == "WORD_CLOUD"
    h.gate.clear()  # time stands still until the gate opens
    await ss.submit_answer("ann", {"question_index": 1, "answer": "  Paris  "})
    assert h.events("word_cloud_accepted", "ann")[-1][0] == {"question_index": 1, "text": "Paris"}
    first = h.events("word_cloud_update", admin)
    assert len(first) == 1 and first[0][0] == {
        "question_index": 1,
        "words": [{"text": "Paris", "count": 1}],
        "total": 1,
    }

    # Inside the 500 ms window: no immediate update, one trailing task
    await ss.submit_answer("bob", {"question_index": 1, "answer": "PARIS"})
    for bad, code in [("merde", "profanity"), ("x" * 31, "too_long"), ("", "empty")]:
        await ss.submit_answer("cid", {"question_index": 1, "answer": bad})
        refused = h.events("word_cloud_refused", "cid")[-1][0]
        assert refused["code"] == code and refused["question_index"] == 1 and refused["message"]
    await ss.submit_answer("cid", {"question_index": 1, "answer": "Lyon"})  # refused words allow a retry
    await ss.submit_answer("ann", {"question_index": 1, "answer": "Lyon"})
    assert h.events("already_replied", "ann")
    assert len(h.events("word_cloud_update", admin)) == 1
    assert len(h.tasks) == 1
    assert h.events("everyone_answered", PIN)

    h.gate.set()
    await h.drain()
    updates = h.events("word_cloud_update", admin)
    assert len(updates) == 2
    assert updates[-1][0] == {
        "question_index": 1,
        "words": [{"text": "Paris", "count": 2}, {"text": "Lyon", "count": 1}],
        "total": 3,
    }
    assert all(t == admin for _, t in h.events("word_cloud_update"))  # host screens only

    await ss.get_question_results("admin", {"question_number": 1})
    assert len(h.events("word_cloud_update", admin)) == 3  # final state, not throttled
    results = h.events("question_results", admin)[-1][0]
    assert {a["answer"] for a in results} == {"Paris", "PARIS", "Lyon"}
    assert all(a["score"] == 0 for a in results)
    # No points, and the streak is untouched (ann keeps 1, nobody is reset)
    ann = h.events("rank_update", "ann")[-1][0]
    assert ann["gained"] == 0 and ann["streak"] == 1 and ann["total"] == 1000
    assert h.events("rank_update", "bob")[-1][0]["streak"] == 0


@pytest.mark.asyncio
async def test_word_cloud_throttle_is_two_per_second(monkeypatch):
    h = Harness(monkeypatch)
    names = [f"p{i:02d}" for i in range(30)]
    await _setup(h, [WORD_CLOUD], players=names, start={"get_ready_seconds": 0})
    await ss.set_question_number("admin", "0")
    h.gate.clear()
    for i, n in enumerate(names):
        await ss.submit_answer(n, {"question_index": 0, "answer": f"w{i % 70}"})
    # 30 words inside one window: one leading update, one trailing task
    assert len(h.events("word_cloud_update")) == 1
    assert len(h.tasks) == 1
    h.gate.set()
    await h.drain()
    assert len(h.events("word_cloud_update")) == 2
    assert h.events("word_cloud_update")[-1][0]["total"] == 30
    assert len(h.events("word_cloud_update")[-1][0]["words"]) == 30


@pytest.mark.asyncio
async def test_word_cloud_top_60():
    r = fakeredis.FakeAsyncRedis(decode_responses=True)
    import classquiz.socket_server as mod

    old = mod.redis
    mod.redis = r
    try:
        for i in range(80):
            for _ in range(i % 5 + 1):
                await mod._add_word(PIN, 0, f"k{i}", f"K{i}")
        snap = await mod._word_cloud_snapshot(PIN, 0)
    finally:
        mod.redis = old
    assert len(snap["words"]) == 60
    assert snap["words"][0]["count"] == 5 and snap["words"][0]["text"].startswith("K")
    assert snap["total"] == sum(i % 5 + 1 for i in range(80))


# --- pause / resume ---


@pytest.mark.asyncio
async def test_pause_and_resume(monkeypatch):
    h = Harness(monkeypatch)
    await _setup(h, [ABCD, ABCD])
    # pause during get-ready is refused
    h.gate.clear()
    await ss.set_question_number("admin", "0")
    await ss.pause_game("admin", {})
    assert h.events("pause_refused", "admin")[-1][0] == {"reason": "get_ready"}
    h.gate.set()
    await h.drain()

    # question opened 5 s ago (20 s limit)
    await h.r.set(f"game:{PIN}:current_time", (datetime.now() - timedelta(seconds=5)).isoformat())
    await ss.pause_game("ann", {})  # phones are ignored
    assert not h.events("game_paused")
    await ss.pause_game("admin", {})
    paused, target = h.events("game_paused")[-1]
    assert target == PIN and paused["question_index"] == 0 and 14.5 <= paused["remaining"] <= 15.0
    await ss.pause_game("admin", {})
    assert h.events("pause_refused", "admin")[-1][0] == {"reason": "already_paused"}

    # answers wait while paused
    await ss.submit_answer("ann", {"question_index": 0, "answer": "a"})
    assert h.events("question_not_active", "ann")[-1][0]["reason"] == "paused"
    # a late player gets the pause state with the question
    h.sessions["cid"] = {}
    await ss.join_game("cid", {"username": "cid", "game_pin": PIN})
    assert h.events("game_paused", "cid")[-1][0] == paused

    await ss.resume_game("admin", {})
    resumed, target = h.events("game_resumed")[-1]
    assert target == PIN and resumed == paused
    started = datetime.fromisoformat(await h.r.get(f"game:{PIN}:current_time"))
    assert 4.9 <= (datetime.now() - started).total_seconds() <= 5.6
    await ss.resume_game("admin", {})
    assert h.events("pause_refused", "admin")[-1][0] == {"reason": "not_paused"}

    # scored from the time before the pause: about 5 s -> ~875
    await ss.submit_answer("ann", {"question_index": 0, "answer": "a"})
    await ss.get_question_results("admin", {"question_number": 0})
    assert 860 <= h.events("rank_update", "ann")[-1][0]["gained"] <= 876

    # no open question after the results
    await ss.pause_game("admin", {})
    assert h.events("pause_refused", "admin")[-1][0] == {"reason": "no_open_question"}


@pytest.mark.asyncio
async def test_results_clear_a_pause(monkeypatch):
    h = Harness(monkeypatch)
    await _setup(h, [ABCD, ABCD], start={"get_ready_seconds": 0})
    await ss.set_question_number("admin", "0")
    await ss.pause_game("admin", {})
    await ss.get_question_results("admin", {"question_number": 0})
    assert await h.r.get(f"game:{PIN}:paused") is None
    await ss.set_question_number("admin", "1")
    await ss.submit_answer("ann", {"question_index": 1, "answer": "a"})
    assert h.events("player_answer")


# --- end now ---


@pytest.mark.asyncio
async def test_end_game_now(monkeypatch):
    h = Harness(monkeypatch)
    await _setup(h, [ABCD, ABCD, ABCD], start={"get_ready_seconds": 0})
    await ss.set_question_number("admin", "0")
    await ss.submit_answer("ann", {"question_index": 0, "answer": "a"})
    await ss.get_question_results("admin", {"question_number": 0})

    await ss.start_game("admin", {"get_ready_seconds": 3})
    h.gate.clear()
    await ss.set_question_number("admin", "1")
    await ss.end_game_now("bob", {})  # phones are ignored
    assert not h.events("game_ended")
    await ss.end_game_now("admin", {})
    assert h.events("game_ended", PIN)[-1][0] == {"reason": "host"}
    assert h.events("final_results", f"players:{PIN}")[-1][0] == {}
    assert "0" in h.events("final_results", f"admin:{PIN}")[-1][0]
    assert h.events("podium", f"admin:{PIN}")[-1][0]["top"][0]["username"] == "ann"
    assert h.events("podium", "bob")[-1][0]["rank"] == 2

    # the countdown that was running does not open question 1
    h.gate.set()
    await h.drain()
    assert [d["question_index"] for d, _ in h.events("set_question_number")] == [0]
    await ss.submit_answer("bob", {"question_index": 1, "answer": "a"})
    assert h.events("question_not_active", "bob")
    # and the host cannot start another question
    await ss.set_question_number("admin", "2")
    assert not h.events("get_ready", PIN)[1:]
    assert [d["question_index"] for d, _ in h.events("set_question_number")] == [0]


# --- captcha ---


@pytest.mark.asyncio
async def test_captcha_is_awaited(monkeypatch):
    h = Harness(monkeypatch)
    game = make_game([ABCD])
    game.captcha_enabled = True
    await game.save(PIN)
    # no captcha key configured: passes
    assert await ss_helpers.check_captcha("token") is True
    h.sessions["ann"] = {}
    await ss.join_game("ann", {"username": "ann", "game_pin": PIN, "captcha": "token"})
    assert h.events("joined_game", "ann")

    async def refuse(_token):
        return False

    monkeypatch.setattr(ss, "check_captcha", refuse)
    h.sessions["bob"] = {}
    await ss.join_game("bob", {"username": "bob", "game_pin": PIN, "captcha": "bad"})
    assert h.events("captcha_invalid", "bob") and not h.events("joined_game", "bob")
    assert await h.r.get(f"game_session:{PIN}:players:bob") is None


@pytest.mark.asyncio
async def test_check_captcha_reads_provider_answer(monkeypatch):
    class Conf:
        hcaptcha_key = "secret"
        recaptcha_key = None

    answers = []

    class Resp:
        def __init__(self, body):
            self.body = body

        async def json(self, content_type=None):
            return self.body

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

    class Session:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        def post(self, url, data):
            answers.append((url, data))
            return Resp({"success": data["response"] == "good"})

    monkeypatch.setattr(ss_helpers, "settings", lambda: Conf())
    monkeypatch.setattr(ss_helpers.aiohttp, "ClientSession", Session)
    assert await ss_helpers.check_captcha("good") is True
    assert await ss_helpers.check_captcha("bad") is False
    assert answers[0] == ("https://hcaptcha.com/siteverify", {"response": "good", "secret": "secret"})


@pytest.mark.asyncio
async def test_word_cloud_throttle_in_real_time(monkeypatch):
    """With real sleeps and Redis expiry: never more than 2 updates per second."""
    import asyncio

    h = Harness(monkeypatch)
    monkeypatch.setattr(ss, "_countdown_sleep", asyncio.sleep)
    names = [f"p{i:02d}" for i in range(24)]
    await _setup(h, [WORD_CLOUD], players=names, start={"get_ready_seconds": 0})
    await ss.set_question_number("admin", "0")
    stamps = []
    real_emit = ss.sio.emit

    async def emit(event, data=None, room=None, to=None, **kw):
        if event == "word_cloud_update":
            stamps.append(asyncio.get_running_loop().time())
        await real_emit(event, data, room=room, to=to, **kw)

    monkeypatch.setattr(ss.sio, "emit", emit)
    for n in names:  # one word every 50 ms for 1.2 s
        await ss.submit_answer(n, {"question_index": 0, "answer": n})
        await asyncio.sleep(0.05)
    await h.drain()
    assert h.events("word_cloud_update")[-1][0]["total"] == 24  # the last word is not lost
    assert 2 <= len(stamps) <= 4
    assert all(b - a >= 0.45 for a, b in zip(stamps, stamps[1:]))
