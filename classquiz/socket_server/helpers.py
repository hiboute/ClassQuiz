# SPDX-FileCopyrightText: 2025 Marlon W (Mawoka)
#
# SPDX-License-Identifier: MPL-2.0
import asyncio
import re
import unicodedata

import aiohttp
from classquiz.config import settings, redis
from classquiz.db.models import (
    PlayGame,
    QuizQuestionType,
    TextQuizAnswer,
    ABCDQuizAnswer,
    VotingQuizAnswer,
    RangeQuizAnswer,
)
from classquiz.helpers.profanity import contains_profanity
from classquiz.socket_server.models import SubmitAnswerData
from .models import SubmitAnswerDataOrderType


async def check_captcha(captcha_data: str) -> bool:
    """Verify a captcha token with hCaptcha or reCAPTCHA.

    Returns True when no captcha key is configured (captcha off), False when
    the provider refuses the token or cannot be reached.
    """
    conf = settings()
    if conf.hcaptcha_key is not None:
        url, secret = "https://hcaptcha.com/siteverify", conf.hcaptcha_key
    elif conf.recaptcha_key is not None:
        url, secret = "https://www.google.com/recaptcha/api/siteverify", conf.recaptcha_key
    else:
        return True
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.post(url, data={"response": captcha_data, "secret": secret}) as resp:
                resp_data = await resp.json(content_type=None)
    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError):
        return False
    return isinstance(resp_data, dict) and resp_data.get("success") is True


def check_answer(game_data: PlayGame, data: SubmitAnswerData) -> (bool, str):
    q_i = int(float(data.question_index))
    q_type = game_data.questions[q_i].type
    q_answers = game_data.questions[q_i].answers
    q_answer = data.answer
    if q_type == QuizQuestionType.ABCD:
        return (check_abcd_question(q_answer, q_answers), data.answer)
    elif q_type == QuizQuestionType.RANGE:
        return (
            check_range_question(q_answer, q_answers),
            q_answer,
        )
    elif q_type == QuizQuestionType.VOTING:
        return (False, q_answer)
    elif q_type == QuizQuestionType.ORDER:
        return check_order_question(data.complex_answer, q_answer, q_answers)
    elif q_type == QuizQuestionType.TEXT:
        return (
            check_text_question(q_answer, q_answers),
            q_answer,
        )

    elif q_type == QuizQuestionType.CHECK:
        return (
            check_check_question(q_answer, q_answers),
            q_answer,
        )
    else:
        return (False, q_answer)
    return (False, q_answer)


def check_abcd_question(answer: str, answers: ABCDQuizAnswer) -> bool:
    for a in answers:
        if a.answer == answer and a.right:
            return True
    return False


def check_range_question(answer: str, answers: RangeQuizAnswer) -> bool:
    if answers.min_correct <= int(float(answer)) <= answers.max_correct:
        return answers.min_correct <= int(float(answer)) <= answers.max_correct


def check_order_question(
    complex_answer: list[SubmitAnswerDataOrderType] | None,
    answer: str,
    answers: list[VotingQuizAnswer],
) -> (bool, str):
    if complex_answer is None:
        return (False, answer)
    correct_answers = [{"answer": a.answer} for a in answers]
    submitted_answers = [{"answer": a.answer} for a in complex_answer]
    answer_str = ", ".join(a["answer"] for a in submitted_answers)
    is_correct = submitted_answers == correct_answers
    return is_correct, answer_str


def check_text_question(answer: str, answers: list[TextQuizAnswer]) -> bool:
    for q in answers:
        if q.case_sensitive:
            if answer == q.answer:
                return True
        else:
            if answer.lower() == q.answer.lower():
                return True
    return False


def check_check_question(answer: str, answers: list[ABCDQuizAnswer]) -> bool:
    correct_string = ""
    for i, a in enumerate(answers):
        if a.right:
            correct_string += str(i)
    return bool(correct_string == answer)


ANSWER_KEY_TTL = 7200


def answered_key(game_pin: str, q_index: int) -> str:
    return f"game_session:{game_pin}:{q_index}:answered"


async def mark_answered(game_pin: str, q_index: int, username: str) -> bool:
    """Atomically record that `username` answered; False if they already had.

    One SADD on a per-question set replaces reading and parsing every answer
    of the question (O(players) per submit, O(players^2) per question).
    """
    key = answered_key(game_pin, q_index)
    added = await redis.sadd(key, username)
    await redis.expire(key, ANSWER_KEY_TTL)
    return added == 1


async def has_already_answered(game_pin: str, q_index: int, username: str) -> bool:
    """Read-only check, kept for callers that only need to know."""
    return bool(await redis.sismember(answered_key(game_pin, q_index), username))


WORD_CLOUD_MIN_LENGTH = 1
WORD_CLOUD_MAX_LENGTH = 30


class WordCloudError(ValueError):
    """A word cloud submission was refused; `code` is stable for the client."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def clean_word(value: object) -> tuple[str, str]:
    """Return (display form, counting key) of a word cloud submission.

    The display form is trimmed with inner whitespace collapsed; the key is
    also casefolded, so "Paris", " paris " and "PARIS" count as one word.
    Raises WordCloudError: empty, too_long, invalid_characters, profanity.
    """
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise WordCloudError("invalid_type", "Send your answer as text.")
    text = unicodedata.normalize("NFC", str(value))
    if any(unicodedata.category(c) in ("Cc", "Cf", "Co", "Cs") and not c.isspace() for c in text):
        raise WordCloudError("invalid_characters", "Your answer contains characters that are not allowed.")
    display = re.sub(r"\s+", " ", text).strip()
    if len(display) < WORD_CLOUD_MIN_LENGTH:
        raise WordCloudError("empty", "Type a word before sending.")
    if len(display) > WORD_CLOUD_MAX_LENGTH:
        raise WordCloudError("too_long", f"Your answer must be at most {WORD_CLOUD_MAX_LENGTH} characters.")
    if contains_profanity(display):
        raise WordCloudError("profanity", "This word is not allowed.")
    return display, display.casefold()
