// SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE
//
// SPDX-License-Identifier: MPL-2.0

/**
 * Shared labels and helpers of the quiz editor (sidebar, card, popup).
 */
import { QuizQuestionType, type Question, type QuestionPoints } from '$lib/quiz_types';
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
