<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { fade } from 'svelte/transition';
	import type { EditorData, TextQuizAnswer } from '$lib/quiz_types';
	import EdIcon from '$lib/editor/EdIcon.svelte';

	interface Props {
		selected_question: number;
		data: EditorData;
	}

	let { selected_question, data = $bindable() }: Props = $props();

	if (!Array.isArray(data.questions[selected_question].answers)) {
		data.questions[selected_question].answers = [];
	}

	for (let i = 0; i < data.questions[selected_question].answers.length; i++) {
		const a = data.questions[selected_question].answers[i] as Partial<TextQuizAnswer>;
		data.questions[selected_question].answers[i] = {
			answer: a.answer ?? '',
			case_sensitive: a.case_sensitive === true
		};
	}

	const answers = $derived(data.questions[selected_question].answers as TextQuizAnswer[]);

	const add_answer = () => {
		data.questions[selected_question].answers = [
			...answers,
			{ answer: '', case_sensitive: false }
		];
	};
	const remove_answer = (index: number) => {
		const arr = [...answers];
		arr.splice(index, 1);
		data.questions[selected_question].answers = arr;
	};
</script>

<div class="mb-4 flex flex-wrap items-center gap-x-4 gap-y-2">
	<span class="bt-eyebrow text-[11px] text-ink-muted">Accepted answers</span>
	<span class="text-xs text-ink-muted">
		A typed answer scores when it matches one of these. Add common spellings.
	</span>
</div>

<div class="flex flex-col gap-2">
	{#each answers as answer, index (index)}
		<div class="row" out:fade={{ duration: 120 }}>
			<span class="num bt-num">{index + 1}</span>
			<input
				bind:value={answer.answer}
				type="text"
				class="bt-input row-input"
				placeholder={index === 0 ? 'The answer' : 'Another accepted spelling'}
				aria-label="Accepted answer {index + 1}"
				maxlength="200"
			/>
			<button
				type="button"
				class="case"
				class:case-on={answer.case_sensitive}
				aria-pressed={answer.case_sensitive}
				title="Match upper and lower case exactly"
				onclick={() => (answer.case_sensitive = !answer.case_sensitive)}
			>
				<span class="font-black normal-case tracking-normal">Aa</span>
				{answer.case_sensitive ? 'Exact case' : 'Any case'}
			</button>
			<button
				type="button"
				class="remove"
				aria-label="Remove answer {index + 1}"
				title="Remove"
				disabled={answers.length <= 1}
				onclick={() => remove_answer(index)}><EdIcon name="x" size={16} /></button
			>
		</div>
	{/each}
</div>
{#if answers.length < 16}
	<button class="add mt-3" type="button" onclick={add_answer}>
		<EdIcon name="plus" size={18} stroke={2.5} /> Add a spelling
	</button>
{/if}

<style>
	.row {
		display: flex;
		align-items: center;
		gap: 10px;
	}
	.num {
		display: grid;
		place-items: center;
		flex: none;
		width: 36px;
		height: 36px;
		border-radius: 12px;
		background: var(--fill-glass-mid);
		font-size: 15px;
	}
	.row-input {
		flex: 1;
		min-width: 0;
		padding: 12px 18px;
		border-radius: 16px;
		font-size: 17px;
		font-weight: 700;
	}
	.case {
		display: inline-flex;
		align-items: center;
		gap: 8px;
		flex: none;
		height: 40px;
		padding: 0 14px;
		border-radius: 999px;
		background: var(--fill-glass);
		color: var(--ink-muted);
		font-size: 12px;
		font-weight: 700;
		letter-spacing: 1.5px;
		text-transform: uppercase;
	}
	.case-on {
		background: var(--fill-glass-strong);
		color: var(--ink);
	}
	.remove {
		display: grid;
		place-items: center;
		flex: none;
		width: 36px;
		height: 36px;
		border-radius: 999px;
		background: var(--fill-glass);
	}
	.remove:hover:not(:disabled) {
		background: rgba(249, 130, 250, 0.3);
	}
	.remove:disabled {
		opacity: 0.3;
		cursor: not-allowed;
	}
	.add {
		display: inline-flex;
		align-items: center;
		gap: 8px;
		height: 40px;
		padding: 0 18px;
		border-radius: 999px;
		background: var(--fill-glass);
		font-size: 13px;
		font-weight: 700;
		letter-spacing: 2px;
		text-transform: uppercase;
	}
	.add:hover {
		background: var(--fill-glass-strong);
	}
	.case:focus-visible,
	.remove:focus-visible,
	.add:focus-visible {
		outline: 3px solid var(--accent-sky-tint);
		outline-offset: 2px;
	}
</style>
