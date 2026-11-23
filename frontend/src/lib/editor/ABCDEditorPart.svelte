<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import type { Answer, EditorData } from '../quiz_types';
	import { QuizQuestionType } from '../quiz_types';
	import { fade } from 'svelte/transition';
	import AnswerTile from '$lib/editor/AnswerTile.svelte';
	import EdIcon from '$lib/editor/EdIcon.svelte';

	interface Props {
		selected_question: number;
		check_choice?: boolean;
		data: EditorData;
	}

	let { selected_question, check_choice = false, data = $bindable() }: Props = $props();

	if (!Array.isArray(data.questions[selected_question].answers)) {
		data.questions[selected_question].answers = [];
	}
	data.questions[selected_question].type =
		check_choice === true ? QuizQuestionType.CHECK : QuizQuestionType.ABCD;

	const answers = $derived(data.questions[selected_question].answers as Answer[]);
	const right_count = $derived(answers.filter((a) => a.right).length);
	const is_true_false = $derived(
		answers.length === 2 &&
			answers[0].answer.trim().toLowerCase() === 'true' &&
			answers[1].answer.trim().toLowerCase() === 'false'
	);

	const add_answer = () => {
		data.questions[selected_question].answers = [
			...answers,
			{ answer: '', right: false }
		];
	};
	const remove_answer = (index: number) => {
		const arr = [...answers];
		arr.splice(index, 1);
		data.questions[selected_question].answers = arr;
	};
	const set_true_false = () => {
		if (
			answers.some((a) => a.answer.trim() !== '') &&
			!confirm('Replace the answers with True and False?')
		) {
			return;
		}
		data.questions[selected_question].answers = [
			{ answer: 'True', right: true },
			{ answer: 'False', right: false }
		];
	};
	const switch_mode = () => {
		data.questions[selected_question].type = check_choice
			? QuizQuestionType.ABCD
			: QuizQuestionType.CHECK;
	};
</script>

<div class="mb-4 flex flex-wrap items-center gap-x-4 gap-y-2">
	<span class="bt-eyebrow text-[11px] text-ink-muted">Answers</span>
	<span class="text-xs text-ink-muted">
		{#if check_choice}
			Players tick every correct answer.
		{:else}
			Tap the check on each correct answer.
		{/if}
	</span>
	<span class="ml-auto flex flex-wrap gap-2">
		{#if !check_choice}
			<button
				type="button"
				class="mini-btn"
				class:mini-on={is_true_false}
				onclick={set_true_false}
				title="Two answers: True and False"
			>
				True / False
			</button>
		{/if}
		<button
			type="button"
			class="mini-btn"
			onclick={switch_mode}
			title={check_choice
				? 'Players pick one answer'
				: 'Players can tick several answers'}
		>
			{check_choice ? 'Single pick' : 'Multiple select'}
		</button>
	</span>
</div>

<div class="grid grid-cols-1 gap-3 md:grid-cols-2">
	{#each answers as _answer, index (index)}
		<div out:fade={{ duration: 120 }}>
			<AnswerTile
				bind:answer={data.questions[selected_question].answers[index]}
				{index}
				check_style={check_choice}
				placeholder={is_true_false ? undefined : `Answer ${index + 1}`}
				removable={answers.length > 1}
				onremove={() => remove_answer(index)}
			/>
		</div>
	{/each}
	{#if answers.length < 4}
		<button class="add-tile" type="button" in:fade={{ duration: 120 }} onclick={add_answer}>
			<EdIcon name="plus" size={20} stroke={2.5} />
			<span>Add an answer</span>
		</button>
	{/if}
</div>

{#if answers.length > 0 && right_count === 0}
	<p class="hint-warn mt-3">
		<EdIcon name="warn" size={15} /> Mark at least one answer as correct, or nobody can score.
	</p>
{/if}

<style>
	.mini-btn {
		height: 32px;
		padding: 0 14px;
		border-radius: 999px;
		background: var(--fill-glass);
		font-size: 12px;
		font-weight: 700;
		letter-spacing: 1.5px;
		text-transform: uppercase;
	}
	.mini-btn:hover {
		background: var(--fill-glass-strong);
	}
	.mini-on {
		box-shadow: inset 0 0 0 2px var(--accent-sky);
	}
	.mini-btn:focus-visible,
	.add-tile:focus-visible {
		outline: 3px solid var(--accent-sky-tint);
		outline-offset: 2px;
	}
	.add-tile {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 10px;
		min-height: 92px;
		border-radius: 25px;
		background: var(--fill-glass);
		color: var(--ink-muted);
		font-weight: 700;
		letter-spacing: 2px;
		text-transform: uppercase;
		font-size: 13px;
		transition: background-color 120ms ease;
	}
	.add-tile:hover {
		background: var(--fill-glass-mid);
		color: var(--ink);
	}
	.hint-warn {
		display: flex;
		align-items: center;
		gap: 8px;
		font-size: 13px;
		color: #ffd3fb;
	}
</style>
