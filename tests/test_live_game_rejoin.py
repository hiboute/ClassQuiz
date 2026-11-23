# SPDX-License-Identifier: MPL-2.0
"""rejoin_game: plain reconnect, reload with the rejoin token, refusals with
`rejoin_failed`, and the open question sent again to a rejoining phone."""

from datetime import datetime, timedelta

import pytest

from tests.test_live_game_flow import ABCD, PIN, Harness, make_game, ss


async def _setup(h, questions=None):
    game = make_game(questions or [ABCD, ABCD])
    await game.save(PIN)
    h.sessions["admin"] = {"game_pin": PIN, "admin": True}
    h.sessions["ann"] = {}
    await ss.join_game("ann", {"username": "ann", "game_pin": PIN})
    joined = h.events("joined_game", "ann")[-1][0]
    return joined


@pytest.mark.asyncio
async def test_joined_game_carries_rejoin_token(monkeypatch):
    h = Harness(monkeypatch)
    joined = await _setup(h)
    assert isinstance(joined, dict)
    assert joined["username"] == "ann"
    assert len(joined["rejoin_token"]) == 32
    assert joined["question_count"] == 2


@pytest.mark.asyncio
async def test_rejoin_with_old_sid(monkeypatch):
    h = Harness(monkeypatch)
    await _setup(h)
    h.sessions["ann2"] = {}
    await ss.rejoin_game("ann2", {"old_sid": "ann", "username": "ann", "game_pin": PIN})
    assert h.events("rejoined_game", "ann2")
    assert not h.events("rejoin_failed", "ann2")
    assert await h.r.get(f"game_session:{PIN}:players:ann") == "ann2"
    players = await h.r.smembers(f"game_session:{PIN}:players")
    assert len(players) == 1 and "ann2" in next(iter(players))
    assert "ann2" in h.rooms[f"players:{PIN}"]


@pytest.mark.asyncio
async def test_rejoin_unknown_player_fails_loudly(monkeypatch):
    h = Harness(monkeypatch)
    await _setup(h)
    h.sessions["zed"] = {}
    await ss.rejoin_game("zed", {"old_sid": "nope", "username": "zed", "game_pin": PIN})
    failed = h.events("rejoin_failed", "zed")
    assert failed and failed[0][0]["reason"] == "unknown_player"
    assert failed[0][0]["message"]
    assert not h.events("rejoined_game", "zed")


@pytest.mark.asyncio
async def test_rejoin_stale_sid_without_token_fails(monkeypatch):
    h = Harness(monkeypatch)
    await _setup(h)
    h.sessions["evil"] = {}
    await ss.rejoin_game("evil", {"old_sid": "wrong", "username": "ann", "game_pin": PIN})
    assert h.events("rejoin_failed", "evil")[0][0]["reason"] == "stale_session"
    # a wrong token does not help either
    await ss.rejoin_game("evil", {"old_sid": "wrong", "username": "ann", "game_pin": PIN, "rejoin_token": "00" * 16})
    assert len(h.events("rejoin_failed", "evil")) == 2
    assert await h.r.get(f"game_session:{PIN}:players:ann") == "ann"


@pytest.mark.asyncio
async def test_rejoin_reclaims_with_token(monkeypatch):
    h = Harness(monkeypatch)
    joined = await _setup(h)
    # The phone reloaded twice: its cookie names a socket the server never kept
    h.sessions["ann3"] = {}
    await ss.rejoin_game(
        "ann3",
        {"old_sid": "lost-sid", "username": "ann", "game_pin": PIN, "rejoin_token": joined["rejoin_token"]},
    )
    assert h.events("rejoined_game", "ann3")
    assert h.events("rejoined_game", "ann3")[0][0]["rejoin_token"] == joined["rejoin_token"]
    assert await h.r.get(f"game_session:{PIN}:players:ann") == "ann3"
    # the old socket left the rooms
    assert "ann" not in h.rooms[f"players:{PIN}"]
    assert "ann3" in h.rooms[f"players:{PIN}"]


@pytest.mark.asyncio
async def test_duplicate_rejoin_is_idempotent(monkeypatch):
    h = Harness(monkeypatch)
    await _setup(h)
    h.sessions["ann2"] = {}
    await ss.rejoin_game("ann2", {"old_sid": "ann", "username": "ann", "game_pin": PIN})
    await ss.rejoin_game("ann2", {"old_sid": "ann", "username": "ann", "game_pin": PIN})
    assert len(h.events("rejoined_game", "ann2")) == 2
    assert not h.events("rejoin_failed", "ann2")


@pytest.mark.asyncio
async def test_rejoin_unknown_game(monkeypatch):
    h = Harness(monkeypatch)
    h.sessions["x"] = {}
    await ss.rejoin_game("x", {"old_sid": "a", "username": "ann", "game_pin": "999999"})
    assert h.events("game_not_found", "x")
    assert h.events("rejoin_failed", "x")[0][0]["reason"] == "game_not_found"


@pytest.mark.asyncio
async def test_rejoin_resends_open_question_with_remaining_time(monkeypatch):
    h = Harness(monkeypatch)
    await _setup(h)
    h.sessions["bob"] = {}
    await ss.join_game("bob", {"username": "bob", "game_pin": PIN})  # so not everyone answers
    await ss.start_game("admin", {"get_ready_seconds": 0})
    await ss.set_question_number("admin", "0")
    await h.r.set(f"game:{PIN}:current_time", (datetime.now() - timedelta(seconds=5)).isoformat())
    h.sessions["ann2"] = {}
    await ss.rejoin_game("ann2", {"old_sid": "ann", "username": "ann", "game_pin": PIN})
    q = h.events("set_question_number", "ann2")
    assert q, "open question not re-sent"
    payload = q[0][0]
    assert payload["question_index"] == 0
    assert 14 <= payload["remaining"] <= 15.1
    assert payload["already_answered"] is False
    assert "right" not in payload["question"]["answers"][0]
    # the rejoined phone can answer
    await ss.submit_answer("ann2", {"question_index": 0, "answer": "a"})
    assert len(await h.r.lrange(f"game_session:{PIN}:0", 0, -1)) == 1
    # a second reload after answering says so
    h.sessions["ann3"] = {}
    await ss.rejoin_game("ann3", {"old_sid": "ann2", "username": "ann", "game_pin": PIN})
    assert h.events("set_question_number", "ann3")[0][0]["already_answered"] is True


@pytest.mark.asyncio
async def test_rejoin_after_results_sends_no_question(monkeypatch):
    h = Harness(monkeypatch)
    await _setup(h)
    await ss.start_game("admin", {"get_ready_seconds": 0})
    await ss.set_question_number("admin", "0")
    await ss.get_question_results("admin", {"question_number": 0})
    h.sessions["ann2"] = {}
    await ss.rejoin_game("ann2", {"old_sid": "ann", "username": "ann", "game_pin": PIN})
    assert h.events("rejoined_game", "ann2")
    assert not h.events("set_question_number", "ann2")


@pytest.mark.asyncio
async def test_rejoin_during_pause_sends_pause(monkeypatch):
    h = Harness(monkeypatch)
    await _setup(h)
    await ss.start_game("admin", {"get_ready_seconds": 0})
    await ss.set_question_number("admin", "0")
    await ss.pause_game("admin", {})
    h.sessions["ann2"] = {}
    await ss.rejoin_game("ann2", {"old_sid": "ann", "username": "ann", "game_pin": PIN})
    q = h.events("set_question_number", "ann2")[0][0]
    paused = h.events("game_paused", "ann2")[0][0]
    assert q["remaining"] == paused["remaining"]
