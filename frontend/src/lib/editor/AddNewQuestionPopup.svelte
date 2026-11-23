<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { portal } from '$lib/editor/portal';
	import type { Question } from '$lib/quiz_types';
	import { onMount } from 'svelte';
	import { fade, scale } from 'svelte/transition';
	import EdIcon from '$lib/editor/EdIcon.svelte';
	import TypePreview from '$lib/editor/TypePreview.svelte';
	import { QUESTION_CHOICES as choices, newQuestion, type QuestionChoice } from '$lib/editor/editor_meta';

	interface Props {
		questions: Question[];
		open: boolean;
		selected_question: number;
	}

	let {
		questions = $bindable(),
		open = $bindable(),
		selected_question = $bindable()
	}: Props = $props();

	let dialog_el: HTMLDivElement = $state();

	onMount(() => {
		document.body.addEventListener('keydown', close_if_esc_is_pressed);
		dialog_el?.querySelector<HTMLButtonElement>('.choice')?.focus();
		return () => document.body.removeEventListener('keydown', close_if_esc_is_pressed);
	});
	const close_if_esc_is_pressed = (key: KeyboardEvent) => {
		if (key.code === 'Escape') {
			open = false;
		}
	};
	const on_parent_click = (e: Event) => {
		if (e.target === e.currentTarget) {
			open = false;
		}
	};

	const add_question = (c: QuestionChoice) => {
		questions = [...questions, newQuestion(c)];
		selected_question = questions.length - 1;
		open = false;
	};
</script>

<div
	use:portal
	class="fixed inset-0 z-50 flex items-center justify-center bg-[rgba(5,3,20,0.72)] p-4"
	onclick={on_parent_click}
	role="presentation"
	transition:fade={{ duration: 120 }}
>
	<div
		class="bt-glass bt-glass-deep popup flex max-h-full w-full max-w-5xl flex-col p-6 lg:p-8"
		role="dialog"
		aria-modal="true"
		aria-labelledby="add-question-title"
		bind:this={dialog_el}
		transition:scale={{ duration: 140, start: 0.97 }}
	>
		<div class="mb-5 flex items-start gap-4">
			<div class="flex-1">
				<span class="bt-eyebrow text-[11px] text-ink-muted">Add to the quiz</span>
				<h2 id="add-question-title" class="bt-headline text-2xl lg:text-3xl">
					Choose a question type
				</h2>
			</div>
			<button
				type="button"
				class="close"
				aria-label="Close"
				onclick={() => (open = false)}><EdIcon name="x" size={20} /></button
			>
		</div>
		<div class="grid min-h-0 grid-cols-1 gap-3 overflow-y-auto sm:grid-cols-2 lg:grid-cols-4">
			{#each choices as c}
				<button
					type="button"
					class="choice"
					onclick={() => add_question(c)}
				>
					<span class="preview" aria-hidden="true"><TypePreview kind={c.preview} /></span>
					<span class="block text-base font-black uppercase leading-tight">{c.name}</span>
					<span class="mt-1 block text-sm leading-snug text-ink-muted">{c.description}</span>
				</button>
			{/each}
		</div>
		<p class="mt-5 text-center text-sm text-ink-muted">
			Need a content slide between questions? Use the Slide button under the list.
		</p>
	</div>
</div>

<style>
	.popup {
		background: rgba(14, 10, 46, 0.92);
	}
	.close {
		display: grid;
		place-items: center;
		width: 40px;
		height: 40px;
		border-radius: 999px;
		background: var(--fill-glass);
	}
	.close:hover {
		background: var(--fill-glass-strong);
	}
	.choice {
		display: flex;
		flex-direction: column;
		text-align: left;
		padding: 14px;
		border-radius: 20px;
		background: var(--fill-glass);
		transition:
			background-color 120ms ease,
			transform 120ms ease;
	}
	.choice:hover {
		background: var(--fill-glass-strong);
		transform: translateY(-2px);
	}
	.choice:focus-visible {
		outline: 3px solid var(--accent-sky-tint);
		outline-offset: 2px;
	}
	.preview {
		display: flex;
		align-items: center;
		justify-content: center;
		height: 78px;
		margin-bottom: 12px;
		padding: 10px;
		border-radius: 14px;
		background: var(--fill-deep);
	}
</style>
