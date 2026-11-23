# SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)
#
# SPDX-License-Identifier: MPL-2.0


import asyncio
import base64
import hashlib
import json
import os
import random

import socketio
from cryptography.fernet import Fernet

from classquiz.config import redis, settings
from classquiz.db.models import (
    PlayGame,
    QuizQuestionType,
    GameSession,
    GamePlayer,
    VotingQuizAnswer,
    AnswerDataList,
    AnswerData,
)
from pydantic import BaseModel, ValidationError
from datetime import datetime

from classquiz.helpers.nickname import NicknameError, random_nickname
from classquiz.socket_server.helpers import (
    check_answer,
    check_captcha,
    mark_answered,
)
from classquiz.socket_server.scoring import (
    base_points_for,
    build_podium,
    build_rank_updates,
    calculate_score,
    streak_bonus,
)
from .models import (
    RejoinGameData,
    JoinGameData,
    ReturnQuestion,
    SubmitAnswerData,
    RegisterAsAdminData,
    KickPlayerInput,
    ConnectSessionIdEvent,
    RankUpdateEvent,
    UsernameInvalidEvent,
)

from classquiz.socket_server.export_helpers import save_quiz_to_storage
from classquiz.socket_server.session import get_session, save_session

settings = settings()

# Room broadcasts go through Redis pub/sub, so a player connected to one
# gunicorn worker gets the events emitted by the worker that handled the
# host's action. Same Redis as the rest of the app (settings.redis). Each
# socket still has to stay on the worker it connected to (sticky sessions or
# websocket-only transport), as Socket.IO always requires.
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=[],
    client_manager=socketio.AsyncRedisManager(str(settings.redis), channel="classquiz-socketio"),
)

KEY_TTL = 7200  # Same lifetime as the other game keys


def _players_room(game_pin: str) -> str:
    """Room of the players' phones only (the game_pin room also holds the host)."""
    return f"players:{game_pin}"


def _admin_room(game_pin: str) -> str:
    return f"admin:{game_pin}"


def _leaderboard_key(game_pin: str) -> str:
    # ZSET username -> total score, kept alongside the player_scores hash
    return f"game_session:{game_pin}:leaderboard"


def _streaks_key(game_pin: str) -> str:
    # HASH username -> current answer streak
    return f"game_session:{game_pin}:streaks"


def _banned_key(game_pin: str) -> str:
    # SET of kicked usernames (casefolded)
    return f"game_session:{game_pin}:banned"


def _locked_key(game_pin: str) -> str:
    # "1" while the host has locked the game against new players
    return f"game_session:{game_pin}:locked"


def _closed_key(game_pin: str, q_index: int) -> str:
    # Set once the results of a question were shown: later answers are refused
    return f"game_session:{game_pin}:{q_index}:closed"


def _is_gradable(question) -> bool:
    """Questions with a right answer (voting and slides have none)."""
    return question.type not in (QuizQuestionType.VOTING, QuizQuestionType.SLIDE)


async def _emit_to_sid(event: str, data, sid: str) -> None:
    """Emit to one socket; skip the Redis round trip when it is on this worker."""
    if sio.manager.is_connected(sid, "/"):
        await sio.emit(event, data, to=sid, ignore_queue=True)
    else:
        await sio.emit(event, data, to=sid)


async def _player_sids(game_pin: str) -> dict[str, str]:
    """username -> sid of the players connected over Socket.IO."""
    players = await redis.smembers(f"game_session:{game_pin}:players")
    res = {}
    for p in players:
        player = GamePlayer.model_validate_json(p)
        if player.sid is not None:
            res[player.username] = player.sid
    return res


async def _total_scores(game_pin: str) -> dict[str, float]:
    scores = dict(await redis.zrange(_leaderboard_key(game_pin), 0, -1, withscores=True))
    if not scores:
        # Game started before the leaderboard existed: fall back to the hash
        scores = {u: float(v) for u, v in (await redis.hgetall(f"game_session:{game_pin}:player_scores")).items()}
    return scores


async def _emit_lock_state(game_pin: str, to: str | None = None) -> None:
    locked = await redis.get(_locked_key(game_pin)) is not None
    await sio.emit("game_lock_state", {"locked": locked}, room=to or _admin_room(game_pin))


def _question_payload(game_data: PlayGame, index: int) -> dict:
    """The `set_question_number` payload for players (no solutions)."""
    temp_return = game_data.model_dump(include={"questions"})["questions"][index]
    question_type = game_data.questions[index].type
    if question_type == QuizQuestionType.VOTING:
        for i in range(len(temp_return["answers"])):
            temp_return["answers"][i] = VotingQuizAnswer(**temp_return["answers"][i])
    temp_return["type"] = question_type
    if question_type == QuizQuestionType.ORDER:
        random.shuffle(temp_return["answers"])
    return {
        "question_index": index,
        "question": ReturnQuestion(**temp_return).model_dump(mode="json"),
    }


def get_fernet_key() -> bytes:
    hlib = hashlib.sha256()
    hlib.update(settings.secret_key.encode("utf-8"))
    return base64.urlsafe_b64encode(hlib.hexdigest().encode("latin-1")[:32])


fernet = Fernet(get_fernet_key())


async def generate_final_results(game_data: PlayGame, game_pin: str) -> dict:
    results = {}
    for i in range(len(game_data.questions)):
        redis_res = await redis.lrange(f"game_session:{game_pin}:{i}", 0, -1)
        if not redis_res:
            continue
        else:
            results[str(i)] = [json.loads(a) for a in redis_res]
    return results


async def set_answer(game_pin: str, q_index: int, data: AnswerData) -> int:
    # Appending is atomic, so concurrent submissions can't overwrite each other
    key = f"game_session:{game_pin}:{q_index}"
    answer_count = await redis.rpush(key, data.model_dump_json())
    await redis.expire(key, 7200)
    return answer_count


async def record_answer(
    game_pin: str,
    game_data: PlayGame,
    question_index: int,
    username: str,
    answer_right: bool,
    answer: str,
    time_taken_ms: float,
) -> AnswerData | None:
    """Score and store one answer, update streak and leaderboard, notify the host.

    Returns None when the player had already answered this question.
    Shared by the Socket.IO players and the box controller.
    """
    if not await mark_answered(game_pin, question_index, username):
        return None
    question = game_data.questions[question_index]
    base = base_points_for(question.points)
    time_taken_ms = max(0.0, float(time_taken_ms))
    score = calculate_score(time_taken_ms, question.time, base) if answer_right else 0
    streak = 0
    bonus = 0
    if _is_gradable(question):
        streaks_key = _streaks_key(game_pin)
        if answer_right:
            streak = int(await redis.hincrby(streaks_key, username, 1))
            bonus = streak_bonus(streak, base)
        else:
            await redis.hset(streaks_key, username, 0)
        await redis.expire(streaks_key, KEY_TTL)
    gained = score + bonus
    async with redis.pipeline(transaction=False) as pipe:
        pipe.hincrby(f"game_session:{game_pin}:player_scores", username, gained)
        pipe.zincrby(_leaderboard_key(game_pin), gained, username)
        pipe.expire(_leaderboard_key(game_pin), KEY_TTL)
        await pipe.execute()
    answer_data = AnswerData(
        username=username,
        answer=answer,
        right=answer_right,
        time_taken=time_taken_ms,
        score=gained,
        streak=streak,
        streak_bonus=bonus,
    )
    answer_count = await set_answer(game_pin=game_pin, q_index=question_index, data=answer_data)
    player_count = await redis.scard(f"game_session:{game_pin}:players")
    # Only the host screens count answers; this used to go to every socket.
    await sio.emit(
        "player_answer",
        {"answer_count": answer_count, "player_count": player_count},
        room=_admin_room(game_pin),
    )
    if answer_count == player_count:
        game_data = await PlayGame.get_from_redis(game_pin)
        game_data.question_show = False
        await game_data.save(game_pin)
        # Host and phones both stop their timer on this.
        await sio.emit("everyone_answered", {}, room=game_pin)
    return answer_data


@sio.event
async def rejoin_game(sid: str, data: dict):
    redis_res = await redis.get(f"game:{data['game_pin']}")
    if redis_res is None:
        await sio.emit("game_not_found", room=sid)
        return
    try:
        d = RejoinGameData(**data)
    except ValidationError as e:
        await sio.emit("error", room=sid)
        print(e)
        return
    if await redis.sismember(_banned_key(d.game_pin), d.username.casefold()):
        # A kicked player reloading with the old cookie: kick again
        await sio.emit("kick", room=sid)
        return
    redis_sid_key = f"game_session:{d.game_pin}:players:{d.username}"
    old_sid = await redis.get(redis_sid_key)
    if old_sid != d.old_sid:
        return
    encrypted_datetime = fernet.encrypt(datetime.now().isoformat().encode("utf-8")).decode("utf-8")
    await sio.emit("time_sync", encrypted_datetime, room=sid)
    await redis.set(redis_sid_key, sid, ex=KEY_TTL)
    await redis.srem(
        f"game_session:{d.game_pin}:players",
        GamePlayer(username=d.username, sid=d.old_sid).model_dump_json(),
    )
    await redis.sadd(
        f"game_session:{d.game_pin}:players",
        GamePlayer(username=d.username, sid=sid).model_dump_json(),
    )
    await redis.zadd(_leaderboard_key(d.game_pin), {d.username: 0}, nx=True)
    game_data = PlayGame.model_validate_json(redis_res)
    session = {
        "game_pin": d.game_pin,
        "username": d.username,
        "sid_custom": sid,
        "admin": False,
    }
    await save_session(sid, sio, session)
    await sio.enter_room(sid, d.game_pin)
    await sio.enter_room(sid, _players_room(d.game_pin))
    await sio.emit(
        "rejoined_game",
        game_data.to_player_data(),
        room=sid,
    )


def _nickname_error(e: ValidationError) -> NicknameError | None:
    for err in e.errors():
        exc = (err.get("ctx") or {}).get("error")
        if isinstance(exc, NicknameError):
            return exc
    return None


@sio.event
async def join_game(sid: str, data: dict):
    if not isinstance(data, dict) or "game_pin" not in data:
        await sio.emit("error", room=sid)
        return
    redis_res = await redis.get(f"game:{data['game_pin']}")
    if redis_res is None:
        await sio.emit("game_not_found", room=sid)
        return
    try:
        d = JoinGameData(**data)
    except ValidationError as e:
        nickname_error = _nickname_error(e)
        if nickname_error is not None:
            await sio.emit(
                "username_invalid",
                UsernameInvalidEvent(code=nickname_error.code, message=nickname_error.message).model_dump(),
                room=sid,
            )
        else:
            await sio.emit("error", room=sid)
            print(e)
        return
    game_data = PlayGame.model_validate_json(redis_res)
    # Late join: players may join a running game unless the host locked it.
    if await redis.get(_locked_key(d.game_pin)) is not None:
        await sio.emit("game_locked", {"started": game_data.started}, room=sid)
        return
    if await redis.sismember(_banned_key(d.game_pin), d.username.casefold()):
        await sio.emit(
            "username_banned",
            {"message": "This nickname was removed from the game by the host."},
            room=sid,
        )
        return
    # +++ START checking captcha +++
    if game_data.captcha_enabled and d.captcha is not None:
        captcha_res = check_captcha(d.captcha)
        if not captcha_res:
            return
    # --- END checking captcha ---
    # SET NX claims the nickname atomically: two phones can't both get it.
    claimed = await redis.set(f"game_session:{d.game_pin}:players:{d.username}", sid, ex=KEY_TTL, nx=True)
    if not claimed:
        await sio.emit("username_already_exists", room=sid)
        return

    session = {
        "game_pin": d.game_pin,
        "username": d.username,
        "sid_custom": sid,
        "admin": False,
    }
    await save_session(sid, sio, session)
    await GamePlayer(username=d.username, sid=sid).to_player_stack(d.game_pin)
    # New players (late ones too) start at 0 and appear in the ranking at once.
    await redis.zadd(_leaderboard_key(d.game_pin), {d.username: 0}, nx=True)
    await redis.expire(_leaderboard_key(d.game_pin), KEY_TTL)
    await sio.enter_room(sid, d.game_pin)
    await sio.enter_room(sid, _players_room(d.game_pin))
    await sio.emit(
        "joined_game",
        game_data.to_player_data(),
        room=sid,
    )

    if d.custom_field == "":
        d.custom_field = None
    if d.custom_field is not None:
        await redis.hset(
            f"game:{d.game_pin}:players:custom_fields",
            d.username,
            d.custom_field,
        )

    await sio.emit(
        "player_joined",
        {"username": d.username, "sid": sid, "late": game_data.started},
        room=_admin_room(d.game_pin),
    )
    # +++ Time-Sync +++
    encrypted_datetime = fernet.encrypt(datetime.now().isoformat().encode("utf-8")).decode("utf-8")
    await sio.emit("time_sync", encrypted_datetime, room=sid)
    # --- Time-Sync ---
    if game_data.started:
        # Bring a late player to the current state of the game.
        await sio.emit("start_game", room=sid)
        q_index = game_data.current_question
        if (
            game_data.question_show
            and 0 <= q_index < len(game_data.questions)
            and game_data.questions[q_index].type != QuizQuestionType.SLIDE
        ):
            await sio.emit("set_question_number", _question_payload(game_data, q_index), room=sid)


class _RandomNicknameInput(BaseModel):
    game_pin: str | None = None


@sio.event
async def get_random_nickname(sid: str, data: dict | None = None):
    try:
        d = _RandomNicknameInput(**(data if isinstance(data, dict) else {}))
    except ValidationError:
        d = _RandomNicknameInput()
    nickname = random_nickname()
    if d.game_pin:
        # Try a few times to give a nickname nobody in this game has yet
        for _ in range(10):
            if await redis.get(f"game_session:{d.game_pin}:players:{nickname}") is None:
                break
            nickname = random_nickname()
    await sio.emit("random_nickname", {"nickname": nickname}, room=sid)


@sio.event
async def start_game(sid: str, _data: dict):
    session = await get_session(sid, sio)
    if not session["admin"]:
        return
    game_data = await PlayGame.get_from_redis(session["game_pin"])
    game_data.started = True
    await game_data.save(session["game_pin"])
    await redis.delete(f"game_in_lobby:{game_data.user_id.hex}")
    await sio.emit("start_game", room=session["game_pin"])


@sio.event
async def register_as_admin(sid: str, data: dict):
    try:
        d = RegisterAsAdminData(**data)
    except ValidationError as e:
        await sio.emit("error", room=sid)
        print(e)
        return
    game_pin = d.game_pin
    game_id = d.game_id
    if await redis.get(f"game_session:{game_pin}") is not None:
        await sio.emit("already_registered_as_admin", room=sid)
        return
    await GameSession(admin=sid, game_id=game_id, answers=[]).save(game_pin)
    game_data = await PlayGame.get_from_redis(game_pin)
    await sio.emit(
        "registered_as_admin",
        {"game_id": game_id, "game": game_data.model_dump(mode="json")},
        room=sid,
    )
    session = {"game_pin": game_pin, "admin": True, "remote": False}
    await save_session(sid, sio, session)
    await sio.enter_room(sid, game_pin)
    await sio.enter_room(sid, _admin_room(d.game_pin))
    await _emit_lock_state(game_pin, to=sid)


async def _set_lock(sid: str, locked: bool) -> None:
    session = await get_session(sid, sio)
    if not session.get("admin"):
        return
    game_pin = session["game_pin"]
    if locked:
        await redis.set(_locked_key(game_pin), "1", ex=KEY_TTL)
    else:
        await redis.delete(_locked_key(game_pin))
    await _emit_lock_state(game_pin)


@sio.event
async def lock_game(sid: str, _data: dict | None = None):
    await _set_lock(sid, True)


@sio.event
async def unlock_game(sid: str, _data: dict | None = None):
    await _set_lock(sid, False)


async def _emit_rank_updates(game_pin: str, question_index: int, answers: AnswerDataList) -> None:
    """Top 5 to the host screens, a personal rank_update to every phone."""
    gained = {a.username: a.score for a in answers}
    streaks = {u: int(v) for u, v in (await redis.hgetall(_streaks_key(game_pin))).items()}
    scores = await _total_scores(game_pin)
    sids = await _player_sids(game_pin)
    top5, updates = build_rank_updates(scores, gained, streaks)
    await sio.emit(
        "leaderboard",
        {"question_index": question_index, "top": top5, "total_players": len(scores)},
        room=_admin_room(game_pin),
    )
    own_answers = {a.username: a for a in answers}
    emits = []
    for username, player_sid in sids.items():
        # Phones render only their own result: send that one entry instead of
        # every player's answer (the payload stays a list for compatibility).
        own = own_answers.get(username)
        emits.append(_emit_to_sid("question_results", [own.model_dump(mode="json")] if own else [], player_sid))
        update = updates.get(username)
        if update is not None:
            emits.append(
                _emit_to_sid(
                    "rank_update",
                    RankUpdateEvent(question_index=question_index, **update).model_dump(),
                    player_sid,
                )
            )
    await asyncio.gather(*emits)


@sio.event
async def get_question_results(sid: str, data: dict):
    session = await get_session(sid, sio)
    if not session["admin"]:
        return
    game_pin = session["game_pin"]
    question_index = int(float(data["question_number"]))
    answer_data_list = await AnswerDataList.get_redis_or_empty(game_pin, question_index)
    game_data = await PlayGame.get_from_redis(game_pin)
    game_data.question_show = False
    await game_data.save(game_pin)
    # The question is over: refuse answers that arrive from now on.
    await redis.set(_closed_key(game_pin, question_index), "1", ex=KEY_TTL)
    if 0 <= question_index < len(game_data.questions) and _is_gradable(game_data.questions[question_index]):
        # No answer resets the streak, like a wrong one.
        answered = {a.username for a in answer_data_list}
        players = await redis.smembers(f"game_session:{game_pin}:players")
        missing = {GamePlayer.model_validate_json(p).username for p in players} - answered
        if missing:
            await redis.hset(_streaks_key(game_pin), mapping={u: 0 for u in missing})
            await redis.expire(_streaks_key(game_pin), KEY_TTL)
    # Host screens (admin + remote) keep the full list, as before.
    await sio.emit("question_results", answer_data_list.model_dump(mode="json"), room=_admin_room(game_pin))
    await _emit_rank_updates(game_pin, question_index, answer_data_list)


@sio.event
async def set_question_number(sid: str, data: str):
    # data is just a number (as a str) of the question
    session = await get_session(sid, sio)
    if not session["admin"]:
        return
    game_pin = session["game_pin"]
    q_index = int(float(data))
    game_data = await PlayGame.get_from_redis(session["game_pin"])
    game_data.current_question = q_index
    game_data.question_show = True
    await game_data.save(session["game_pin"])
    await redis.set(f"game:{session['game_pin']}:current_time", datetime.now().isoformat(), ex=7200)
    if game_data.questions[q_index].type == QuizQuestionType.SLIDE:
        await sio.emit(
            "set_question_number",
            {
                "question_index": q_index,
            },
            room=sid,
        )
        return
    await sio.emit(
        "set_question_number",
        _question_payload(game_data, q_index),
        room=game_pin,
    )


@sio.event
async def submit_answer(sid: str, data: dict):
    now = datetime.now()
    try:
        d = SubmitAnswerData(**data)
    except ValidationError as e:
        await sio.emit("error", room=sid)
        print(e)
        return
    d.answer = str(d.answer)
    session = await get_session(sid, sio)
    if "username" not in session:
        return
    game_pin = session["game_pin"]
    question_index = int(float(d.question_index))
    game_data = await PlayGame.get_from_redis(game_pin)

    if question_index != game_data.current_question or await redis.get(_closed_key(game_pin, question_index)):
        await sio.emit("question_not_active", room=sid)
        return
    started_raw = await redis.get(f"game:{game_pin}:current_time")
    if started_raw is None:
        await sio.emit("question_not_active", room=sid)
        return

    answer_right, answer = check_answer(game_data, d)
    latency = int(float(session.get("ping", 0)))
    time_q_started = datetime.fromisoformat(started_raw)
    diff = (time_q_started - now).total_seconds() * 1000  # - timedelta(milliseconds=latency)
    answer_data = await record_answer(
        game_pin=game_pin,
        game_data=game_data,
        question_index=question_index,
        username=session["username"],
        answer_right=answer_right,
        answer=answer,
        time_taken_ms=abs(diff) - latency,
    )
    if answer_data is None:
        await sio.emit("already_replied", room=sid)


@sio.event
async def get_final_results(sid: str, _data: dict):
    session: dict = await get_session(sid, sio)
    if not session["admin"]:
        return
    game_pin = session["game_pin"]
    game_data = await PlayGame.get_from_redis(game_pin)
    results = await generate_final_results(game_data, game_pin)
    # The full per-question results only go to the host screens; phones only
    # use this event as the "game over" signal, so they get an empty object.
    await sio.emit("final_results", results, room=_admin_room(game_pin))
    await sio.emit("final_results", {}, room=_players_room(game_pin))
    scores = await _total_scores(game_pin)
    top3, own = build_podium(scores)
    total_players = len(scores)
    await sio.emit(
        "podium",
        {"top": top3, "total_players": total_players, "rank": None, "total": None},
        room=_admin_room(game_pin),
    )
    sids = await _player_sids(game_pin)
    await asyncio.gather(
        *(
            _emit_to_sid(
                "podium",
                {
                    "top": top3,
                    "total_players": total_players,
                    "rank": own.get(username, {}).get("rank"),
                    "total": own.get(username, {}).get("total", 0),
                },
                player_sid,
            )
            for username, player_sid in sids.items()
        )
    )


@sio.event
async def get_export_token(sid: str):
    session = await get_session(sid, sio)
    if not session["admin"]:
        return
    game_data = await PlayGame.get_from_redis(session["game_pin"])
    results = await generate_final_results(game_data, session["game_pin"])
    token = os.urandom(32).hex()
    await redis.set(f"export_token:{token}", json.dumps(results), ex=7200)
    await sio.emit("export_token", token, room=sid)


@sio.event
async def show_solutions(sid: str, _data: dict):
    session: dict = await get_session(sid, sio)
    game_data = await PlayGame.get_from_redis(session["game_pin"])
    if not session["admin"]:
        return
    await sio.emit(
        "solutions",
        game_data.questions[game_data.current_question].model_dump(mode="json"),
        room=session["game_pin"],
    )


@sio.event
async def echo_time_sync(sid: str, data: str):
    then_dec = fernet.decrypt(data).decode("utf-8")
    then = datetime.fromisoformat(then_dec)
    now = datetime.now()
    delta = now - then
    session = await get_session(sid, sio)
    session["ping"] = delta.microseconds / 1000
    await save_session(sid, sio, session)


@sio.event
async def kick_player(sid: str, data: dict):
    try:
        d = KickPlayerInput(**data)
    except ValidationError as e:
        await sio.emit("error", room=sid)
        print(e)
        return

    session: dict = await get_session(sid, sio)
    if not session["admin"]:
        return
    game_pin = session["game_pin"]

    # Ban the nickname on the server: a cleared cookie can't bring it back.
    await redis.sadd(_banned_key(game_pin), d.username.casefold())
    await redis.expire(_banned_key(game_pin), KEY_TTL)
    await redis.zrem(_leaderboard_key(game_pin), d.username)
    player_sid = await redis.get(f"game_session:{game_pin}:players:{d.username}")
    await redis.srem(
        f"game_session:{game_pin}:players",
        GamePlayer(username=d.username, sid=player_sid).model_dump_json(),
    )
    if player_sid is None:
        return
    await sio.leave_room(player_sid, game_pin)
    await sio.leave_room(player_sid, _players_room(game_pin))
    await sio.emit("kick", room=player_sid)


class _RegisterAsRemoteInput(BaseModel):
    game_pin: str
    game_id: str


@sio.event
async def register_as_remote(sid: str, data: dict):
    try:
        d = _RegisterAsRemoteInput(**data)
    except ValidationError as e:
        await sio.emit("error", room=sid)
        print(e)
        return
    await sio.emit(
        "registered_as_admin",
        {"game_id": d.game_id, "game": await redis.get(f"game:{d.game_pin}")},
        room=sid,
    )
    await sio.emit("control_visibility", {"visible": False}, room=_admin_room(d.game_pin))
    session = await get_session(sid, sio)
    session["game_pin"] = d.game_pin
    session["admin"] = True
    session["remote"] = True
    await save_session(sid, sio, session)
    await sio.enter_room(sid, d.game_pin)
    await sio.enter_room(sid, _admin_room(d.game_pin))
    await _emit_lock_state(d.game_pin, to=sid)


class _SetControlVisibilityInput(BaseModel):
    visible: bool


@sio.event
async def set_control_visibility(sid: str, data: dict):
    try:
        d = _SetControlVisibilityInput(**data)
    except ValidationError as e:
        await sio.emit("error", room=sid)
        print(e)
        return
    session: dict = await get_session(sid, sio)
    await sio.emit(
        "control_visibility",
        {"visible": d.visible},
        room=_admin_room(session["game_pin"]),
    )


@sio.event
async def save_quiz(sid: str):
    session: dict = await get_session(sid, sio)
    if not session["admin"]:
        return
    await save_quiz_to_storage(session["game_pin"])
    # Only the host that asked (this went to every connected socket before)
    await sio.emit("results_saved_successfully", room=sid)


@sio.event
async def connect(sid: str, _environ, _auth):
    session_id = os.urandom(16).hex()
    print("Connection opened with handler")
    sio_session = {"session_id": session_id}
    await sio.save_session(sid, sio_session)
    # To the new socket only (this went to every connected socket before:
    # O(players^2) messages while 400 phones join, and it leaked session ids).
    await sio.emit("session_id", ConnectSessionIdEvent(session_id=session_id).model_dump(mode="json"), to=sid)
