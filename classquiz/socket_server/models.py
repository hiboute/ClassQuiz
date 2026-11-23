# SPDX-FileCopyrightText: 2025 Marlon W (Mawoka)
#
# SPDX-License-Identifier: MPL-2.0

from pydantic import BaseModel, field_validator, ValidationInfo
from classquiz.db.models import QuizQuestion, QuizQuestionType, VotingQuizAnswer
from classquiz.helpers.nickname import clean_nickname


class JoinGameData(BaseModel):
    username: str
    game_pin: str
    captcha: str | None = None
    custom_field: str | None = None

    @field_validator("username", mode="before")
    @classmethod
    def valid_nickname(cls, v: object) -> str:
        # Trims, checks length (2-20), allowed characters and the profanity
        # list. Raises NicknameError (a ValueError) with a stable `code`; the
        # join_game handler turns it into a `username_invalid` event.
        return clean_nickname(v)


class RejoinGameData(BaseModel):
    old_sid: str | None = None
    game_pin: str
    username: str
    # Secret sent in joined_game / rejoined_game; lets a phone take its
    # nickname back when the server still holds a stale socket for it.
    rejoin_token: str | None = None


class RegisterAsAdminData(BaseModel):
    game_pin: str
    game_id: str


class ABCDQuizAnswerWithoutSolution(BaseModel):
    answer: str
    color: str | None = None


class RangeQuizAnswerWithoutSolution(BaseModel):
    min: int
    max: int


class ReturnQuestion(QuizQuestion):
    answers: list[ABCDQuizAnswerWithoutSolution] | RangeQuizAnswerWithoutSolution | list[VotingQuizAnswer]
    type: QuizQuestionType = QuizQuestionType.ABCD

    @field_validator("answers")
    def answers_not_none_if_abcd_type(cls, v, info: ValidationInfo):
        if info.data["type"] == QuizQuestionType.ABCD and type(v[0]) is not ABCDQuizAnswerWithoutSolution:
            raise ValueError("Answers can't be none if type is ABCD")
        if info.data["type"] == QuizQuestionType.RANGE and type(v) is not RangeQuizAnswerWithoutSolution:
            raise ValueError("Answer must be from type RangeQuizAnswer if type is RANGE")
        # skipcq: PTC-W0047
        if info.data["type"] == QuizQuestionType.VOTING and type(v[0]) is not VotingQuizAnswer:
            pass
        return v


class SubmitAnswerDataOrderType(BaseModel):
    answer: str


class SubmitAnswerData(BaseModel):
    question_index: int
    answer: str | int
    complex_answer: list[SubmitAnswerDataOrderType] | None = None


class KickPlayerInput(BaseModel):
    username: str


class UsernameInvalidEvent(BaseModel):
    """Payload of `username_invalid`, sent to a player whose nickname was refused."""

    code: str  # too_short | too_long | invalid_characters | profanity | invalid_type
    message: str  # English, ready to display
    min_length: int = 2
    max_length: int = 20


class RankUpdateEvent(BaseModel):
    """Payload of `rank_update`, sent to each player after a question's results."""

    question_index: int
    rank: int
    total_players: int
    total: int
    gained: int
    streak: int
    behind_username: str | None = None
    behind_gap: int | None = None


class ConnectSessionIdEvent(BaseModel):
    session_id: str
