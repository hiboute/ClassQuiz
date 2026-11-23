<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!--
	A live question on the big screen: headline, countdown disc, answers-in
	counter, and the body for its type (tiles, free text, range, order, word
	cloud). The world comes from the stage around it.
-->
<script lang="ts">
	import { QuizQuestionType, type Question, type RangeQuizAnswer } from '$lib/quiz_types';
	import MediaComponent from '$lib/editor/MediaComponent.svelte';
	import AnswerTile from './AnswerTile.svelte';
	import WordCloud from './WordCloud.svelte';
	import { fitText } from './fit';
	import { isWordCloud, plain, type WordCount } from './worlds';

	interface Props {
		question: Question;
		index: number;
		total: number;
		quizTitle?: string;
		timeLeft: number;
		time: number;
		answerCount: number;
		playerCount: number;
		paused?: boolean;
		words?: WordCount[];
	}

	let {
		question,
		index,
		total,
		quizTitle = '',
		timeLeft,
		time,
		answerCount,
		playerCount,
		paused = false,
		words = []
	}: Props = $props();

	const hasImage = $derived(!!question.image);
	const text = $derived(plain(question.question));
	const type = $derived(question.type ?? QuizQuestionType.ABCD);
	const tiles = $derived(
		type === QuizQuestionType.ABCD ||
			type === QuizQuestionType.VOTING ||
			type === QuizQuestionType.CHECK
			? (question.answers as { answer: string }[])
			: []
	);

	const BODY_TOP = $derived(hasImage ? 540 : 528);
	const BODY_H = $derived(hasImage ? 408 : 420);
	const rows = $derived(Math.max(1, Math.ceil(tiles.length / 2)));
	const tileH = $derived(Math.min(196, Math.floor((BODY_H - (rows - 1) * 28) / rows)));

	const R = 144;
	const C = 2 * Math.PI * R;
	const progress = $derived(time > 0 ? Math.max(0, Math.min(1, timeLeft / time)) : 0);

	// Order items in a fixed shuffled order, so the screen does not give the answer away.
	const orderItems = $derived.by(() => {
		if (type !== QuizQuestionType.ORDER || !Array.isArray(question.answers)) return [];
		const items = (question.answers as { answer: string }[]).map((a) => a.answer);
		let seed = index * 9301 + 49297;
		const rnd = () => ((seed = (seed * 9301 + 49297) % 233280) / 233280);
		for (let i = items.length - 1; i > 0; i--) {
			const j = Math.floor(rnd() * (i + 1));
			[items[i], items[j]] = [items[j], items[i]];
		}
		if (items.length > 1 && items.every((it, i) => it === (question.answers as { answer: string }[])[i].answer)) {
			items.push(items.shift() as string);
		}
		return items;
	});
	const range = $derived(type === QuizQuestionType.RANGE ? (question.answers as RangeQuizAnswer) : null);
</script>

<h1 class="h-title" style="width: 1420px">
	<span class="h-kicker">
		{quizTitle ? `${quizTitle}, ` : ''}question {index + 1} of {total}
	</span>
	<span
		class="h-headline q-headline"
		use:fitText={{ max: hasImage ? 64 : 72, min: 36, lines: hasImage ? 2 : 3, key: text }}
		>{text}</span
	>
</h1>

<div class="q-clock" class:q-clock--paused={paused}>
	<svg viewBox="0 0 316 316" aria-hidden="true">
		<defs>
			<linearGradient id="q-ring" x1="0" y1="0" x2="1" y2="1">
				<stop offset="0" stop-color="#5db5df" />
				<stop offset="1" stop-color="#27be82" />
			</linearGradient>
		</defs>
		<circle cx="158" cy="158" r={R} fill="none" stroke="rgba(254,255,255,0.17)" stroke-width="14" />
		<circle
			cx="158"
			cy="158"
			r={R}
			fill="none"
			stroke="url(#q-ring)"
			stroke-width="14"
			stroke-linecap="round"
			stroke-dasharray={C}
			stroke-dashoffset={C * (1 - progress)}
			transform="rotate(-90 158 158)"
			class="q-ring"
		/>
	</svg>
	<div class="q-clock__num h-num bt-text-aurora">{Math.max(0, timeLeft)}</div>
	<div class="q-clock__label h-label">
		{paused ? 'Paused' : timeLeft <= 0 ? 'Time is up' : 'Seconds'}
	</div>
</div>

<div class="q-count">
	<div class="q-count__num h-num">{answerCount} <small>/ {playerCount}</small></div>
	<div class="q-count__label">Answers in</div>
</div>

{#if hasImage}
	<div class="q-image">
		{#if /^(data:|https?:|\/)/.test(question.image ?? '')}
			<img src={question.image} alt="" class="q-media" />
		{:else}
			<MediaComponent
				src={question.image ?? ''}
				muted={false}
				allow_fullscreen={false}
				css_classes="q-media"
			/>
		{/if}
	</div>
{/if}

<div class="q-body" style="top: {BODY_TOP}px; height: {BODY_H}px">
	{#if tiles.length}
		<div class="q-grid" class:q-grid--one={tiles.length === 1}>
			{#each tiles as answer, i}
				<AnswerTile index={i} text={answer.answer} height={tileH} />
			{/each}
		</div>
		{#if type === QuizQuestionType.CHECK}
			<p class="q-hint">Several answers can be right.</p>
		{/if}
	{:else if isWordCloud(question)}
		<div class="q-cloud">
			{#if words.length}
				<WordCloud {words} width={1780} height={BODY_H} />
			{:else}
				<div class="q-card">
					<span class="h-label">Word cloud</span>
					<span class="q-card__big">Type a word or two on your phone</span>
				</div>
			{/if}
		</div>
	{:else if type === QuizQuestionType.TEXT}
		<div class="q-card">
			<span class="h-label">Free answer</span>
			<span class="q-card__big">Type your answer on your phone</span>
		</div>
	{:else if range}
		<div class="q-card">
			<span class="h-label">Pick a number</span>
			<div class="q-range">
				<span class="h-num q-range__end">{range.min}</span>
				<span class="q-range__track"><span></span></span>
				<span class="h-num q-range__end">{range.max}</span>
			</div>
		</div>
	{:else if orderItems.length}
		<div class="q-order">
			<span class="h-label q-order__label">Put these in the right order</span>
			<div class="q-order__items">
				{#each orderItems as item, i}
					<span class="q-order__item {['bt-tile-a', 'bt-tile-b', 'bt-tile-c', 'bt-tile-d'][i % 4]}"
						>{item}</span
					>
				{/each}
			</div>
		</div>
	{/if}
</div>

<style>
	.q-headline {
		max-height: calc(3 * 1.08em + 4px);
		overflow: hidden;
	}
	.q-clock {
		position: absolute;
		z-index: 3;
		left: 1540px;
		top: 64px;
		width: 316px;
		height: 316px;
		border-radius: 50%;
		background: var(--fill-deep);
	}
	.q-clock svg {
		position: absolute;
		inset: 0;
	}
	.q-ring {
		transition: stroke-dashoffset 1s linear;
	}
	.q-clock__num {
		position: absolute;
		left: 0;
		right: 0;
		top: 84px;
		text-align: center;
		font-size: 168px;
	}
	.q-clock__label {
		position: absolute;
		left: 0;
		right: 0;
		top: 232px;
		text-align: center;
		font-size: 20px;
	}
	.q-clock--paused .q-clock__num {
		opacity: 0.5;
		animation: q-blink 1.4s ease-in-out infinite;
	}
	@keyframes q-blink {
		50% {
			opacity: 0.2;
		}
	}
	.q-count {
		position: absolute;
		z-index: 3;
		left: 1540px;
		top: 404px;
		width: 316px;
		text-align: center;
	}
	.q-count__num {
		font-size: 72px;
	}
	.q-count__num small {
		font-size: 36px;
		font-weight: 400;
	}
	.q-count__label {
		margin-top: 8px;
		font-size: 22px;
		color: var(--ink-muted);
	}
	.q-image {
		position: absolute;
		z-index: 3;
		left: 84px;
		width: 1400px;
		top: 300px;
		height: 214px;
		display: flex;
		justify-content: center;
	}
	.q-image :global(.q-media) {
		height: 214px;
		width: auto;
		max-width: 1400px;
		object-fit: contain;
		border-radius: 18px;
	}
	.q-body {
		position: absolute;
		z-index: 3;
		left: 70px;
		right: 70px;
		display: flex;
		flex-direction: column;
		justify-content: center;
	}
	.q-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 28px;
	}
	.q-grid--one {
		grid-template-columns: 1fr;
	}
	.q-hint {
		margin: 14px 0 0;
		text-align: center;
		font-size: 22px;
		color: var(--ink-muted);
	}
	.q-cloud {
		display: flex;
		justify-content: center;
		height: 100%;
		align-items: center;
	}
	.q-card {
		align-self: center;
		width: 1300px;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 26px;
		padding: 56px 64px;
		border-radius: 25px;
		background: var(--fill-deep);
		text-align: center;
	}
	.q-card__big {
		font-size: 60px;
		font-weight: 900;
		line-height: 1.08;
		text-transform: uppercase;
	}
	.q-range {
		display: flex;
		align-items: center;
		gap: 36px;
		width: 100%;
	}
	.q-range__end {
		font-size: 96px;
	}
	.q-range__track {
		flex: 1;
		height: 18px;
		border-radius: 9999px;
		background: var(--fill-glass-mid);
		position: relative;
	}
	.q-range__track span {
		position: absolute;
		inset: 0;
		border-radius: 9999px;
		background: linear-gradient(90deg, var(--accent-sky) 0%, var(--accent-green) 100%);
		opacity: 0.85;
	}
	.q-order {
		display: flex;
		flex-direction: column;
		gap: 24px;
	}
	.q-order__label {
		font-size: 24px;
	}
	.q-order__items {
		display: flex;
		flex-wrap: wrap;
		gap: 18px;
	}
	.q-order__item {
		height: 96px;
		padding: 0 36px;
		font-size: 40px;
	}
</style>
