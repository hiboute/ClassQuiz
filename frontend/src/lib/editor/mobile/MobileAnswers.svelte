<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!--
	Phone answer list for multiple choice, multiple select and polls: one
	brand tile per answer, a 44px correct toggle on the right (not for polls).
	An empty answer shows a remove button while more than two are left.
-->
<script lang="ts">
	import type { Answer, Question } from '$lib/quiz_types';
	import { QuizQuestionType } from '$lib/quiz_types';
	import ShapeMark from '$lib/brand/ShapeMark.svelte';
	import { answerStyle } from '$lib/brand/answers';
	import EdIcon from '$lib/editor/EdIcon.svelte';

	let { question = $bindable() }: { question: Question } = $props();

	const poll = $derived(question.type === QuizQuestionType.VOTING);
	const check = $derived(question.type === QuizQuestionType.CHECK);
	const answers = $derived(
		(Array.isArray(question.answers) ? question.answers : []) as Answer[]
	);
	const right_count = $derived(answers.filter((a) => a.right).length);

	const add = () => {
		question.answers = [
			...answers,
			poll ? { answer: '', image: undefined } : { answer: '', right: false }
		] as Answer[];
	};
	const remove = (i: number) => {
		const arr = [...answers];
		arr.splice(i, 1);
		question.answers = arr;
	};
</script>

<div class="head">
	<span class="lbl">{poll ? 'Options' : 'Answers'}</span>
	<span class="hint">
		{#if poll}
			No correct answer in a poll
		{:else if check}
			Tick every correct one
		{:else}
			Tap the check on each correct one
		{/if}
	</span>
</div>

<div class="flex flex-col gap-2">
	{#each answers as answer, i (i)}
		{@const style = answerStyle(i)}
		<div class="atile {style.className}" class:atile-right={!poll && answer.right}>
			<span class="bt-tile-mark mark"><ShapeMark index={i} size={18} /></span>
			<input
				bind:value={question.answers[i].answer}
				type="text"
				class="atile-input"
				enterkeyhint="next"
				placeholder={poll ? `Option ${i + 1}` : `Answer ${i + 1}`}
				aria-label="{poll ? 'Option' : 'Answer'} {i + 1} ({style.label})"
				maxlength="200"
			/>
			{#if answer.answer === '' && answers.length > 2}
				<button
					type="button"
					class="tbtn"
					aria-label="Remove {poll ? 'option' : 'answer'} {i + 1}"
					onclick={() => remove(i)}><EdIcon name="x" size={18} /></button
				>
			{/if}
			{#if !poll}
				<button
					type="button"
					class="tbtn tick"
					class:tick-on={answer.right}
					class:tick-box={check}
					aria-pressed={answer.right}
					aria-label="Answer {i + 1} is correct"
					onclick={() => (question.answers[i].right = !answer.right)}
				>
					<EdIcon name="check" size={20} stroke={3} />
				</button>
			{/if}
		</div>
	{/each}
</div>

{#if answers.length < 4}
	<button type="button" class="add" onclick={add}>
		<EdIcon name="plus" size={18} stroke={2.5} />
		{poll ? 'Add an option' : 'Add an answer'}
	</button>
{/if}

{#if !poll && answers.length > 0 && right_count === 0}
	<p class="warn"><EdIcon name="warn" size={15} /> Mark at least one answer as correct.</p>
{/if}

<style>
	.head {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		gap: 12px;
		margin: 0 0 10px;
	}
	.lbl {
		font-size: 12px;
		letter-spacing: 3px;
		text-transform: uppercase;
		color: var(--ink-muted);
	}
	.hint {
		font-size: 13px;
		color: var(--ink-muted);
		text-align: right;
	}
	.atile {
		min-height: 60px;
		padding: 0 7px 0 8px;
		gap: 10px;
		border-radius: 18px;
		text-transform: none;
	}
	.atile-right {
		box-shadow: inset 0 0 0 3px var(--ink);
	}
	.mark {
		width: 40px;
		height: 40px;
	}
	.atile-input {
		flex: 1;
		min-width: 0;
		height: 44px;
		padding: 0 2px;
		border: 0;
		border-bottom: 2px solid transparent;
		background: transparent;
		color: inherit;
		font-family: var(--bt-font);
		font-size: 17px;
		font-weight: 700;
		outline: none;
	}
	.atile-input::placeholder {
		color: currentColor;
		opacity: 0.62;
		font-weight: 400;
	}
	.atile-input:focus {
		border-bottom-color: currentColor;
	}
	.tbtn {
		display: grid;
		place-items: center;
		flex: none;
		width: 44px;
		height: 44px;
		border-radius: 999px;
		background: var(--fill-deep);
		color: var(--ink);
	}
	.tick {
		color: rgba(255, 255, 255, 0.55);
	}
	.tick-box {
		border-radius: 12px;
	}
	.tick-on {
		background: var(--ink);
		color: var(--ink-dark);
	}
	.tbtn:focus-visible,
	.add:focus-visible {
		outline: 3px solid var(--ink);
		outline-offset: 2px;
	}
	.add {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 8px;
		width: 100%;
		min-height: 48px;
		margin-top: 8px;
		border-radius: 18px;
		background: var(--fill-glass);
		color: var(--ink-muted);
		font-size: 13px;
		font-weight: 700;
		letter-spacing: 2px;
		text-transform: uppercase;
	}
	.warn {
		display: flex;
		align-items: center;
		gap: 8px;
		margin-top: 10px;
		font-size: 14px;
		color: var(--accent-orchid-tint);
	}
</style>
