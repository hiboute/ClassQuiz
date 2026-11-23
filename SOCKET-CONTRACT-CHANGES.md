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
- Payload: `{game_pin, username, old_sid?, rejoin_token?}`.
- A kicked player who reloads with the old cookie now gets `kick` again,
  instead of rejoining.
- Accepted when `old_sid` is the socket the server holds for this nickname
  (a plain reconnect), or when `rejoin_token` matches the secret the phone got
  in `joined_game` (the server still holds a stale socket of the same phone,
  e.g. a reload that raced a reconnect: the old socket leaves the rooms). A
  second rejoin from the socket that already rejoined is answered again.
- Anything else gets **`rejoin_failed`** (S→C, the sender), never silence:
  `{"reason": "unknown_player" | "stale_session" | "game_not_found" | "invalid",
  "message": "..."}` (English, ready to display). `game_not_found` still comes
  first for a game that is gone. The phone clears its cookie and shows the
  join form with the message.
- `rejoined_game` carries `username` and `rejoin_token` (keep the token).
- If a question is open, the rejoining phone then gets `set_question_number`
  again (see below), plus `game_paused` during a pause.

### `joined_game` / `rejoined_game` (S→C)
- Same player data as before (an object, not a list), plus `username` (as
  stored, trimmed) and `rejoin_token` (32 hex characters). The phone keeps
  the token (cookie `joined_game`) and sends it with `rejoin_game`.

### `kick_player` (C→S, host only)
- Also bans the nickname, case-insensitively, for the rest of the game (Redis
  set, 2 h). It removes the player from the leaderboard and from the
  `players:<pin>` room. The kicked phone gets `kick`, as before.

### `submit_answer` (C→S)
- Answers that arrive after the host showed that question's results get
  `question_not_active`.
- `question_not_active` (S→C, the answering phone) now has a payload:
  `{"question_index": 3, "reason": "closed"}`. `reason` is one of:
  - `closed`: not the current question, or its results were shown;
  - `get_ready`: the get-ready countdown is still running;
  - `paused`: the host paused the timer;
  - `not_open`: no answer window is open.
  It used to have no payload; a listener that takes no argument still works.
- On a `WORD_CLOUD` question, `answer` is the player's free text (see
  "Word cloud" below).
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
- Sent to one phone that joins late or rejoins while the question is open,
  it also carries `remaining` (seconds left, one decimal: start the timer from
  it, not from `question.time`) and, on a rejoin, `already_answered`
  (true: show "answer sent" instead of the answer tiles). It is not re-sent
  once the question's results were shown.
- With the get-ready screen on (the default), it arrives `seconds` after
  `get_ready`, at the moment the answer window opens. Start the phone and host
  timers on this event, as today.

### `set_question_number` (C→S, host): new optional payload
- Still accepted: the question index as a string or number (`"2"`).
- New: `{"question_index": 2, "get_ready_seconds": 0}`. `get_ready_seconds`
  is optional and overrides the game's setting for this question only
  (0 = open at once, no `get_ready`).
- An index out of range now gets `error` (it used to crash the handler).
- Ignored after `end_game_now`.

### `start_game` (C→S, host): new optional payload
- `{"get_ready_seconds": 3}`, optional. Whole seconds, clamped to 0..10;
  0 disables the get-ready screen for the whole game. Without it the game uses
  3. `{}` or no payload works as before.

### `join_game` (C→S): captcha is now really checked
- The captcha check was never awaited, so it always passed. It is now
  awaited. It only applies when the game has `captcha_enabled` **and** the
  phone sends a `captcha` value **and** the server has an hCaptcha or
  reCAPTCHA key. With no key configured (our deploy) it always passes.
- A refused captcha gets **`captcha_invalid`** (S→C, the joining phone):
  `{"message": "The captcha check failed. Try again."}`. It used to end the
  join silently.

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

### `get_ready` (S→C, host + remote + phones, `<pin>` room)
Sent when the host sets a question (`set_question_number`), before the
question itself, unless the delay is 0 or the question is a slide.
```json
{"question_index": 2, "question_count": 10, "title": "Capital of France?",
 "type": "ABCD", "points": "double", "seconds": 3, "image": "/api/v1/storage/..."}
```
- `image` is only present when the question has one. `type` is a
  `QuizQuestionType` value, `points` is `standard | double | none`.
- Show a "Get ready" screen with a `seconds` countdown. Nobody can answer
  yet: `submit_answer` gets `question_not_active` with `reason: "get_ready"`,
  and the scoring clock has not started.
- After `seconds`, the server sends `set_question_number` as usual and starts
  the answer window then, so a fast answer still gets the full points.
- If the host sets another question (or ends the game) during the countdown,
  the old countdown is dropped: only the latest question opens.
- One emit to the `<pin>` room reaches the phones and the host screens (the
  host and remote are in that room too), so it is not sent twice.

### Pause / resume / end now (host only)

#### `pause_game` (C→S, host or remote)
- Payload: none or `{}`. Ignored when it comes from a phone.
- Freezes the timer of the open question. The server stores the remaining
  seconds; answers get `question_not_active` with `reason: "paused"` until
  resume. The box controller buttons are refused too.
- Refused with **`pause_refused`** (S→C, the sender):
  `{"reason": "get_ready" | "no_open_question" | "already_paused"}`.

#### `resume_game` (C→S, host or remote)
- Payload: none or `{}`. Restarts the timer where it stopped: the scoring
  clock does not count the paused time.
- Refused with `pause_refused` `{"reason": "not_paused"}` when not paused.

#### `game_paused` / `game_resumed` (S→C, host + remote + phones, `<pin>` room)
- Payload: `{"question_index": 3, "remaining": 14.6}` (seconds, one decimal).
- `game_paused`: stop the countdown and show "Paused". `game_resumed`:
  restart the countdown from `remaining`. Both carry the same value.
- A phone that joins late during a pause gets `game_paused` right after
  `set_question_number`.
- Showing the results (`get_question_results`) or setting another question
  clears a pause; no `game_resumed` is sent then.

#### `end_game_now` (C→S, host or remote)
- Payload: none or `{}`. Ends the game at once, from any state (lobby,
  get-ready, open question, results): cancels a running countdown, closes the
  current question (later answers get `question_not_active`), then sends, in
  order: `game_ended`, `final_results`, `podium` (same payloads as
  `get_final_results`). Later `set_question_number` calls are ignored.
- Answers already given count; the open question's results are not shown.

#### `game_ended` (S→C, host + remote + phones, `<pin>` room)
- Payload: `{"reason": "host"}`. Sent only by `end_game_now`, just before
  `final_results` and `podium`.

### Word cloud

New question type **`WORD_CLOUD`** (`QuizQuestionType`). Editor payload:
```json
{"question": "One word for Monday?", "time": "30", "type": "WORD_CLOUD",
 "answers": [], "image": null, "points": "none"}
```
- `answers` is ignored and stored as `[]` (`""` or `null` are accepted too).
- `points` is ignored: a word cloud never awards points and never changes a
  streak. It is not a Postgres enum (questions are stored as JSON), so **no
  migration**.
- Phones get `set_question_number` with `question.type: "WORD_CLOUD"` and
  `question.answers: []`: show a text field (max 30 characters).

#### Submitting (C→S, phone): `submit_answer`
- `{"question_index": 4, "answer": "Pizza"}`. Same event as the other types.
- The text is trimmed and inner whitespace collapsed, then must be 1 to 30
  characters, without control characters, and pass the profanity filter
  (same list as nicknames).
- One accepted word per player per question; a second one gets
  `already_replied`. A refused word does not count: the player can try again.
- Counts as an answer for `player_answer` and `everyone_answered`.

#### `word_cloud_accepted` (S→C, the submitting phone)
- `{"question_index": 4, "text": "Pizza"}`: the cleaned text as stored. This is
  the phone's only "result": show "Sent!".

#### `word_cloud_refused` (S→C, the submitting phone)
```json
{"question_index": 4, "code": "too_long",
 "message": "Your answer must be at most 30 characters.", "max_length": 30}
```
- `code`: `empty`, `too_long`, `invalid_characters`, `profanity` or
  `invalid_type`. `message` is English, ready to display.

#### `word_cloud_update` (S→C, host + remote, `admin:<pin>`)
```json
{"question_index": 4, "total": 57,
 "words": [{"text": "Pizza", "count": 12}, {"text": "Coffee", "count": 9}]}
```
- `words`: at most 60, most frequent first (ties alphabetical). Words are
  counted case-insensitively with whitespace collapsed ("pizza", " PIZZA "
  count as one); `text` is the spelling of the first player who sent it.
- `total`: number of accepted submissions.
- Live while players answer, **at most 2 per second** per question across all
  workers: the first word of a 500 ms window is sent at once, later words of
  the window in one update at its end, so the last word is never missed.
- Sent once more, not throttled, with the final state when the host emits
  `get_question_results` for the question (before `question_results`).

#### Results
- `question_results` (host) lists the submissions as `AnswerData` with
  `answer` = the text, `right: false`, `score: 0`. Phones get their own entry
  as for other types, and `rank_update` with `gained: 0` and an unchanged
  streak. The phone can ignore both and keep its "Sent!" screen.

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
| `game:<pin>:question_token` | STRING | random token, changed on each `set_question_number` and on `end_game_now` (cancels a stale countdown) |
| `game:<pin>:get_ready` | STRING | index of the question in its get-ready countdown |
| `game:<pin>:paused` | STRING | JSON `{question_index, remaining}` while paused |
| `game:<pin>:ended` | STRING | `"1"` after `end_game_now` |
| `game_session:<pin>:<q>:wc_counts` | ZSET | word key (casefolded) → count |
| `game_session:<pin>:<q>:wc_display` | HASH | word key → first spelling |
| `game_session:<pin>:<q>:wc_total` | STRING | accepted submissions |
| `game_session:<pin>:<q>:wc_throttle` / `wc_trailing` | STRING | rate limit of `word_cloud_update` (expire in 0.5 s / 10 s) |

`game:<pin>:current_time` (the question start used for scoring) is now
removed when a get-ready countdown starts and set when the answer window
opens; a resume moves it forward by the paused time.

`PlayGame` (the `game:<pin>` JSON) has a new field `get_ready_seconds`
(default 3), so `registered_as_admin` and `joined_game` carry it too.
