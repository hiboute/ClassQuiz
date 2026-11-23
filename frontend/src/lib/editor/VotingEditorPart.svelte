<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import type { EditorData, VotingAnswer } from '../quiz_types';
	import { fade } from 'svelte/transition';
	import AnswerTile from '$lib/editor/AnswerTile.svelte';
	import EdIcon from '$lib/editor/EdIcon.svelte';

	interface Props {
		selected_question: number;
		data: EditorData;
	}

	let { selected_question, data = $bindable() }: Props = $props();

	if (!Array.isArray(data.questions[selected_question].answers)) {
		data.questions[selected_question].answers = [];
	}
	try {
		// answers of another type (with a right flag) do not belong in a poll
		if (typeof (data.questions[selected_question].answers[0] as { right?: unknown }).right === 'boolean') {
			data.questions[selected_question].answers = [];
		}
		// eslint-disable-next-line no-empty
	} catch {}

	const answers = $derived(data.questions[selected_question].answers as VotingAnswer[]);

	const add_answer = () => {
		data.questions[selected_question].answers = [...answers, { answer: '', image: undefined }];
	};
	const remove_answer = (index: number) => {
		const arr = [...answers];
		arr.splice(index, 1);
		data.questions[selected_question].answers = arr;
	};
</script>

<div class="mb-4 flex flex-wrap items-center gap-x-4 gap-y-2">
	<span class="bt-eyebrow text-[11px] text-ink-muted">Options</span>
	<span class="text-xs text-ink-muted">
		A poll: no correct answer, no points. The screen shows how the room voted.
	</span>
</div>

<div class="grid grid-cols-1 gap-3 md:grid-cols-2">
	{#each answers as _answer, index (index)}
		<div out:fade={{ duration: 120 }}>
			<AnswerTile
				bind:answer={data.questions[selected_question].answers[index]}
				{index}
				correct_toggle={false}
				placeholder="Option {index + 1}"
				removable={answers.length > 1}
				onremove={() => remove_answer(index)}
			/>
		</div>
	{/each}
	{#if answers.length < 4}
		<button class="add-tile" type="button" in:fade={{ duration: 120 }} onclick={add_answer}>
			<EdIcon name="plus" size={20} stroke={2.5} />
			<span>Add an option</span>
		</button>
	{/if}
</div>

<style>
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
	.add-tile:focus-visible {
		outline: 3px solid var(--accent-sky-tint);
		outline-offset: 2px;
	}
</style>
