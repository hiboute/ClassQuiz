# Socket contract changes (live competitive quiz)

Backend changes for a 400-phone live quiz. This file lists every Socket.IO event
that is new or changed, so the frontend can be wired to it. Nothing here needs a
DB migration.

Direction: **S→C** means server to client, **C→S** means client to server.

## Rooms (server side)

| Room | Who is in it |
|---|---|
| `<game_pin>` | host, remote and every phone (as before) |
| `admin:<game_pin>` | host screen and remote (as before) |
| `players:<game_pin>` | **new**: phones only (joined via `join_game` or `rejoin_game`) |

Every `sio.emit` in `classquiz/socket_server` now names a room or a sid. Room
broadcasts go through Redis (`AsyncRedisManager` on `settings.redis`, channel
`classquiz-socketio`), so they reach sockets on every gunicorn worker. A socket
still has to stay on the worker it connected to: use sticky sessions, or the
websocket-only transport.

---

## Changed events

### `player_answer` (S→C, host only)
- **Before:** sent to every connected socket, payload `{}`.
- **Now:** sent to `admin:<pin>` only, each time a player answers.
- Payload: `{"answer_count": 12, "player_count": 400}`. The frontend can keep
  doing `answer_count += 1`, or read the counts from the payload.

### `everyone_answered` (S→C, host + phones of this game)
- **Before:** sent to every connected socket.
- **Now:** sent to the `<pin>` room only. Payload is still `{}`.

### `question_results` (S→C)
Sent when the host emits `get_question_results`.
- **Host / remote (`admin:<pin>`)**: same as before, the full list of
  `AnswerData`, plus two new fields on each entry:
  ```json
  [{"username": "ann", "answer": "a", "right": true, "time_taken": 812.0,
    "score": 1100, "streak": 2, "streak_bonus": 100}]
  ```
  `score` is the total gained on the question, streak bonus included, and
  matches the `player_scores` hash.
- **Phones**: each phone now gets **only its own entry**: a list with one
  element, or `[]` if it did not answer. Phones used to get every player's
  answers. It is still a list of the same shape, so `results_kahoot.svelte`
  (`+gained`, `Total score`) works unchanged.
- **Breaking for the old phone end screen:** the phone used to build its
  final top 5 from everyone's `question_results`. It now knows only its own
  score, so wire the end screen to `podium` (below).

### `final_results` (S→C)
- **Host / remote (`admin:<pin>`)**: unchanged, the full
  `{question_index: [AnswerData...]}` dict.
- **Phones (`players:<pin>`)**: `{}`. The phone only used this as a
  "game over" signal (any value other than `[null]`). Read the ranking from
  `podium`.

### `player_joined` (S→C, host only)
- Adds `late`: `{"username": "ann", "sid": "...", "late": true}`. `late` is
  `true` when the player joined after `start_game`.

### `join_game` (C→S): server-side nickname validation and late join
Request payload unchanged: `{username, game_pin, captcha?, custom_field?}`.

Checks, in order. Each one ends the join with the event shown:
1. Game missing: `game_not_found` (unchanged).
2. Invalid nickname: **`username_invalid`** (new, below).
3. Game locked by the host: **`game_locked`** (new).
4. Nickname banned (kicked earlier in this game): **`username_banned`** (new).
5. Nickname taken: `username_already_exists` (unchanged; the claim is now
   atomic).

**`game_already_started` is no longer sent.** A running game accepts new
players unless it is locked. A late player starts at 0 points and gets, in
order: `joined_game`, `time_sync`, `start_game`, then `set_question_number`
for the current question if one is open. They can answer it, scored from the
question's real start time.

The nickname is stored **trimmed, with inner whitespace collapsed**:
`"  Léa  "` becomes `"Léa"`. The phone should keep the server's value. It is
not echoed back yet, so trim on the client the same way, or read the
`random_nickname` value.

### `rejoin_game` (C→S)
- A kicked player who reloads with the old cookie now gets `kick` again,
  instead of rejoining.

### `kick_player` (C→S, host only)
- Also bans the nickname, case-insensitively, for the rest of the game (Redis
  set, 2 h). It removes the player from the leaderboard and from the
  `players:<pin>` room. The kicked phone gets `kick`, as before.

### `submit_answer` (C→S)
- Answers that arrive after the host showed that question's results get
  `question_not_active`.
- Scoring:
  - Correct answer: `round(base * (1 - (t/T)/2))`, clamped to
    `[base/2, base]`, where `t` is the answer time and `T` the time limit.
  - Answers under 0.5 s score `base`. A wrong answer scores 0. A score is never
    negative.
  - `base` comes from the question's `points` setting.
- Streak:
  - A correct answer adds 1 to the streak. A wrong answer, or no answer by the
    time results are shown, resets it to 0. Voting questions and slides do not
    touch it.
  - Bonus: `min(100 * (streak - 1), 500)`, only on questions that award points.

### `session_id` (S→C)
- Sent to the connecting socket only. It used to go to every connected socket.

### `results_saved_successfully` (S→C)
- Sent to the host that emitted `save_quiz` only. It used to go to every
  connected socket.

### `set_question_number` (S→C)
- `question` now carries `points`: `"standard" | "double" | "none"`. A phone
  can show "Double points!" with it.

---

## New events

### `rank_update` (S→C, each phone, personal)
Sent to every phone right after `question_results`.
```json
{
  "question_index": 3,
  "rank": 7,
  "total_players": 400,
  "total": 4210,
  "gained": 1100,
  "streak": 2,
  "behind_username": "ann",
  "behind_gap": 230
}
```
- `behind_username` is the player one rank above, and `behind_gap` the points
  between you. Both are `null` for rank 1.
- Ties are ordered by username, so ranks are always 1..N with no gaps.

### `leaderboard` (S→C, host + remote)
Sent to `admin:<pin>` right after `question_results`.
```json
{
  "question_index": 3,
  "total_players": 400,
  "top": [{"username": "ann", "score": 4440, "gained": 1000}]
}
```
`top` holds at most 5 entries, best first. `score` is the total and `gained`
the points from this question.

### `podium` (S→C)
Sent when the host emits `get_final_results`, after `final_results`.
- **Each phone**:
  ```json
  {"top": [{"rank": 1, "username": "ann", "score": 9100},
           {"rank": 2, "username": "bob", "score": 8800},
           {"rank": 3, "username": "cid", "score": 8650}],
   "total_players": 400, "rank": 57, "total": 5120}
  ```
- **Host / remote (`admin:<pin>`)**: the same payload with `"rank": null` and
  `"total": null`.
- `top` holds at most 3 entries.

### `lock_game` / `unlock_game` (C→S, host only)
- Payload: none, or `{}`. Ignored when it comes from a phone.
- Effect: a locked game refuses every new `join_game`, in the lobby or while
  running. Rejoins of players already in the game still work.

### `game_lock_state` (S→C, host + remote)
- Payload: `{"locked": true}`.
- Sent to `admin:<pin>` after every `lock_game` or `unlock_game`.
- Sent to the host right after `registered_as_admin`, and to a remote right
  after it registers.

### `game_locked` (S→C, the joining phone)
- Payload: `{"started": true}`. Reply to a `join_game` refused because the game
  is locked.

### `username_invalid` (S→C, the joining phone)
```json
{"code": "too_short", "message": "The nickname must be at least 2 characters.",
 "min_length": 2, "max_length": 20}
```
- `code` is one of `too_short`, `too_long`, `invalid_characters`,
  `profanity` or `invalid_type`.
- `message` is English and ready to display. Translate by `code` if needed.
- The rules:
  - The nickname is trimmed, then must be 2 to 20 characters long.
  - Allowed characters: letters from any script (accents included), digits,
    space, and `- _ . '` (`’` too).
  - The nickname must contain at least one letter or digit.
  - It is checked against a small FR + EN profanity list. Before the check it
    is normalised: case, accents, leetspeak (0→o 1→i 3→e 4→a 5→s @→a),
    separators, repeated letters.
- The current join form refuses names of 3 characters or fewer on the client.
  The server accepts 2.

### `username_banned` (S→C, the joining phone)
- Payload:
  `{"message": "This nickname was removed from the game by the host."}`.
- Sent when someone joins with a nickname the host kicked. It is deliberately
  not `kick`, so an innocent player who picks the same name does not get the
  "kicked" cookie.

### `get_random_nickname` (C→S) and `random_nickname` (S→C)
- Request: `{"game_pin": "123456"}`. `game_pin` is optional. With it, the
  server avoids names already taken in that game.
- Reply to the same socket: `{"nickname": "Swift Otter"}`. The name is an
  adjective + noun, English, always valid.
- REST equivalent: `GET /api/v1/live/random_nickname?game_pin=123456` returns
  `{"nickname": "..."}`.

---

## Quiz data: `points` per question

`QuizQuestion.points`: `"standard"` (1000, the default), `"double"` (2000) or
`"none"` (0).
- It is optional. Questions are stored as JSON in `quiz.questions`, so
  existing quizzes load as `standard` and **no migration is needed**.
- `null`, an empty value or an unknown value also becomes `standard`.
- The editor can send it as a field of each question.

## Redis keys added (all expire after 2 h, like the others)

| Key | Type | Content |
|---|---|---|
| `game_session:<pin>:<q>:answered` | SET | usernames that answered question q (dedupe via SADD) |
| `game_session:<pin>:streaks` | HASH | username → current streak |
| `game_session:<pin>:leaderboard` | ZSET | username → total score (alongside `player_scores`) |
| `game_session:<pin>:banned` | SET | kicked usernames, casefolded |
| `game_session:<pin>:locked` | STRING | `"1"` while locked |
| `game_session:<pin>:<q>:closed` | STRING | set when question q's results were shown |
