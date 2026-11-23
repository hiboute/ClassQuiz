// SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE
//
// SPDX-License-Identifier: MPL-2.0

/**
 * Shared labels and helpers of the quiz editor (sidebar, card, popup).
 */
import {
	QuizQuestionType,
	type Answers,
	type Question,
	type QuestionPoints
} from '$lib/quiz_types';
import { dataSchema } from '$lib/yupSchemas';
import type { Schema } from 'yup';

const questionSchema = (dataSchema.fields.questions as unknown as { innerType: Schema }).innerType;

/** First validation message of one question, or null when it is fine. */
export const questionIssue = (q: Question): string | null => {
	try {
		questionSchema.validateSync(q, { abortEarly: true });
		return null;
	} catch (err) {
		return (err as { errors?: string[] })?.errors?.[0] ?? 'Something is missing';
	}
};

export interface TypeMeta {
	name: string;
	short: string;
	description: string;
}

export const TYPE_META: Record<string, TypeMeta> = {
	[QuizQuestionType.ABCD]: {
		name: 'Multiple choice',
		short: 'Quiz',
		description: 'Up to four answers, one or more of them correct. Players tap a shape.'
	},
	[QuizQuestionType.CHECK]: {
		name: 'Multiple select',
		short: 'Select',
		description: 'Players tick every correct answer, then submit.'
	},
	[QuizQuestionType.WORD_CLOUD]: {
		name: 'Word cloud',
		short: 'Cloud',
		description: 'Players type a short word, the screen shows a live cloud.'
	},
	[QuizQuestionType.VOTING]: {
		name: 'Poll',
		short: 'Poll',
		description: 'Players vote for an option. No correct answer, no points.'
	},
	[QuizQuestionType.ORDER]: {
		name: 'Put in order',
		short: 'Order',
		description: 'Players drag the items into the right order.'
	},
	[QuizQuestionType.TEXT]: {
		name: 'Type answer',
		short: 'Text',
		description: 'Players type the answer. List every spelling you accept.'
	},
	[QuizQuestionType.RANGE]: {
		name: 'Slider',
		short: 'Slider',
		description: 'Players pick a number on a slider. A range of values counts as correct.'
	},
	[QuizQuestionType.SLIDE]: {
		name: 'Slide',
		short: 'Slide',
		description: 'A content slide between questions: text and shapes, no answers.'
	}
};

export const typeMeta = (type: QuizQuestionType | string | undefined): TypeMeta =>
	TYPE_META[String(type ?? QuizQuestionType.ABCD)] ?? TYPE_META[QuizQuestionType.ABCD];

export const TIME_PRESETS = [5, 10, 20, 30, 60, 90, 120] as const;

export const POINTS_OPTIONS: { value: QuestionPoints; label: string; hint: string }[] = [
	{ value: 'standard', label: 'Standard', hint: '1000' },
	{ value: 'double', label: 'Double', hint: '2000' },
	{ value: 'none', label: 'No points', hint: '0' }
];

/** Question types that award points (and so show the points selector). */
export const SCORED_TYPES: readonly string[] = [
	QuizQuestionType.ABCD,
	QuizQuestionType.CHECK,
	QuizQuestionType.ORDER,
	QuizQuestionType.TEXT,
	QuizQuestionType.RANGE
];

export const pointsOf = (q: Question): QuestionPoints =>
	q.points === 'double' || q.points === 'none' ? q.points : 'standard';

/** The answer colours ClassQuiz used to write into every answer. */
export const LEGACY_DEFAULT_COLORS = ['#d6edc9', '#b07156', '#7f7057', '#4e6e58'];

/** True when the author picked a colour of their own (not unset, not a legacy default). */
export const isCustomColor = (color: string | null | undefined): boolean =>
	Boolean(color) && !LEGACY_DEFAULT_COLORS.includes(String(color).toLowerCase());

/** Plain text of the rich question title (for lists and previews). */
export const plainText = (html: string | undefined | null): string => {
	if (!html) return '';
	return html
		.replace(/<[^>]*>/g, ' ')
		.replace(/&nbsp;/g, ' ')
		.replace(/&amp;/g, '&')
		.replace(/&lt;/g, '<')
		.replace(/&gt;/g, '>')
		.replace(/&quot;/g, '"')
		.replace(/&#39;/g, "'")
		.replace(/\s+/g, ' ')
		.trim();
};

/** Look of the little picture of a question type (add popup, type sheet). */
export type TypePreviewKind =
	'tiles' | 'truefalse' | 'check' | 'cloud' | 'poll' | 'order' | 'text' | 'range';

/** One entry of the "add a question" choices. */
export interface QuestionChoice {
	key: string;
	name: string;
	/** long description (desktop popup) */
	description: string;
	/** one short line (phone type sheet) */
	blurb: string;
	type: QuizQuestionType;
	preview: TypePreviewKind;
	answers: () => Answers;
	time?: string;
}

export const QUESTION_CHOICES: QuestionChoice[] = [
	{
		key: 'abcd',
		name: typeMeta(QuizQuestionType.ABCD).name,
		description: typeMeta(QuizQuestionType.ABCD).description,
		blurb: 'Up to 4 answers, one or more correct',
		type: QuizQuestionType.ABCD,
		preview: 'tiles',
		answers: () => [
			{ answer: '', right: true },
			{ answer: '', right: false },
			{ answer: '', right: false },
			{ answer: '', right: false }
		]
	},
	{
		key: 'truefalse',
		name: 'True or false',
		description: 'Two answers, True and False. Quick to write, quick to play.',
		blurb: 'Two answers, quick to write',
		type: QuizQuestionType.ABCD,
		preview: 'truefalse',
		time: '10',
		answers: () => [
			{ answer: 'True', right: true },
			{ answer: 'False', right: false }
		]
	},
	{
		key: 'cloud',
		name: typeMeta(QuizQuestionType.WORD_CLOUD).name,
		description: 'Word cloud: players type a short word, the screen shows a live cloud.',
		blurb: 'Players type a word, live cloud',
		type: QuizQuestionType.WORD_CLOUD,
		preview: 'cloud',
		time: '30',
		answers: () => []
	},
	{
		key: 'check',
		name: typeMeta(QuizQuestionType.CHECK).name,
		description: typeMeta(QuizQuestionType.CHECK).description,
		blurb: 'Players tick every correct answer',
		type: QuizQuestionType.CHECK,
		preview: 'check',
		answers: () => [
			{ answer: '', right: true },
			{ answer: '', right: true },
			{ answer: '', right: false },
			{ answer: '', right: false }
		]
	},
	{
		key: 'poll',
		name: typeMeta(QuizQuestionType.VOTING).name,
		description: typeMeta(QuizQuestionType.VOTING).description,
		blurb: 'A vote, no correct answer, no points',
		type: QuizQuestionType.VOTING,
		preview: 'poll',
		answers: () => [
			{ answer: '', image: undefined },
			{ answer: '', image: undefined }
		]
	},
	{
		key: 'order',
		name: typeMeta(QuizQuestionType.ORDER).name,
		description: typeMeta(QuizQuestionType.ORDER).description,
		blurb: 'Drag the items into order',
		type: QuizQuestionType.ORDER,
		preview: 'order',
		time: '30',
		answers: () => [
			{ answer: '', id: 0 },
			{ answer: '', id: 1 },
			{ answer: '', id: 2 }
		]
	},
	{
		key: 'text',
		name: typeMeta(QuizQuestionType.TEXT).name,
		description: typeMeta(QuizQuestionType.TEXT).description,
		blurb: 'Players type it, list every spelling',
		type: QuizQuestionType.TEXT,
		preview: 'text',
		time: '30',
		answers: () => [{ answer: '', case_sensitive: false }]
	},
	{
		key: 'range',
		name: typeMeta(QuizQuestionType.RANGE).name,
		description: typeMeta(QuizQuestionType.RANGE).description,
		blurb: 'Pick a number, a range counts',
		type: QuizQuestionType.RANGE,
		preview: 'range',
		answers: () => ({
			max: 10,
			min: 0,
			max_correct: 7,
			min_correct: 3
		})
	}
];

/** A new, empty question of the chosen type. */
export const newQuestion = (c: QuestionChoice): Question => ({
	type: c.type,
	time: c.time ?? '20',
	question: '',
	image: undefined,
	answers: c.answers(),
	points: c.type === QuizQuestionType.WORD_CLOUD ? 'none' : 'standard'
});

/** A new content slide (designed in the slide editor). */
export const newSlide = (): Question => ({
	type: QuizQuestionType.SLIDE,
	time: '120',
	question: 'Slide',
	image: undefined,
	answers: ''
});

/** Rough length of a quiz in minutes: each question's time plus 15 s around it. */
export const quizMinutes = (questions: Question[]): number =>
	Math.max(
		1,
		Math.round(
			questions.reduce(
				(s, q) =>
					s +
					(q.type === QuizQuestionType.SLIDE
						? 15
						: (parseInt(String(q.time), 10) || 0) + 15),
				0
			) / 60
		)
	);

/** True when the answers are exactly True and False (the true or false shortcut). */
export const isTrueFalse = (answers: unknown): boolean =>
	Array.isArray(answers) &&
	answers.length === 2 &&
	String(answers[0]?.answer ?? '')
		.trim()
		.toLowerCase() === 'true' &&
	String(answers[1]?.answer ?? '')
		.trim()
		.toLowerCase() === 'false';

/** Key of the QUESTION_CHOICES entry a question matches. */
export const choiceKeyOf = (q: Question | undefined): string | null => {
	switch (q?.type ?? QuizQuestionType.ABCD) {
		case QuizQuestionType.ABCD:
			return isTrueFalse(q?.answers) ? 'truefalse' : 'abcd';
		case QuizQuestionType.CHECK:
			return 'check';
		case QuizQuestionType.VOTING:
			return 'poll';
		case QuizQuestionType.WORD_CLOUD:
			return 'cloud';
		case QuizQuestionType.ORDER:
			return 'order';
		case QuizQuestionType.TEXT:
			return 'text';
		case QuizQuestionType.RANGE:
			return 'range';
		default:
			return null;
	}
};

/** Display name of a question, true or false included. */
export const questionTypeName = (q: Question | undefined): string => {
	const key = choiceKeyOf(q);
	if (key === 'truefalse') return 'True or false';
	return typeMeta(q?.type).name;
};
