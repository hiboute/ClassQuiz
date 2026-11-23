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
from datetime import datetime, timedelta

from classquiz.helpers.nickname import NicknameError, random_nickname
from classquiz.socket_server.helpers import (
    WordCloudError,
    check_answer,
    check_captcha,
    clean_word,
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


def _current_time_key(game_pin: str) -> str:
    # ISO start time of the open question's answer window (used for scoring)
    return f"game:{game_pin}:current_time"


def _question_token_key(game_pin: str) -> str:
    # Changes every time the host sets a question or ends the game, so a
    # get-ready countdown that is no longer current does nothing.
    return f"game:{game_pin}:question_token"


def _get_ready_key(game_pin: str) -> str:
    # Index of the question whose get-ready countdown is running
    return f"game:{game_pin}:get_ready"


def _paused_key(game_pin: str) -> str:
    # JSON {question_index, remaining} while the host has paused the timer
    return f"game:{game_pin}:paused"


def _ended_key(game_pin: str) -> str:
    # "1" once the host ended the game with end_game_now
    return f"game:{game_pin}:ended"


def _wc_key(game_pin: str, q_index: int, part: str) -> str:
    # Word cloud keys of question q: counts (ZSET), display (HASH), total,
    # throttle and trailing (rate limit of word_cloud_update)
    return f"game_session:{game_pin}:{q_index}:wc_{part}"


DEFAULT_GET_READY_SECONDS = 3
MAX_GET_READY_SECONDS = 10
WORD_CLOUD_TOP = 60
WORD_CLOUD_THROTTLE_MS = 500  # at most 2 word_cloud_update per second

# Keeps a reference to running background tasks (asyncio only holds weak ones)
_background_tasks: set = set()


async def _countdown_sleep(seconds: float) -> None:
    """Wait without blocking the event loop (a function so tests can patch it)."""
    await asyncio.sleep(seconds)


def _start_background(coro_fn, *args) -> None:
    task = sio.start_background_task(coro_fn, *args)
    if task is not None:
        _background_tasks.add(task)
        add_done_callback = getattr(task, "add_done_callback", None)
        if add_done_callback is not None:
            add_done_callback(_background_tasks.discard)


def _clean_get_ready_seconds(value, default: int = DEFAULT_GET_READY_SECONDS) -> int:
    """0..10 whole seconds; anything invalid falls back to `default`."""
    if value is None or isinstance(value, bool):
        return default
    try:
        seconds = int(float(value))
    except (TypeError, ValueError):
        return default
    return min(MAX_GET_READY_SECONDS, max(0, seconds))


def _time_limit_s(question) -> float:
    try:
        return max(0.0, float(question.time))
    except (TypeError, ValueError):
        return 0.0


def _is_gradable(question) -> bool:
    """Questions with a right answer (voting, slides and word clouds have none)."""
    return question.type not in (QuizQuestionType.VOTING, QuizQuestionType.SLIDE, QuizQuestionType.WORD_CLOUD)


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
    word_key: str | None = None,
) -> AnswerData | None:
    """Score and store one answer, update streak and leaderboard, notify the host.

    Returns None when the player had already answered this question.
    Shared by the Socket.IO players and the box controller. `word_key` is the
    counting key of a word cloud answer (`answer` is then its display form).
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
    if word_key is not None:
        await _add_word(game_pin, question_index, word_key, answer)
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


def _rejoin_token_key(game_pin: str) -> str:
    """HASH username -> secret the phone got in joined_game (proves who it is on rejoin)."""
    return f"game_session:{game_pin}:rejoin_tokens"


def _player_data(game_data: PlayGame, **extra) -> dict:
    data = game_data.to_player_data()
    if isinstance(data, tuple):  # to_player_data returns a 1-tuple
        data = data[0]
    return {**data, **extra}


async def _new_rejoin_token(game_pin: str, username: str) -> str:
    token = os.urandom(16).hex()
    await redis.hset(_rejoin_token_key(game_pin), username, token)
    await redis.expire(_rejoin_token_key(game_pin), KEY_TTL)
    return token


async def _rejoin_failed(sid: str, reason: str, message: str) -> None:
    await sio.emit("rejoin_failed", {"reason": reason, "message": message}, room=sid)


async def _send_open_question(sid: str, game_pin: str, game_data: PlayGame, username: str | None = None) -> None:
    """Bring a (re)joining phone to the open question: the question, the time
    left, whether this player already answered it, and a pause."""
    q_index = game_data.current_question
    if not (
        game_data.question_show
        and 0 <= q_index < len(game_data.questions)
        and game_data.questions[q_index].type != QuizQuestionType.SLIDE
    ):
        return
    if await redis.get(_closed_key(game_pin, q_index)) is not None:
        return
    payload = _question_payload(game_data, q_index)
    paused = await redis.get(_paused_key(game_pin))
    started_raw = await redis.get(_current_time_key(game_pin))
    if paused is not None:
        payload["remaining"] = float(json.loads(paused)["remaining"])
    elif started_raw is not None:
        elapsed = (datetime.now() - datetime.fromisoformat(_as_str(started_raw))).total_seconds()
        payload["remaining"] = round(max(0.0, _time_limit_s(game_data.questions[q_index]) - elapsed), 1)
    if username is not None:
        payload["already_answered"] = bool(
            await redis.sismember(f"game_session:{game_pin}:{q_index}:answered", username)
        )
    await sio.emit("set_question_number", payload, room=sid)
    if paused is not None:
        await sio.emit("game_paused", json.loads(paused), room=sid)


@sio.event
async def rejoin_game(sid: str, data: dict):
    """A phone that lost its socket (reload, network switch) takes its place back.

    Accepted when `old_sid` is the socket the server holds for this nickname
    (a plain reconnect), or when `rejoin_token` is the secret this phone got
    in `joined_game` (the held socket is a stale one of the same phone, e.g.
    after a reload raced a reconnect). Anything else gets `rejoin_failed`.
    """
    if not isinstance(data, dict) or "game_pin" not in data:
        await _rejoin_failed(sid, "invalid", "Join the game again.")
        return
    redis_res = await redis.get(f"game:{data['game_pin']}")
    if redis_res is None:
        await sio.emit("game_not_found", room=sid)
        await _rejoin_failed(sid, "game_not_found", "This game is over or no longer exists.")
        return
    try:
        d = RejoinGameData(**data)
    except ValidationError as e:
        await sio.emit("error", room=sid)
        await _rejoin_failed(sid, "invalid", "Join the game again.")
        print(e)
        return
    if await redis.sismember(_banned_key(d.game_pin), d.username.casefold()):
        # A kicked player reloading with the old cookie: kick again
        await sio.emit("kick", room=sid)
        return
    redis_sid_key = f"game_session:{d.game_pin}:players:{d.username}"
    held_sid = _as_str(await redis.get(redis_sid_key))
    if held_sid is None:
        await _rejoin_failed(sid, "unknown_player", "Your place in this game expired. Join again.")
        return
    stored_token = _as_str(await redis.hget(_rejoin_token_key(d.game_pin), d.username))
    token_ok = bool(d.rejoin_token) and stored_token is not None and d.rejoin_token == stored_token
    if held_sid == sid:
        pass  # this socket already rejoined (duplicate request): answer again
    elif held_sid == d.old_sid or token_ok:
        if held_sid != d.old_sid and held_sid != sid and sio.manager.is_connected(held_sid, "/"):
            # The same phone still has an older socket open here: retire it.
            await sio.leave_room(held_sid, d.game_pin)
            await sio.leave_room(held_sid, _players_room(d.game_pin))
    else:
        await _rejoin_failed(
            sid,
            "stale_session",
            "This nickname is already in use in this game. Join again with another one.",
        )
        return
    encrypted_datetime = fernet.encrypt(datetime.now().isoformat().encode("utf-8")).decode("utf-8")
    await sio.emit("time_sync", encrypted_datetime, room=sid)
    await redis.set(redis_sid_key, sid, ex=KEY_TTL)
    players_key = f"game_session:{d.game_pin}:players"
    async with redis.pipeline(transaction=False) as pipe:
        for old in {held_sid, d.old_sid}:
            pipe.srem(players_key, GamePlayer(username=d.username, sid=old).model_dump_json())
        pipe.sadd(players_key, GamePlayer(username=d.username, sid=sid).model_dump_json())
        await pipe.execute()
    await redis.zadd(_leaderboard_key(d.game_pin), {d.username: 0}, nx=True)
    token = stored_token if stored_token is not None else await _new_rejoin_token(d.game_pin, d.username)
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
        _player_data(game_data, username=d.username, rejoin_token=token),
        room=sid,
    )
    if game_data.started:
        await _send_open_question(sid, d.game_pin, game_data, d.username)


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
        # check_captcha passes when no captcha key is configured (captcha off)
        if not await check_captcha(d.captcha):
            await sio.emit("captcha_invalid", {"message": "The captcha check failed. Try again."}, room=sid)
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
    token = await _new_rejoin_token(d.game_pin, d.username)
    await sio.emit(
        "joined_game",
        _player_data(game_data, username=d.username, rejoin_token=token),
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
        await _send_open_question(sid, d.game_pin, game_data)


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
async def start_game(sid: str, data: dict | None = None):
    session = await get_session(sid, sio)
    if not session["admin"]:
        return
    game_data = await PlayGame.get_from_redis(session["game_pin"])
    game_data.started = True
    if isinstance(data, dict) and "get_ready_seconds" in data:
        # Optional: get-ready delay of every question of this game (0 disables)
        game_data.get_ready_seconds = _clean_get_ready_seconds(data["get_ready_seconds"])
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
    await redis.delete(_paused_key(game_pin))
    if (
        0 <= question_index < len(game_data.questions)
        and game_data.questions[question_index].type == QuizQuestionType.WORD_CLOUD
    ):
        # Final state of the cloud, not throttled
        await _emit_word_cloud(game_pin, question_index)
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


def _parse_set_question(data) -> tuple[int, object]:
    """(question index, optional get_ready_seconds) from the host's payload.

    The payload is the question index as a str or number (as before), or
    {"question_index": 2, "get_ready_seconds": 3}.
    """
    if isinstance(data, dict):
        raw = data.get("question_index", data.get("question_number"))
        return int(float(raw)), data.get("get_ready_seconds")
    return int(float(data)), None


def _get_ready_payload(game_data: PlayGame, index: int, seconds: int) -> dict:
    question = game_data.questions[index]
    payload = {
        "question_index": index,
        "question_count": len(game_data.questions),
        "title": question.question,
        "type": (question.type or QuizQuestionType.ABCD).value,
        "points": getattr(question.points, "value", question.points),
        "seconds": seconds,
    }
    if question.image:
        payload["image"] = question.image
    return payload


async def _open_question(game_pin: str, game_data: PlayGame, q_index: int, host_sid: str | None = None) -> None:
    """Open the answer window of question q_index now and send it out."""
    game_data.current_question = q_index
    game_data.question_show = True
    await game_data.save(game_pin)
    await redis.set(_current_time_key(game_pin), datetime.now().isoformat(), ex=KEY_TTL)
    await redis.delete(_get_ready_key(game_pin))
    if game_data.questions[q_index].type == QuizQuestionType.SLIDE:
        await sio.emit("set_question_number", {"question_index": q_index}, room=host_sid or _admin_room(game_pin))
        return
    await sio.emit("set_question_number", _question_payload(game_data, q_index), room=game_pin)


def _as_str(value) -> str | None:
    return value.decode() if isinstance(value, bytes) else value


async def _open_after_get_ready(game_pin: str, q_index: int, token: str, seconds: int) -> None:
    """Background task: wait out the get-ready screen, then open the question."""
    try:
        await _countdown_sleep(seconds)
        # The host moved on (or ended the game) during the countdown: do nothing.
        if _as_str(await redis.get(_question_token_key(game_pin))) != token:
            return
        if await redis.get(_ended_key(game_pin)) is not None:
            return
        game_data = await PlayGame.get_from_redis(game_pin)
        if game_data.current_question != q_index:
            return
        await _open_question(game_pin, game_data, q_index)
    except Exception as e:  # a background task has nobody to report to
        print(f"get_ready task failed for {game_pin}/{q_index}: {e!r}")


@sio.event
async def set_question_number(sid: str, data):
    # data is the question index (str or number), or a dict with
    # question_index and an optional get_ready_seconds for this question.
    session = await get_session(sid, sio)
    if not session["admin"]:
        return
    game_pin = session["game_pin"]
    try:
        q_index, seconds_raw = _parse_set_question(data)
    except (TypeError, ValueError):
        await sio.emit("error", room=sid)
        return
    game_data = await PlayGame.get_from_redis(game_pin)
    if not 0 <= q_index < len(game_data.questions):
        await sio.emit("error", room=sid)
        return
    if await redis.get(_ended_key(game_pin)) is not None:
        return
    seconds = _clean_get_ready_seconds(seconds_raw, _clean_get_ready_seconds(game_data.get_ready_seconds))
    token = os.urandom(8).hex()
    await redis.set(_question_token_key(game_pin), token, ex=KEY_TTL)
    await redis.delete(_paused_key(game_pin), _get_ready_key(game_pin))
    if seconds == 0 or game_data.questions[q_index].type == QuizQuestionType.SLIDE:
        # No get-ready screen: open at once, as before
        await _open_question(game_pin, game_data, q_index, host_sid=sid)
        return
    # Get ready: nobody can answer until the countdown is over. The previous
    # start time is removed so it cannot be used to score this question.
    game_data.current_question = q_index
    game_data.question_show = False
    await game_data.save(game_pin)
    await redis.delete(_current_time_key(game_pin))
    await redis.set(_get_ready_key(game_pin), str(q_index), ex=KEY_TTL)
    # The game room holds the phones and the host screens (admin room) alike.
    await sio.emit("get_ready", _get_ready_payload(game_data, q_index, seconds), room=game_pin)
    _start_background(_open_after_get_ready, game_pin, q_index, token, seconds)


async def _question_not_active(sid: str, question_index: int, reason: str) -> None:
    await sio.emit("question_not_active", {"question_index": question_index, "reason": reason}, room=sid)


@sio.event
async def submit_answer(sid: str, data: dict):
    now = datetime.now()
    try:
        d = SubmitAnswerData(**data)
    except ValidationError as e:
        await sio.emit("error", room=sid)
        print(e)
        return
    raw_answer = d.answer
    d.answer = str(d.answer)
    session = await get_session(sid, sio)
    if "username" not in session:
        return
    game_pin = session["game_pin"]
    question_index = int(float(d.question_index))
    game_data = await PlayGame.get_from_redis(game_pin)

    if question_index != game_data.current_question or await redis.get(_closed_key(game_pin, question_index)):
        await _question_not_active(sid, question_index, "closed")
        return
    if await redis.get(_get_ready_key(game_pin)) is not None:
        # Still on the get-ready screen: the answer window is not open yet
        await _question_not_active(sid, question_index, "get_ready")
        return
    if await redis.get(_paused_key(game_pin)) is not None:
        await _question_not_active(sid, question_index, "paused")
        return
    started_raw = await redis.get(_current_time_key(game_pin))
    if started_raw is None:
        await _question_not_active(sid, question_index, "not_open")
        return
    time_q_started = datetime.fromisoformat(_as_str(started_raw))
    if time_q_started > now:
        await _question_not_active(sid, question_index, "get_ready")
        return

    latency = int(float(session.get("ping", 0)))
    diff = (time_q_started - now).total_seconds() * 1000  # - timedelta(milliseconds=latency)
    time_taken_ms = abs(diff) - latency
    if game_data.questions[question_index].type == QuizQuestionType.WORD_CLOUD:
        await _submit_word(sid, session["username"], game_pin, game_data, question_index, raw_answer, time_taken_ms)
        return

    answer_right, answer = check_answer(game_data, d)
    answer_data = await record_answer(
        game_pin=game_pin,
        game_data=game_data,
        question_index=question_index,
        username=session["username"],
        answer_right=answer_right,
        answer=answer,
        time_taken_ms=time_taken_ms,
    )
    if answer_data is None:
        await sio.emit("already_replied", room=sid)


# --- Word cloud ---


async def _submit_word(
    sid: str, username: str, game_pin: str, game_data: PlayGame, q_index: int, raw, time_taken_ms: float
) -> None:
    """One free-text word per player: no points, no streak change."""
    try:
        display, key = clean_word(raw)
    except WordCloudError as e:
        # Refused words do not count as the player's answer: they can retry.
        await sio.emit(
            "word_cloud_refused",
            {"question_index": q_index, "code": e.code, "message": e.message, "max_length": 30},
            room=sid,
        )
        return
    answer_data = await record_answer(
        game_pin=game_pin,
        game_data=game_data,
        question_index=q_index,
        username=username,
        answer_right=False,
        answer=display,
        time_taken_ms=time_taken_ms,
        word_key=key,
    )
    if answer_data is None:
        await sio.emit("already_replied", room=sid)
        return
    await sio.emit("word_cloud_accepted", {"question_index": q_index, "text": display}, room=sid)
    await _word_cloud_changed(game_pin, q_index)


async def _add_word(game_pin: str, q_index: int, key: str, display: str) -> None:
    async with redis.pipeline(transaction=False) as pipe:
        pipe.zincrby(_wc_key(game_pin, q_index, "counts"), 1, key)
        # The first player's spelling is the one shown
        pipe.hsetnx(_wc_key(game_pin, q_index, "display"), key, display)
        pipe.incr(_wc_key(game_pin, q_index, "total"))
        for part in ("counts", "display", "total"):
            pipe.expire(_wc_key(game_pin, q_index, part), KEY_TTL)
        await pipe.execute()


async def _word_cloud_snapshot(game_pin: str, q_index: int) -> dict:
    top = await redis.zrevrange(_wc_key(game_pin, q_index, "counts"), 0, WORD_CLOUD_TOP - 1, withscores=True)
    keys = [_as_str(k) for k, _ in top]
    displays = await redis.hmget(_wc_key(game_pin, q_index, "display"), keys) if keys else []
    words = [
        {"text": _as_str(display) or key, "count": int(count)} for key, (_, count), display in zip(keys, top, displays)
    ]
    words.sort(key=lambda w: (-w["count"], w["text"].casefold()))
    total = int(await redis.get(_wc_key(game_pin, q_index, "total")) or 0)
    return {"question_index": q_index, "words": words, "total": total}


async def _emit_word_cloud(game_pin: str, q_index: int) -> None:
    await sio.emit("word_cloud_update", await _word_cloud_snapshot(game_pin, q_index), room=_admin_room(game_pin))


async def _word_cloud_changed(game_pin: str, q_index: int) -> None:
    """Send word_cloud_update at most every 500 ms per question, on all workers.

    The first word of a window is sent at once (the throttle key is taken
    with SET NX PX). Words that arrive while it is held are sent by one
    trailing task at the end of the window, so the host never misses the last
    words.
    """
    throttle = _wc_key(game_pin, q_index, "throttle")
    if await redis.set(throttle, "1", px=WORD_CLOUD_THROTTLE_MS, nx=True):
        await _emit_word_cloud(game_pin, q_index)
    elif await redis.set(_wc_key(game_pin, q_index, "trailing"), "1", px=10_000, nx=True):
        _start_background(_word_cloud_trailing, game_pin, q_index)


async def _word_cloud_trailing(game_pin: str, q_index: int) -> None:
    throttle = _wc_key(game_pin, q_index, "throttle")
    trailing = _wc_key(game_pin, q_index, "trailing")
    try:
        for _ in range(20):
            wait_ms = await redis.pttl(throttle)
            if wait_ms > 0:
                await _countdown_sleep(wait_ms / 1000)
            if await redis.set(throttle, "1", px=WORD_CLOUD_THROTTLE_MS, nx=True):
                # Released before the snapshot is read: a word stored after
                # this starts a new trailing task, so it is not lost.
                await redis.delete(trailing)
                await _emit_word_cloud(game_pin, q_index)
                return
    except Exception as e:
        print(f"word cloud task failed for {game_pin}/{q_index}: {e!r}")
    await redis.delete(trailing)


# --- Pause / resume / end now (host only) ---


async def _admin_game_pin(sid: str) -> str | None:
    session = await get_session(sid, sio)
    if not session.get("admin"):
        return None
    return session["game_pin"]


@sio.event
async def pause_game(sid: str, _data: dict | None = None):
    """Freeze the timer of the open question; answers are refused until resume."""
    game_pin = await _admin_game_pin(sid)
    if game_pin is None:
        return
    game_data = await PlayGame.get_from_redis(game_pin)
    q_index = game_data.current_question
    started_raw = await redis.get(_current_time_key(game_pin))
    reason = None
    if not 0 <= q_index < len(game_data.questions) or game_data.questions[q_index].type == QuizQuestionType.SLIDE:
        reason = "no_open_question"
    elif await redis.get(_get_ready_key(game_pin)) is not None:
        reason = "get_ready"
    elif not game_data.question_show or started_raw is None or await redis.get(_closed_key(game_pin, q_index)):
        reason = "no_open_question"
    elif await redis.get(_paused_key(game_pin)) is not None:
        reason = "already_paused"
    if reason is not None:
        await sio.emit("pause_refused", {"reason": reason}, room=sid)
        return
    elapsed = (datetime.now() - datetime.fromisoformat(_as_str(started_raw))).total_seconds()
    remaining = round(max(0.0, _time_limit_s(game_data.questions[q_index]) - elapsed), 1)
    payload = {"question_index": q_index, "remaining": remaining}
    await redis.set(_paused_key(game_pin), json.dumps(payload), ex=KEY_TTL)
    await sio.emit("game_paused", payload, room=game_pin)


@sio.event
async def resume_game(sid: str, _data: dict | None = None):
    """Restart the timer where it was frozen."""
    game_pin = await _admin_game_pin(sid)
    if game_pin is None:
        return
    raw = await redis.get(_paused_key(game_pin))
    if raw is None:
        await sio.emit("pause_refused", {"reason": "not_paused"}, room=sid)
        return
    paused = json.loads(raw)
    await redis.delete(_paused_key(game_pin))
    game_data = await PlayGame.get_from_redis(game_pin)
    q_index = paused["question_index"]
    if q_index != game_data.current_question or not 0 <= q_index < len(game_data.questions):
        return
    # Move the start time so the elapsed time is what it was at the pause:
    # scoring and the remaining time carry on from there.
    elapsed = max(0.0, _time_limit_s(game_data.questions[q_index]) - float(paused["remaining"]))
    new_start = datetime.now() - timedelta(seconds=elapsed)
    await redis.set(_current_time_key(game_pin), new_start.isoformat(), ex=KEY_TTL)
    await sio.emit("game_resumed", paused, room=game_pin)


@sio.event
async def end_game_now(sid: str, _data: dict | None = None):
    """Stop the game at once and show the final podium."""
    game_pin = await _admin_game_pin(sid)
    if game_pin is None:
        return
    await redis.set(_ended_key(game_pin), "1", ex=KEY_TTL)
    # A new token cancels a running get-ready countdown
    await redis.set(_question_token_key(game_pin), os.urandom(8).hex(), ex=KEY_TTL)
    await redis.delete(_paused_key(game_pin), _get_ready_key(game_pin))
    game_data = await PlayGame.get_from_redis(game_pin)
    if 0 <= game_data.current_question < len(game_data.questions):
        await redis.set(_closed_key(game_pin, game_data.current_question), "1", ex=KEY_TTL)
    game_data.question_show = False
    await game_data.save(game_pin)
    await sio.emit("game_ended", {"reason": "host"}, room=game_pin)
    await _send_final_results(game_pin)


@sio.event
async def get_final_results(sid: str, _data: dict):
    session: dict = await get_session(sid, sio)
    if not session["admin"]:
        return
    await _send_final_results(session["game_pin"])


async def _send_final_results(game_pin: str) -> None:
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
