<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import type { EditorData, OrderQuizAnswer } from '$lib/quiz_types';
	import { fade } from 'svelte/transition';
	import { flip } from 'svelte/animate';
	import ShapeMark from '$lib/brand/ShapeMark.svelte';
	import { answerStyle } from '$lib/brand/answers';
	import EdIcon from '$lib/editor/EdIcon.svelte';

	interface Props {
		selected_question: number;
		data: EditorData;
	}

	let { selected_question, data = $bindable() }: Props = $props();

	if (!Array.isArray(data.questions[selected_question].answers)) {
		data.questions[selected_question].answers = [];
	}
	// give every item a stable numeric id for the animated list
	data.questions[selected_question].answers = (
		data.questions[selected_question].answers as OrderQuizAnswer[]
	).map((a, i) => ({
		answer: a.answer ?? '',
		color: a.color ?? undefined,
		id: i
	}));

	const answers = $derived(data.questions[selected_question].answers as OrderQuizAnswer[]);

	const move_item = (index: number, to: number) => {
		if (to < 0 || to >= answers.length) return;
		const arr = [...answers];
		[arr[index], arr[to]] = [arr[to], arr[index]];
		data.questions[selected_question].answers = arr;
	};
	const remove_item = (index: number) => {
		const arr = [...answers];
		arr.splice(index, 1);
		data.questions[selected_question].answers = arr;
	};
	const add_item = () => {
		const next_id = answers.reduce((m, a) => Math.max(m, Number(a.id ?? 0)), -1) + 1;
		data.questions[selected_question].answers = [
			...answers,
			{ answer: '', color: undefined, id: next_id }
		];
	};
</script>

<div class="mb-4 flex flex-wrap items-center gap-x-4 gap-y-2">
	<span class="bt-eyebrow text-[11px] text-ink-muted">Correct order</span>
	<span class="text-xs text-ink-muted">
		Write the items from first to last. Players get them shuffled.
	</span>
</div>

<div class="flex flex-col gap-2">
	{#each answers as answer, i (answer.id)}
		<div
			class="item {answerStyle(i).className}"
			animate:flip={{ duration: 180 }}
			out:fade={{ duration: 120 }}
		>
			<span class="pos bt-num">{i + 1}</span>
			<span class="bt-tile-mark mark"><ShapeMark index={i} size={16} /></span>
			<input
				bind:value={answer.answer}
				type="text"
				class="item-input"
				placeholder="Item {i + 1}"
				aria-label="Item {i + 1}"
				maxlength="200"
			/>
			<span class="flex gap-1">
				<button
					type="button"
					class="tool"
					aria-label="Move up"
					title="Move up"
					disabled={i === 0}
					onclick={() => move_item(i, i - 1)}><EdIcon name="up" size={16} /></button
				>
				<button
					type="button"
					class="tool"
					aria-label="Move down"
					title="Move down"
					disabled={i === answers.length - 1}
					onclick={() => move_item(i, i + 1)}><EdIcon name="down" size={16} /></button
				>
				<button
					type="button"
					class="tool"
					aria-label="Remove item {i + 1}"
					title="Remove"
					disabled={answers.length <= 1}
					onclick={() => remove_item(i)}><EdIcon name="x" size={16} /></button
				>
			</span>
		</div>
	{/each}
</div>
{#if answers.length < 4}
	<button class="add mt-3" type="button" onclick={add_item}>
		<EdIcon name="plus" size={18} stroke={2.5} /> Add an item
	</button>
{/if}

<style>
	.item {
		min-height: 64px;
		padding: 8px 10px 8px 16px;
		gap: 12px;
		border-radius: 20px;
		text-transform: none;
	}
	.pos {
		width: 22px;
		font-size: 22px;
		text-align: center;
	}
	.mark {
		width: 36px;
		height: 36px;
		border-radius: 10px;
	}
	.item-input {
		flex: 1;
		min-width: 0;
		align-self: stretch;
		border: 0;
		border-bottom: 2px solid transparent;
		background: transparent;
		color: inherit;
		font-family: var(--bt-font);
		font-weight: 800;
		font-size: 18px;
		outline: none;
	}
	.item-input::placeholder {
		color: currentColor;
		opacity: 0.55;
	}
	.item-input:focus {
		border-bottom-color: currentColor;
	}
	.tool {
		display: grid;
		place-items: center;
		width: 34px;
		height: 34px;
		border-radius: 999px;
		background: var(--fill-deep);
		color: var(--ink);
	}
	.tool:hover:not(:disabled) {
		background: rgba(10, 5, 31, 0.9);
	}
	.tool:disabled {
		opacity: 0.35;
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
	.tool:focus-visible,
	.add:focus-visible {
		outline: 3px solid var(--accent-sky-tint);
		outline-offset: 2px;
	}
</style>
