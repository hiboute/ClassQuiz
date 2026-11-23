// SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE
//
// SPDX-License-Identifier: MPL-2.0

/* Helpers shared by the player phone screens. */

/** Colour world of each question, by index: one list for host, phone and remote. */
export { QUESTION_WORLDS, questionWorld } from '$lib/brand/answers';

/** Nickname rules of the server: trimmed, inner whitespace collapsed, 2 to 20 chars. */
export const NICKNAME_MIN = 2;
export const NICKNAME_MAX = 20;

export function cleanNickname(raw: string): string {
	return (raw ?? '').trim().replace(/\s+/g, ' ');
}

/** Same character rules as the server, so most mistakes show before a round trip. */
export function nicknameProblem(raw: string): string | null {
	const name = cleanNickname(raw);
	if (name.length === 0) return null;
	if (name.length < NICKNAME_MIN) return `At least ${NICKNAME_MIN} characters.`;
	if (name.length > NICKNAME_MAX) return `At most ${NICKNAME_MAX} characters.`;
	if (!/^[\p{L}\p{M}\p{N} _.\-'’]+$/u.test(name)) {
		return "Letters, digits, spaces and - _ . ' only.";
	}
	if (!/[\p{L}\p{N}]/u.test(name)) return 'Use at least one letter or digit.';
	return null;
}

/** 6960 -> "6 960" (thin grouping like the mockups, tabular digits do the rest). */
export function formatPoints(n: number | null | undefined): string {
	const v = Math.round(Number(n) || 0);
	const sign = v < 0 ? '-' : '';
	return sign + String(Math.abs(v)).replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
}

/** 1 -> "ST", 2 -> "ND", 12 -> "TH" */
export function ordinalSuffix(n: number): string {
	const v = Math.abs(Math.floor(n));
	const t = v % 100;
	if (t >= 11 && t <= 13) return 'TH';
	switch (v % 10) {
		case 1:
			return 'ST';
		case 2:
			return 'ND';
		case 3:
			return 'RD';
		default:
			return 'TH';
	}
}

export function ordinal(n: number): string {
	return `${n}${ordinalSuffix(n).toLowerCase()}`;
}

/** Short vibration where supported (Android Chrome); silently nothing elsewhere. */
export function haptic(pattern: number | number[] = 25): void {
	try {
		if (typeof navigator !== 'undefined' && typeof navigator.vibrate === 'function') {
			navigator.vibrate(pattern);
		}
	} catch {
		/* not supported */
	}
}

/** The legacy game_mode value for "answer shapes only on phones" is renamed "shapes" here. */
export function isShapesMode(mode: unknown): boolean {
	return mode === 'shapes' || mode === 'kahoot';
}

/** Strip HTML from rich-text question titles for compact phone display. */
export function plainText(html: string | undefined | null): string {
	if (!html) return '';
	return String(html)
		.replace(/<br\s*\/?>/gi, ' ')
		.replace(/<[^>]*>/g, '')
		.replace(/&nbsp;/g, ' ')
		.replace(/&amp;/g, '&')
		.replace(/&lt;/g, '<')
		.replace(/&gt;/g, '>')
		.replace(/&quot;/g, '"')
		.replace(/&#39;/g, "'")
		.replace(/\s+/g, ' ')
		.trim();
}

export interface RankUpdate {
	question_index: number;
	rank: number;
	total_players: number;
	total: number;
	gained: number;
	streak: number;
	behind_username: string | null;
	behind_gap: number | null;
}

export interface PodiumEntry {
	rank: number;
	username: string;
	score: number;
}

export interface PodiumData {
	top: PodiumEntry[];
	total_players: number;
	rank: number | null;
	total: number | null;
}

export interface OwnResult {
	username: string;
	answer: string;
	right: boolean;
	time_taken: number;
	score: number;
	streak?: number;
	streak_bonus?: number;
}

export interface GetReadyData {
	question_index: number;
	title: string;
	type: string;
	points?: string;
	seconds: number;
	image?: string | null;
	question_count?: number;
}

export interface AnswerPayload {
	question_index: number;
	answer: string;
	complex_answer?: Array<{ answer: string }>;
}

export interface LockedAnswer {
	label: string;
	index?: number;
	/** sent, waiting for the server to accept it (word cloud) */
	pending?: boolean;
}
