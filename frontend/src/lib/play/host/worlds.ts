// SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE
//
// SPDX-License-Identifier: MPL-2.0

import { WORLDS, type World } from '$lib/brand/answers';
import { QuizQuestionType, type Question } from '$lib/quiz_types';

/** Each question gets its own colour world, cycling through the six. */
export const worldFor = (index: number): World => WORLDS[((index % 6) + 6) % 6];

/** Question types that award points (and so move the leaderboard). */
export const isGraded = (q: Question | undefined): boolean =>
	!!q &&
	q.type !== QuizQuestionType.VOTING &&
	q.type !== QuizQuestionType.SLIDE &&
	(q.type as string) !== 'WORD_CLOUD' &&
	(q as Question & { points?: string }).points !== 'none';

export const isWordCloud = (q: Question | undefined): boolean =>
	(q?.type as string | undefined) === 'WORD_CLOUD';

/** Thin space thousands separator, like the mockups ("7 480"). */
export const fmt = (n: number | null | undefined): string =>
	Math.round(n ?? 0)
		.toString()
		.replace(/\B(?=(\d{3})+(?!\d))/g, ' ');

/** Plain text of a question that may hold editor HTML. */
export const plain = (html: string | undefined): string => {
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

export const TYPE_LABEL: Record<string, string> = {
	ABCD: 'Quiz',
	CHECK: 'Several answers',
	VOTING: 'Poll',
	TEXT: 'Type the answer',
	RANGE: 'Pick a number',
	ORDER: 'Put in order',
	SLIDE: 'Slide',
	WORD_CLOUD: 'Word cloud'
};

export interface LeaderEntry {
	username: string;
	score: number;
	gained?: number;
}
export interface LeaderboardData {
	question_index: number;
	total_players: number;
	top: LeaderEntry[];
}
export interface PodiumEntry {
	rank: number;
	username: string;
	score: number;
}
export interface PodiumData {
	top: PodiumEntry[];
	total_players: number;
}
export interface WordCount {
	text: string;
	count: number;
}
export interface ResultEntry {
	username: string;
	answer: string;
	right: boolean;
	time_taken: number;
	score: number;
	streak?: number;
}
export interface GetReadyData {
	question_index: number;
	question_count?: number;
	title: string;
	type: string;
	points?: string;
	seconds: number;
	image?: string | null;
}

/** Word counts from raw answers (fallback when no word_cloud_update came). */
export const countWords = (results: ResultEntry[] | null | undefined): WordCount[] => {
	const map = new Map<string, WordCount>();
	for (const r of results ?? []) {
		const text = String(r.answer ?? '').trim().replace(/\s+/g, ' ');
		if (!text) continue;
		const key = text.toLocaleLowerCase();
		const cur = map.get(key);
		if (cur) cur.count += 1;
		else map.set(key, { text, count: 1 });
	}
	return [...map.values()].sort((a, b) => b.count - a.count);
};
