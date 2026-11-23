#!/usr/bin/env python3
"""Socket.IO load test for the live quiz: N phones join one game and answer.

Each player is one python-socketio AsyncClient doing what the phone does:
connect (polling, then websocket upgrade, like socket.io-client), join_game,
echo time_sync, then answer every question after a random think time. It
follows the current socket contract (SOCKET-CONTRACT-CHANGES.md): get_ready
before each question, CHECK answers as index strings ("02"), WORD_CLOUD
answers as free text, rank_update after each result, podium at the end.

Answer latency is measured with a Socket.IO acknowledgement: the server sends
the ack once the submit_answer handler has finished (stored, scored,
host notified), so it is the real round trip of one answer.

Two ways to run it:

1. Against a game a person hosts (presenter screen, captcha off):

    uv run --with "python-socketio[asyncio_client]" \\
        python simulate_players_async.py --url https://quiz.indiatechhub.xyz \\
        --pin 123456 --players 400 --ramp 20

   Wait until the lobby shows every player, then run the game by hand. The
   players leave when the podium arrives (or on Ctrl-C).

2. Fully automatic (--drive): the script signs in as the organiser, creates a
   5-question quiz (ABCD, ABCD double, CHECK, WORD_CLOUD, VOTING), starts it,
   registers as the host over Socket.IO, waits for every player, plays every
   question (results as soon as everyone answered or the time is up), then
   asks for the podium:

    python simulate_players_async.py --url http://localhost:8080 --drive \\
        --login admin --password '...' --players 400 --ramp 20

   With --processes N the players are spread over N processes (a single
   Python process can be the bottleneck above ~200 sockets).

It prints a summary every 5 s and a final one with join time, answer latency
p50/p95, the host-side timings and every error event counted.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import multiprocessing
import os
import random
import statistics
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter
from http.cookiejar import CookieJar

import socketio

stats: Counter = Counter()
join_ms: list[float] = []
answer_ms: list[float] = []
connect_ms: list[float] = []
rank_ms: list[float] = []  # get_question_results (host) -> rank_update (phone)

ERROR_EVENTS = (
    "game_not_found",
    "username_already_exists",
    "username_invalid",
    "username_banned",
    "game_locked",
    "captcha_invalid",
    "already_replied",
    "question_not_active",
    "word_cloud_refused",
    "rejoin_failed",
    "error",
    "kick",
)
WORDS = ["Coffee", "Chai", "Sleep", "Meetings", "Code", "Gym", "Traffic", "Music", "Rain", "Focus"]


def pct(values: list[float], p: float) -> float:
    if not values:
        return float("nan")
    s = sorted(values)
    return s[min(len(s) - 1, int(p * len(s)))]


class Player:
    def __init__(self, idx: int, args: argparse.Namespace):
        self.idx = idx
        self.args = args
        self.name = f"{args.prefix}{idx}"
        self.sio = socketio.AsyncClient(reconnection=True, reconnection_attempts=5)
        self.t_join = 0.0
        self.done = asyncio.Event()
        on = self.sio.on

        @on("connect")
        async def _connect():
            stats["connected"] += 1

        @on("disconnect")
        async def _disconnect(*_):
            stats["disconnects"] += 1

        @on("joined_game")
        async def _joined(_data):
            stats["joined"] += 1
            join_ms.append((time.monotonic() - self.t_join) * 1000)

        @on("time_sync")
        async def _time_sync(data):
            await self.sio.emit("echo_time_sync", data)

        @on("start_game")
        async def _start(*_):
            stats["start_game"] += 1

        @on("get_ready")
        async def _get_ready(*_):
            stats["get_ready"] += 1

        @on("set_question_number")
        async def _question(data):
            stats["questions_seen"] += 1
            question = (data or {}).get("question")
            if not question:
                return  # a slide
            asyncio.create_task(self.answer(data["question_index"], question))

        @on("rank_update")
        async def _rank(data):
            stats["rank_update"] += 1
            sent = (data or {}).get("question_index")
            t0 = self.args._results_at.get(sent) if hasattr(self.args, "_results_at") else None
            if t0:
                rank_ms.append((time.time() - t0) * 1000)

        @on("podium")
        async def _podium(data):
            stats["podium"] += 1
            if data and data.get("rank"):
                stats["podium_with_rank"] += 1
            self.done.set()

        for event in ("question_results", "everyone_answered", "word_cloud_accepted", "final_results", "game_ended"):
            self.sio.on(event, self._counter(event))
        for event in ERROR_EVENTS:
            self.sio.on(event, self._counter(f"ERR_{event}"))
        # Host-only events: a phone must never get them (they used to be broadcast).
        for event in ("player_answer", "leaderboard", "word_cloud_update", "player_joined"):
            self.sio.on(event, self._counter(f"LEAK_{event}"))

    @staticmethod
    def _counter(name: str):
        async def handler(*_):
            stats[name] += 1

        return handler

    async def answer(self, q_index: int, question: dict) -> None:
        a = self.args
        await asyncio.sleep(random.uniform(a.min_think, a.max_think))
        qtype = str(question.get("type") or "ABCD").upper()
        answers = question.get("answers")
        if qtype == "WORD_CLOUD":
            answer = random.choice(WORDS)
        elif qtype == "CHECK" and isinstance(answers, list) and answers:
            picks = sorted(random.sample(range(len(answers)), k=random.randint(1, len(answers))))
            answer = "".join(str(i) for i in picks)
        elif isinstance(answers, list) and answers:
            answer = random.choice(answers)["answer"]
        else:
            stats["skipped_unsupported"] += 1
            return
        t0 = time.monotonic()
        try:
            await self.sio.call("submit_answer", {"question_index": q_index, "answer": answer}, timeout=30)
            answer_ms.append((time.monotonic() - t0) * 1000)
            stats["answers_acked"] += 1
        except Exception:  # noqa: BLE001
            stats["ERR_answer_timeout"] += 1

    async def run(self) -> None:
        t0 = time.monotonic()
        try:
            await self.sio.connect(self.args.url, socketio_path="socket.io", wait_timeout=30)
        except Exception as e:  # noqa: BLE001
            stats["ERR_connect_failed"] += 1
            if self.args.verbose:
                print(f"{self.name}: connect failed: {e!r}")
            return
        connect_ms.append((time.monotonic() - t0) * 1000)
        self.t_join = time.monotonic()
        await self.sio.emit("join_game", {"username": self.name, "game_pin": self.args.pin, "captcha": None})
        waiter = asyncio.create_task(self.sio.wait())
        await asyncio.wait({waiter, asyncio.create_task(self.done.wait())}, return_when=asyncio.FIRST_COMPLETED)
        await asyncio.sleep(1)
        await self.sio.disconnect()


def summary() -> str:
    c = f"connect p50 {pct(connect_ms, .5):.0f} ms p95 {pct(connect_ms, .95):.0f} ms"
    j = f"join (join_game -> joined_game) p50 {pct(join_ms, .5):.0f} ms p95 {pct(join_ms, .95):.0f} ms max {max(join_ms, default=0):.0f} ms"
    a = (
        f"answer ack p50 {pct(answer_ms, .5):.0f} ms p95 {pct(answer_ms, .95):.0f} ms max {max(answer_ms):.0f} ms (n={len(answer_ms)})"
        if answer_ms
        else "no answer acked yet"
    )
    r = f"results -> rank_update p50 {pct(rank_ms, .5):.0f} ms p95 {pct(rank_ms, .95):.0f} ms" if rank_ms else ""
    return f"{dict(sorted(stats.items()))}\n  {c}\n  {j}\n  {a}\n  {r}"


async def reporter() -> None:
    while True:
        await asyncio.sleep(5)
        print(time.strftime("%H:%M:%S"), summary(), flush=True)


# ---------------------------------------------------------------- host driver

QUIZ = {
    "public": False,
    "title": "Load test",
    "description": "Created by simulate_players_async.py",
    "questions": [
        {"question": "Load test ABCD", "time": "20", "type": "ABCD", "points": "standard",
         "answers": [{"answer": a, "right": i == 0} for i, a in enumerate(["A1", "B1", "C1", "D1"])]},
        {"question": "Load test double", "time": "20", "type": "ABCD", "points": "double",
         "answers": [{"answer": a, "right": i == 1} for i, a in enumerate(["A2", "B2", "C2", "D2"])]},
        {"question": "Load test check", "time": "20", "type": "CHECK", "points": "standard",
         "answers": [{"answer": a, "right": i in (0, 2)} for i, a in enumerate(["A3", "B3", "C3", "D3"])]},
        {"question": "Load test word cloud", "time": "20", "type": "WORD_CLOUD", "points": "none", "answers": []},
        {"question": "Load test poll", "time": "20", "type": "VOTING", "points": "none",
         "answers": [{"answer": a} for a in ["P1", "P2", "P3", "P4"]]},
    ],
}


class Api:
    def __init__(self, base: str):
        self.base = base.rstrip("/")
        self.jar = CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))

    def call(self, method: str, path: str, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base + path, data=data, method=method,
                                     headers={"Content-Type": "application/json"})
        with self.opener.open(req, timeout=30) as r:
            raw = r.read()
            return json.loads(raw) if raw else None

    def cookie_header(self) -> str:
        return "; ".join(f"{c.name}={c.value}" for c in self.jar)


def start_game(args) -> tuple[str, str]:
    api = Api(args.url)
    s = api.call("POST", "/api/v1/login/start", {"email": args.login})
    api.call("POST", f"/api/v1/login/step/1?session_id={s['session_id']}",
             {"auth_type": "PASSWORD", "data": args.password})
    quiz_id = args.quiz_id
    if not quiz_id:
        token = api.call("POST", "/api/v1/editor/start?edit=false")["token"]
        title = f"Load test {time.strftime('%H%M%S')}"
        api.call("POST", f"/api/v1/editor/finish?edit_id={token}", {**QUIZ, "title": title})
        quiz_id = next(q["id"] for q in api.call("GET", "/api/v1/quiz/list?page_size=100") if q["title"] == title)
    q = urllib.parse.urlencode({"game_mode": "normal", "captcha_enabled": "False", "cqcs_enabled": "False"})
    game = api.call("POST", f"/api/v1/quiz/start/{quiz_id}?{q}")
    return str(game["game_pin"]), str(game["game_id"])


async def drive_host(args, joined_target: int, results_at: dict) -> dict:
    """Host over Socket.IO: lobby, every question, results, podium."""
    host = socketio.AsyncClient()
    ev: dict[str, asyncio.Event] = {k: asyncio.Event() for k in ("registered", "opened", "everyone", "results", "podium", "leaderboard")}
    st = {"joined": 0, "answers": 0, "player_count": 0, "q": None, "words": 0, "events": Counter()}
    timings: dict = {"questions": []}

    @host.on("registered_as_admin")
    async def _reg(d):
        st["game"] = d["game"] if isinstance(d["game"], dict) else json.loads(d["game"])
        ev["registered"].set()

    @host.on("player_joined")
    async def _pj(_d):
        st["joined"] += 1

    @host.on("set_question_number")
    async def _sq(d):
        st["opened_at"] = time.monotonic()
        ev["opened"].set()

    @host.on("player_answer")
    async def _pa(d):
        st["answers"] = d.get("answer_count", st["answers"] + 1)
        st["player_count"] = d.get("player_count", st["player_count"])

    @host.on("everyone_answered")
    async def _ea(_d):
        ev["everyone"].set()

    @host.on("question_results")
    async def _qr(_d):
        ev["results"].set()

    @host.on("leaderboard")
    async def _lb(_d):
        ev["leaderboard"].set()

    @host.on("word_cloud_update")
    async def _wc(d):
        st["words"] += 1

    @host.on("podium")
    async def _pod(d):
        st["podium"] = d
        ev["podium"].set()

    for e in ("error", "pause_refused", "already_registered_as_admin"):
        host.on(e, (lambda name: (lambda *_: st["events"].update([name])))(e))

    await host.connect(args.url, socketio_path="socket.io", wait_timeout=30)
    await host.emit("register_as_admin", {"game_pin": args.pin, "game_id": args.game_id})
    await asyncio.wait_for(ev["registered"].wait(), 20)
    n_questions = len(st["game"]["questions"])
    t_wait = time.monotonic()
    while st["joined"] < joined_target and time.monotonic() - t_wait < args.join_timeout:
        await asyncio.sleep(0.5)
    timings["joined"] = st["joined"]
    timings["lobby_wait_s"] = round(time.monotonic() - t_wait, 1)
    print(f"HOST: {st['joined']}/{joined_target} players in the lobby, starting", flush=True)
    await host.emit("start_game", {"get_ready_seconds": 3})
    await asyncio.sleep(1)
    for qi in range(n_questions):
        for k in ("opened", "everyone", "results", "leaderboard"):
            ev[k].clear()
        st["answers"] = 0
        t_set = time.monotonic()
        await host.emit("set_question_number", str(qi))
        await asyncio.wait_for(ev["opened"].wait(), 20)
        opened = time.monotonic()
        limit = float(st["game"]["questions"][qi]["time"]) + 1
        try:
            await asyncio.wait_for(ev["everyone"].wait(), limit)
            everyone = True
        except asyncio.TimeoutError:
            everyone = False
        all_in = time.monotonic()
        results_at[qi] = time.time()
        await host.emit("get_question_results", {"question_number": str(qi), "game_id": args.game_id})
        await asyncio.wait_for(ev["results"].wait(), 30)
        res = time.monotonic()
        q = {
            "q": qi,
            "type": st["game"]["questions"][qi]["type"],
            "get_ready_s": round(opened - t_set, 2),
            "answers": st["answers"],
            "everyone_answered": everyone,
            "answer_window_s": round(all_in - opened, 2),
            "results_ms": round((res - all_in) * 1000),
        }
        timings["questions"].append(q)
        print("HOST:", q, flush=True)
        await asyncio.sleep(args.results_pause)
    t_fin = time.monotonic()
    await host.emit("get_final_results", {})
    await asyncio.wait_for(ev["podium"].wait(), 30)
    timings["podium_ms"] = round((time.monotonic() - t_fin) * 1000)
    timings["podium_top"] = st["podium"]["top"]
    timings["podium_total_players"] = st["podium"]["total_players"]
    timings["word_cloud_updates"] = st["words"]
    timings["host_errors"] = dict(st["events"])
    await asyncio.sleep(2)
    await host.disconnect()
    return timings


# ---------------------------------------------------------------- runners


async def run_players(args, indexes: list[int]) -> None:
    players = [Player(i, args) for i in indexes]
    rep = asyncio.create_task(reporter()) if not args.quiet else None
    tasks = []
    gap = args.ramp / max(1, len(players))
    for pl in players:
        tasks.append(asyncio.create_task(pl.run()))
        await asyncio.sleep(gap)
    try:
        await asyncio.gather(*tasks)
    finally:
        if rep:
            rep.cancel()


def _child(args, indexes, results_at, queue):
    args._results_at = results_at
    try:
        asyncio.run(run_players(args, indexes))
    finally:
        queue.put({"stats": dict(stats), "join_ms": join_ms, "answer_ms": answer_ms,
                   "connect_ms": connect_ms, "rank_ms": rank_ms})


async def main_async(args) -> None:
    if not args.drive:
        args._results_at = {}
        rep = asyncio.create_task(reporter())
        try:
            await run_players(args, list(range(args.players)))
        finally:
            rep.cancel()
            print("FINAL", summary())
        return

    args.pin, args.game_id = start_game(args)
    print(f"Game {args.pin} started (game id {args.game_id})", flush=True)
    mgr = multiprocessing.Manager()
    results_at = mgr.dict()
    queue = mgr.Queue()
    procs = []
    n = max(1, args.processes)
    for k in range(n):
        idx = list(range(k, args.players, n))
        pargs = argparse.Namespace(**{**vars(args), "quiet": True})
        p = multiprocessing.Process(target=_child, args=(pargs, idx, results_at, queue))
        p.start()
        procs.append(p)
    t0 = time.monotonic()
    timings = await drive_host(args, args.players, results_at)
    for p in procs:
        await asyncio.get_running_loop().run_in_executor(None, p.join, 60)
    for _ in procs:
        part = queue.get(timeout=30)
        stats.update(part["stats"])
        join_ms.extend(part["join_ms"])
        answer_ms.extend(part["answer_ms"])
        connect_ms.extend(part["connect_ms"])
        rank_ms.extend(part["rank_ms"])
    timings["total_s"] = round(time.monotonic() - t0, 1)
    print("HOST TIMINGS", json.dumps(timings, indent=1))
    print("FINAL", summary())
    if args.json_out:
        with open(args.json_out, "w") as f:
            json.dump({"timings": timings, "stats": dict(stats),
                       "connect_p50": pct(connect_ms, .5), "connect_p95": pct(connect_ms, .95),
                       "join_p50": pct(join_ms, .5), "join_p95": pct(join_ms, .95), "join_max": max(join_ms, default=0),
                       "answer_p50": pct(answer_ms, .5), "answer_p95": pct(answer_ms, .95),
                       "answer_max": max(answer_ms, default=0), "answers": len(answer_ms),
                       "rank_p50": pct(rank_ms, .5), "rank_p95": pct(rank_ms, .95)}, f, indent=1)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--url", default="https://quiz.indiatechhub.xyz")
    p.add_argument("--pin", help="Six-digit game PIN shown on the presenter screen (not with --drive)")
    p.add_argument("--players", type=int, default=400)
    p.add_argument("--ramp", type=float, default=20, help="Seconds over which players join")
    p.add_argument("--min-think", type=float, default=0.5, help="Seconds, before answering")
    p.add_argument("--max-think", type=float, default=6.0, help="Seconds, before answering")
    p.add_argument("--prefix", default="lt", help="Player name prefix (names must be unique per game)")
    p.add_argument("--drive", action="store_true", help="Create and host the game too (needs --login/--password)")
    p.add_argument("--login", default=os.environ.get("CQ_LOGIN", "admin"))
    p.add_argument("--password", default=os.environ.get("CQ_PASSWORD"))
    p.add_argument("--quiz-id", help="With --drive: host this quiz instead of creating one")
    p.add_argument("--processes", type=int, default=1, help="With --drive: player processes")
    p.add_argument("--join-timeout", type=float, default=120)
    p.add_argument("--results-pause", type=float, default=2, help="Seconds on each result screen")
    p.add_argument("--json-out")
    p.add_argument("--quiet", action="store_true")
    p.add_argument("--verbose", action="store_true")
    args = p.parse_args()
    if not args.drive and not args.pin:
        p.error("--pin is required without --drive")
    if args.drive and not args.password:
        p.error("--drive needs --password (or CQ_PASSWORD)")
    try:
        asyncio.run(main_async(args))
    except KeyboardInterrupt:
        print("FINAL", summary())
        sys.exit(130)


if __name__ == "__main__":
    main()
