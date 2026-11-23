<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!--
	Phone answer screen, in the question's colour world: question number and
	countdown ring on top, the question small, then the input for its type
	filling the rest of the screen. Once answered it turns into the
	"Answer locked in" state. The parent owns the timer (pause and resume come
	from the host) and sends the answer.
-->
<script lang="ts">
	import { onDestroy } from 'svelte';
	import type { ReturnQuestion } from '$lib/quiz_types';
	import CircularTimer from '$lib/play/circular_progress.svelte';
	import ShapeMark from '$lib/brand/ShapeMark.svelte';
	import { answerStyle } from '$lib/brand/answers';
	import PhoneShell from '$lib/play/phone/PhoneShell.svelte';
	import Choice from '$lib/play/questions/choice.svelte';
	import Check from '$lib/play/questions/check.svelte';
	import TextAnswer from '$lib/play/questions/text.svelte';
	import RangeAnswer from '$lib/play/questions/range.svelte';
	import OrderAnswer from '$lib/play/questions/order.svelte';
	import {
		formatPoints,
		isShapesMode,
		plainText,
		questionWorld,
		type AnswerPayload,
		type LockedAnswer
	} from '$lib/play/phone/phone';

	interface Props {
		question: ReturnQuestion;
		question_index: number | string;
		question_count?: number;
		game_mode?: any;
		username?: string;
		total_score?: number | null;
		/** Date.now() value at which the time runs out */
		deadline: number;
		paused?: boolean;
		/** seconds left while paused */
		paused_remaining?: number | null;
		/** the host closed the question (everyone answered, solutions shown) */
		time_up?: boolean;
		locked?: LockedAnswer | null;
		/** refusal message for a free-text answer (word cloud): the player may retry */
		answer_error?: string;
		onanswer: (payload: AnswerPayload, locked: LockedAnswer) => void;
	}

	let {
		question,
		question_index,
		question_count,
		game_mode,
		username = '',
		total_score = null,
		deadline,
		paused = false,
		paused_remaining = null,
		time_up = false,
		locked = null,
		answer_error = '',
		onanswer
	}: Props = $props();

	const index = $derived(Number(question_index) || 0);
	const type = $derived(String(question.type ?? 'ABCD').toUpperCase());
	const world = $derived(questionWorld(index));
	const shapes = $derived(isShapesMode(game_mode));
	const text = $derived(plainText(question.question));
	const total = $derived(Math.max(1, Number(question.time) || 1));

	// shorter phones (360x740 and below) get a smaller ring
	let vh = $state(844);
	const ring_size = $derived(vh < 760 ? 76 : 92);

	let now = $state(Date.now());
	const tick = setInterval(() => (now = Date.now()), 250);
	onDestroy(() => clearInterval(tick));

	const exact_left = $derived(
		paused && paused_remaining !== null && paused_remaining !== undefined
			? Math.max(0, Number(paused_remaining))
			: Math.max(0, (deadline - now) / 1000)
	);
	const seconds_left = $derived(Math.ceil(exact_left));
	const progress = $derived(1 - exact_left / total);
	const over = $derived(time_up || (!paused && seconds_left <= 0));

	// Only one answer per question, whatever the number of taps
	let sending = false;
	// a refused word cloud entry unlocks the field again
	$effect(() => {
		if (!locked) sending = false;
	});
	const send = (payload: Omit<AnswerPayload, 'question_index'>, lock: LockedAnswer) => {
		if (sending || locked) return;
		sending = true;
		onanswer({ question_index: index, ...payload }, lock);
	};

	const answers = $derived(Array.isArray(question.answers) ? (question.answers as any[]) : []);
	const range = $derived(
		!Array.isArray(question.answers) && question.answers
			? (question.answers as { min: number; max: number })
			: { min: 0, max: 100 }
	);
	let last_text = $state('');
	let range_value = $state(0);
	let range_init = false;
	$effect(() => {
		if (type === 'RANGE' && !range_init) {
			range_init = true;
			const lo = Number(range.min) || 0;
			const hi = Number(range.max) || 0;
			range_value = Math.round((hi - lo) / 2 + lo);
		}
	});
	// RANGE: when time runs out, the current slider value counts
	$effect(() => {
		if (type === 'RANGE' && over && !locked && !time_up) {
			send({ answer: String(range_value) }, { label: String(range_value) });
		}
	});

	const locked_title = $derived(
		type === 'VOTING'
			? 'Vote counted'
			: type === 'WORD_CLOUD'
				? locked?.pending
					? 'Sending'
					: 'Sent'
				: 'Locked in'
	);
</script>

<svelte:window bind:innerHeight={vh} />

<PhoneShell {world} state={locked ? 'locked' : over ? 'time-up' : 'question'}>
	<div class="pa-top">
		<div class="pa-q">
			<span class="bt-eyebrow pa-eyebrow"
				>Question{#if question.points === 'double'}<span class="pa-double">Double points</span
					>{/if}</span
			>
			<b class="bt-num"
				>{index + 1}{#if question_count}<span class="pa-of">&nbsp;/ {question_count}</span>{/if}</b
			>
		</div>
		{#if type !== 'SLIDE'}
			<CircularTimer text={String(seconds_left)} {progress} size={ring_size} />
		{/if}
	</div>

	{#if text}
		<p class="pa-text" class:pa-text-long={text.length > 110}>{text}</p>
	{/if}

	{#if locked}
		<div class="pl-locked" data-testid="answer-locked" aria-live="polite">
			{#if locked.index !== undefined && (type === 'ABCD' || type === 'VOTING')}
				{@const st = answerStyle(locked.index)}
				<span class="pl-chip {st.className}">
					<ShapeMark index={locked.index} size={44} />
				</span>
			{/if}
			<span class="bt-kicker pl-kicker">Answer</span>
			<span class="bt-headline pl-headline">{locked_title}</span>
			{#if locked.label}
				<p class="pl-choice">{locked.label}</p>
			{/if}
			<p class="pl-wait">
				{over ? 'Results on the big screen in a moment.' : 'Waiting for the others.'}
			</p>
		</div>
	{:else if type === 'SLIDE'}
		<div class="pl-locked" data-testid="slide-screen">
			<span class="bt-kicker pl-kicker">Look at</span>
			<span class="bt-headline pl-headline">the big screen</span>
			<p class="pl-wait">Nothing to answer on this one.</p>
		</div>
	{:else if over}
		<div class="pl-locked" data-testid="time-up">
			<span class="bt-kicker pl-kicker">Time is up</span>
			<span class="bt-headline pl-headline">No answer</span>
			<p class="pl-wait">Results on the big screen. Get ready for the next one.</p>
		</div>
	{:else if type === 'ABCD' || type === 'VOTING'}
		<div class="pa-body">
			<Choice
				{answers}
				{shapes}
				disabled={Boolean(locked)}
				onpick={(answer, i) =>
					send({ answer }, { label: shapes ? answerStyle(i).label : answer, index: i })}
			/>
		</div>
	{:else if type === 'CHECK'}
		<div class="pa-body">
			<Check
				{answers}
				{shapes}
				disabled={Boolean(locked)}
				onsubmit={(answer, label) => send({ answer }, { label })}
			/>
		</div>
	{:else if type === 'TEXT' || type === 'WORD_CLOUD'}
		<TextAnswer
			error={answer_error}
			mode={type === 'WORD_CLOUD' ? 'word_cloud' : 'text'}
			disabled={Boolean(locked)}
			initial={last_text}
			onsubmit={(answer) => {
				last_text = answer;
				send({ answer }, { label: answer });
			}}
		/>
	{:else if type === 'RANGE'}
		<RangeAnswer
			min={range.min}
			max={range.max}
			bind:value={range_value}
			disabled={Boolean(locked)}
			onsubmit={(answer) => send({ answer }, { label: answer })}
		/>
	{:else if type === 'ORDER'}
		<OrderAnswer
			{answers}
			disabled={Boolean(locked)}
			onsubmit={(ordered, label) => send({ answer: 'a', complex_answer: ordered }, { label })}
		/>
	{/if}

	<div class="pa-foot">
		<b>{username}</b>
		{#if total_score !== null && total_score !== undefined}
			<span><span class="pa-tnum">{formatPoints(total_score)}</span> points</span>
		{/if}
	</div>
</PhoneShell>

<style>
	.pa-top {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 12px;
		min-height: 92px;
	}
	.pa-q b {
		display: block;
		margin-top: 4px;
		font-size: 44px;
		line-height: 0.9;
	}
	.pa-eyebrow {
		font-size: 15px;
	}
	.pa-double {
		display: inline-block;
		margin-left: 10px;
		padding: 3px 10px;
		border-radius: 9999px;
		background: var(--fill-deep);
		color: var(--accent-green-tint);
		font-size: 11px;
		letter-spacing: 2px;
		vertical-align: 1px;
	}
	.pa-of {
		font-weight: 400;
		font-size: 26px;
	}
	.pa-text {
		margin: 18px 0 0;
		font-size: 21px;
		font-weight: 700;
		line-height: 1.2;
		overflow-wrap: anywhere;
		display: -webkit-box;
		-webkit-line-clamp: 4;
		line-clamp: 4;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
	.pa-text-long {
		font-size: 17px;
	}
	.pa-body {
		flex: 1 1 auto;
		display: flex;
		flex-direction: column;
		min-height: 0;
		margin-top: 20px;
	}
	.pa-foot {
		margin-top: 16px;
		display: flex;
		justify-content: space-between;
		gap: 12px;
		font-size: 15px;
		color: var(--ink-muted);
	}
	.pa-foot b {
		color: var(--ink);
		font-weight: 700;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	.pa-foot > span {
		flex: none;
	}
	.pa-tnum {
		font-variant-numeric: tabular-nums;
	}

	/* locked in, time up, slide */
	.pl-locked {
		margin: auto 0;
		padding: 32px 0;
	}
	.pl-chip {
		width: 88px;
		height: 88px;
		justify-content: center;
		margin-bottom: 28px;
		animation: pl-in 380ms cubic-bezier(0.2, 0.8, 0.2, 1) both;
	}
	@keyframes pl-in {
		from {
			transform: scale(0.7);
			opacity: 0;
		}
	}
	@media (prefers-reduced-motion: reduce) {
		.pl-chip {
			animation: none;
		}
	}
	.pl-kicker {
		font-size: 20px;
	}
	.pl-headline {
		font-size: 44px;
		margin-top: 4px;
	}
	.pl-choice {
		margin: 16px 0 0;
		font-size: 22px;
		font-weight: 700;
		overflow-wrap: anywhere;
	}
	@media (max-height: 760px) {
		.pa-top {
			min-height: 76px;
		}
		.pa-q b {
			font-size: 38px;
		}
		.pa-text {
			margin-top: 12px;
			font-size: 17px;
			-webkit-line-clamp: 3;
			line-clamp: 3;
		}
		.pa-body {
			margin-top: 14px;
		}
		.pa-foot {
			margin-top: 10px;
		}
	}
	.pl-wait {
		margin: 14px 0 0;
		font-size: 17px;
		color: var(--ink-muted);
	}
</style>
