# SPDX-License-Identifier: MPL-2.0
"""Socket handler flow against an in-memory Redis (fakeredis): join, late join,
lock, answers, streaks, results, leaderboard, kick/ban, podium."""

import asyncio
import importlib
import json
from datetime import datetime, timedelta

import pytest

import tests.test_live_game_rules  # noqa: F401  (sets the settings env)

fakeredis = pytest.importorskip("fakeredis")

import classquiz.db.models as db_models  # noqa: E402
import classquiz.socket_server as ss  # noqa: E402

ss_helpers = importlib.import_module("classquiz.socket_server.helpers")

PIN = "123456"


class Harness:
    def __init__(self, monkeypatch):
        self.r = fakeredis.FakeAsyncRedis(decode_responses=True)
        for mod in (ss, ss_helpers, db_models):
            monkeypatch.setattr(mod, "redis", self.r)
        self.sessions: dict[str, dict] = {}
        self.rooms: dict[str, set] = {}
        self.sent: list[tuple[str, object, str]] = []

        async def get_session(sid, _sio, *a, **k):
            return dict(self.sessions[sid])

        async def save_session(sid, _sio, data, *a, **k):
            self.sessions[sid] = dict(data)

        async def enter_room(sid, room, namespace=None):
            self.rooms.setdefault(room, set()).add(sid)

        async def leave_room(sid, room, namespace=None):
            self.rooms.get(room, set()).discard(sid)

        async def emit(event, data=None, room=None, to=None, **kw):
            target = to or room
            assert target is not None, f"global emit of {event}"
            self.sent.append((event, data, target))

        monkeypatch.setattr(ss, "get_session", get_session)
        monkeypatch.setattr(ss, "save_session", save_session)
        monkeypatch.setattr(ss.sio, "enter_room", enter_room)
        monkeypatch.setattr(ss.sio, "leave_room", leave_room)
        monkeypatch.setattr(ss.sio, "emit", emit)
        monkeypatch.setattr(ss.sio.manager, "is_connected", lambda sid, ns: True)

        # Background tasks run on the test loop; their sleeps wait on `gate`
        # (open by default) and are recorded. A sleep also lets the word
        # cloud throttle window expire, as real time would.
        self.tasks: list = []
        self.sleeps: list[float] = []
        self.gate = asyncio.Event()
        self.gate.set()

        def start_background_task(fn, *args, **kwargs):
            task = asyncio.ensure_future(fn(*args, **kwargs))
            self.tasks.append(task)
            return task

        async def fake_sleep(seconds):
            self.sleeps.append(seconds)
            await self.gate.wait()
            for key in await self.r.keys("*:wc_throttle"):
                await self.r.delete(key)

        monkeypatch.setattr(ss.sio, "start_background_task", start_background_task)
        monkeypatch.setattr(ss, "_countdown_sleep", fake_sleep)

    async def drain(self):
        """Run the background tasks started so far (and the ones they start)."""
        while self.tasks:
            tasks, self.tasks = self.tasks, []
            await asyncio.gather(*tasks)

    def events(self, name, target=None):
        return [(d, t) for e, d, t in self.sent if e == name and (target is None or t == target)]


def make_game(questions):
    import uuid

    return db_models.PlayGame(
        quiz_id=uuid.uuid4(),
        description="d",
        user_id=uuid.uuid4(),
        title="t",
        questions=questions,
        game_id=uuid.uuid4(),
        game_pin=PIN,
    )


ABCD = {
    "question": "q",
    "time": "20",
    "type": "ABCD",
    "answers": [{"right": True, "answer": "a"}, {"right": False, "answer": "b"}],
}


@pytest.mark.asyncio
async def test_full_flow(monkeypatch):
    h = Harness(monkeypatch)
    game = make_game([ABCD, {**ABCD, "points": "double"}, {**ABCD, "points": "none"}])
    await game.save(PIN)
    h.sessions["admin"] = {"game_pin": PIN, "admin": True}

    # bad nickname -> username_invalid
    h.sessions["x"] = {}
    await ss.join_game("x", {"username": "merde", "game_pin": PIN})
    assert h.events("username_invalid", "x")[0][0]["code"] == "profanity"

    for name in ("ann", "bob"):
        h.sessions[name] = {}
        await ss.join_game(name, {"username": name, "game_pin": PIN})
        assert h.events("joined_game", name)
    await ss.join_game("dup", {"username": "ann", "game_pin": PIN})
    assert h.events("username_already_exists", "dup")
    assert h.rooms[f"players:{PIN}"] == {"ann", "bob"}

    # get_ready_seconds 0: questions open at once, as before the get-ready screen
    await ss.start_game("admin", {"get_ready_seconds": 0})
    await ss.set_question_number("admin", "0")
    # late join during a running question gets start_game + the question
    h.sessions["cid"] = {}
    await ss.join_game("cid", {"username": "cid", "game_pin": PIN})
    assert h.events("start_game", "cid") and h.events("set_question_number", "cid")

    # lock blocks new players
    await ss.lock_game("admin", {})
    assert h.events("game_lock_state", f"admin:{PIN}")[-1][0] == {"locked": True}
    h.sessions["dan"] = {}
    await ss.join_game("dan", {"username": "dan", "game_pin": PIN})
    assert h.events("game_locked", "dan")
    await ss.unlock_game("admin", {})
    assert h.events("game_lock_state", f"admin:{PIN}")[-1][0] == {"locked": False}

    # Q0: ann right fast, bob wrong, cid no answer
    await ss.submit_answer("ann", {"question_index": 0, "answer": "a"})
    await ss.submit_answer("ann", {"question_index": 0, "answer": "a"})
    assert h.events("already_replied", "ann")
    await ss.submit_answer("bob", {"question_index": 0, "answer": "b"})
    assert len(h.events("player_answer", f"admin:{PIN}")) == 2
    await ss.get_question_results("admin", {"question_number": 0})
    admin_results = h.events("question_results", f"admin:{PIN}")[-1][0]
    assert {a["username"] for a in admin_results} == {"ann", "bob"}
    ann_results = h.events("question_results", "ann")[-1][0]
    assert len(ann_results) == 1 and ann_results[0]["score"] == 1000
    assert h.events("question_results", "cid")[-1][0] == []
    ru = h.events("rank_update", "bob")[-1][0]
    assert ru["rank"] in (2, 3) and ru["behind_username"] is not None
    assert h.events("rank_update", "ann")[-1][0]["rank"] == 1
    lb = h.events("leaderboard", f"admin:{PIN}")[-1][0]
    assert lb["top"][0] == {"username": "ann", "score": 1000, "gained": 1000} and lb["total_players"] == 3

    # answers after results are refused
    await ss.submit_answer("cid", {"question_index": 0, "answer": "a"})
    assert h.events("question_not_active", "cid")

    # Q1 double: ann right again -> streak 2 -> +100; time ~0 -> 2000
    await ss.set_question_number("admin", "1")
    await ss.submit_answer("ann", {"question_index": 1, "answer": "a"})
    await ss.get_question_results("admin", {"question_number": 1})
    ru = h.events("rank_update", "ann")[-1][0]
    assert ru["gained"] == 2100 and ru["streak"] == 2 and ru["total"] == 3100
    assert int(await h.r.hget(f"game_session:{PIN}:player_scores", "ann")) == 3100

    # Q2 none: right answer, no points, no bonus
    await ss.set_question_number("admin", "2")
    # pretend the question started 5 s ago
    await h.r.set(f"game:{PIN}:current_time", (datetime.now() - timedelta(seconds=5)).isoformat())
    await ss.submit_answer("ann", {"question_index": 2, "answer": "a"})
    await ss.get_question_results("admin", {"question_number": 2})
    ru = h.events("rank_update", "ann")[-1][0]
    assert ru["gained"] == 0 and ru["streak"] == 3
    # bob did not answer: streak reset
    assert h.events("rank_update", "bob")[-1][0]["streak"] == 0

    # kick + ban
    await ss.kick_player("admin", {"username": "bob"})
    assert h.events("kick", "bob")
    h.sessions["bob2"] = {}
    await ss.join_game("bob2", {"username": "BOB", "game_pin": PIN})
    assert h.events("username_banned", "bob2")
    await ss.rejoin_game("bob3", {"old_sid": "bob", "username": "bob", "game_pin": PIN})
    assert h.events("kick", "bob3")

    # podium
    await ss.get_final_results("admin", {})
    assert h.events("final_results", f"players:{PIN}")[-1][0] == {}
    assert isinstance(h.events("final_results", f"admin:{PIN}")[-1][0], dict)
    p = h.events("podium", "cid")[-1][0]
    assert p["top"][0]["username"] == "ann" and p["rank"] == 2 and p["total_players"] == 2
    assert h.events("podium", f"admin:{PIN}")[-1][0]["rank"] is None

    # keys expire like the others
    for key in (f"game_session:{PIN}:leaderboard", f"game_session:{PIN}:streaks", f"game_session:{PIN}:0:answered"):
        assert await h.r.ttl(key) > 0, key
    stored = json.loads((await h.r.lrange(f"game_session:{PIN}:1", 0, -1))[0])
    assert stored["streak_bonus"] == 100
