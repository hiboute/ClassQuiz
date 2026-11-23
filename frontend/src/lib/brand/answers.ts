// SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE
//
// SPDX-License-Identifier: MPL-2.0

/**
 * The four answer options of the live quiz. Each one differs by colour,
 * lightness and shape mark, so players tell them apart at a glance without
 * relying on hue. Index 0..3 maps to A..D; use answerStyle(i) for any index
 * (it wraps around for questions with more than four options).
 */

export type AnswerShape = 'triangle' | 'diamond' | 'circle' | 'square';

export interface AnswerStyle {
	key: 'a' | 'b' | 'c' | 'd';
	shape: AnswerShape;
	/** gradient start and end colours */
	from: string;
	to: string;
	/** full CSS gradient, same as var(--answer-x) in app.css */
	gradient: string;
	/** text and mark ink on the tile */
	text: string;
	/** global class that paints the tile (see app.css) */
	className: string;
	/** accessible name of the shape */
	label: string;
}

export const ANSWERS: readonly AnswerStyle[] = [
	{
		key: 'a',
		shape: 'triangle',
		from: '#f982fa',
		to: '#d783ff',
		gradient: 'linear-gradient(120deg, #f982fa 0%, #d783ff 100%)',
		text: '#000000',
		className: 'bt-tile-a',
		label: 'Triangle'
	},
	{
		key: 'b',
		shape: 'diamond',
		from: '#692aac',
		to: '#664bdc',
		gradient: 'linear-gradient(120deg, #692aac 0%, #664bdc 100%)',
		text: '#feffff',
		className: 'bt-tile-b',
		label: 'Diamond'
	},
	{
		key: 'c',
		shape: 'circle',
		from: '#27be82',
		to: '#5db5df',
		gradient: 'linear-gradient(120deg, #27be82 0%, #5db5df 100%)',
		text: '#000000',
		className: 'bt-tile-c',
		label: 'Circle'
	},
	{
		key: 'd',
		shape: 'square',
		from: '#0d458a',
		to: '#418eed',
		gradient: 'linear-gradient(100deg, #0d458a 0%, #2a6abb 62%, #418eed 100%)',
		text: '#feffff',
		className: 'bt-tile-d',
		label: 'Square'
	}
] as const;

export const ANSWER_SHAPES: readonly AnswerShape[] = ANSWERS.map((a) => a.shape);

/** Style of the answer at index i (wraps around after four). */
export function answerStyle(i: number): AnswerStyle {
	const n = ANSWERS.length;
	return ANSWERS[((i % n) + n) % n];
}

/** The six colour worlds of the system. */
export type World = 'indigo' | 'teal' | 'violet' | 'midnight' | 'cobalt' | 'ultraviolet';
export const WORLDS: readonly World[] = [
	'indigo',
	'teal',
	'violet',
	'midnight',
	'cobalt',
	'ultraviolet'
];

/** Photographic grounds shipped in static/brand/grounds (WebP, 1920x1080). */
export const GROUNDS = {
	cover: '/brand/grounds/core-cover-mosaic.webp',
	indigoPortrait: '/brand/grounds/indigo-portrait-right-hair.webp',
	violetWave: '/brand/grounds/violet-plain-wave.webp',
	midnightGlow: '/brand/grounds/midnight-plain-glow.webp',
	cobaltDeep: '/brand/grounds/cobalt-plain-deep.webp',
	ultravioletPortrait: '/brand/grounds/ultraviolet-portrait-neon.webp'
} as const;

export const APP_NAME = 'India Tech Hub Live Quiz';
export const APP_NAME_SHORT = 'Live Quiz';
