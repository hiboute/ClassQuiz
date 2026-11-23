<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { portal } from '$lib/editor/portal';
	import type { Answers, Question } from '$lib/quiz_types';
	import { QuizQuestionType } from '$lib/quiz_types';
	import { onMount } from 'svelte';
	import { fade, scale } from 'svelte/transition';
	import ShapeMark from '$lib/brand/ShapeMark.svelte';
	import EdIcon from '$lib/editor/EdIcon.svelte';
	import { typeMeta } from '$lib/editor/editor_meta';

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

	type Preview = 'tiles' | 'truefalse' | 'check' | 'cloud' | 'poll' | 'order' | 'text' | 'range';

	interface Choice {
		key: string;
		name: string;
		description: string;
		type: QuizQuestionType;
		preview: Preview;
		answers: () => Answers;
		time?: string;
	}

	const choices: Choice[] = [
		{
			key: 'abcd',
			name: typeMeta(QuizQuestionType.ABCD).name,
			description: typeMeta(QuizQuestionType.ABCD).description,
			type: QuizQuestionType.ABCD,
			preview: 'tiles',
			answers: () => [
				{ answer: '', right: true },
				{ answer: '', right: false },
				{ answer: '', right: false },
				{ answer: '', right: false }
			]
		},
		{
			key: 'truefalse',
			name: 'True or false',
			description: 'Two answers, True and False. Quick to write, quick to play.',
			type: QuizQuestionType.ABCD,
			preview: 'truefalse',
			time: '10',
			answers: () => [
				{ answer: 'True', right: true },
				{ answer: 'False', right: false }
			]
		},
		{
			key: 'cloud',
			name: typeMeta(QuizQuestionType.WORD_CLOUD).name,
			description: 'Word cloud: players type a short word, the screen shows a live cloud.',
			type: QuizQuestionType.WORD_CLOUD,
			preview: 'cloud',
			time: '30',
			answers: () => []
		},
		{
			key: 'check',
			name: typeMeta(QuizQuestionType.CHECK).name,
			description: typeMeta(QuizQuestionType.CHECK).description,
			type: QuizQuestionType.CHECK,
			preview: 'check',
			answers: () => [
				{ answer: '', right: true },
				{ answer: '', right: true },
				{ answer: '', right: false },
				{ answer: '', right: false }
			]
		},
		{
			key: 'poll',
			name: typeMeta(QuizQuestionType.VOTING).name,
			description: typeMeta(QuizQuestionType.VOTING).description,
			type: QuizQuestionType.VOTING,
			preview: 'poll',
			answers: () => [
				{ answer: '', image: undefined },
				{ answer: '', image: undefined }
			]
		},
		{
			key: 'order',
			name: typeMeta(QuizQuestionType.ORDER).name,
			description: typeMeta(QuizQuestionType.ORDER).description,
			type: QuizQuestionType.ORDER,
			preview: 'order',
			time: '30',
			answers: () => [
				{ answer: '', id: 0 },
				{ answer: '', id: 1 },
				{ answer: '', id: 2 }
			]
		},
		{
			key: 'text',
			name: typeMeta(QuizQuestionType.TEXT).name,
			description: typeMeta(QuizQuestionType.TEXT).description,
			type: QuizQuestionType.TEXT,
			preview: 'text',
			time: '30',
			answers: () => [{ answer: '', case_sensitive: false }]
		},
		{
			key: 'range',
			name: typeMeta(QuizQuestionType.RANGE).name,
			description: typeMeta(QuizQuestionType.RANGE).description,
			type: QuizQuestionType.RANGE,
			preview: 'range',
			answers: () => ({
				max: 10,
				min: 0,
				max_correct: 7,
				min_correct: 3
			})
		}
	];

	const add_question = (c: Choice) => {
		const empty_question: Question = {
			type: c.type,
			time: c.time ?? '20',
			question: '',
			image: undefined,
			answers: c.answers(),
			points: c.type === QuizQuestionType.WORD_CLOUD ? 'none' : 'standard'
		};
		questions = [...questions, empty_question];
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
					<span class="preview" aria-hidden="true">
						{#if c.preview === 'tiles' || c.preview === 'check'}
							<span class="grid w-full grid-cols-2 gap-1">
								{#each [0, 1, 2, 3] as k}
									<span class="pv-tile bt-tile-{['a', 'b', 'c', 'd'][k]}">
										<ShapeMark index={k} size={10} />
										{#if c.preview === 'check' && k < 2}
											<EdIcon name="check" size={11} stroke={3} class="ml-auto" />
										{/if}
									</span>
								{/each}
							</span>
						{:else if c.preview === 'truefalse'}
							<span class="grid w-full grid-cols-2 gap-1">
								<span class="pv-tile pv-tall bt-tile-a"><ShapeMark index={0} size={11} />True</span>
								<span class="pv-tile pv-tall bt-tile-b"><ShapeMark index={1} size={11} />False</span>
							</span>
						{:else if c.preview === 'cloud'}
							<span class="cloud">
								<b class="text-[19px] text-accent-sky">beauty</b>
								<b class="text-[12px] text-accent-pink">AI</b>
								<b class="text-[14px] text-accent-green">skin</b>
								<b class="text-[11px]">data</b>
								<b class="text-[15px] text-accent-orchid">care</b>
							</span>
						{:else if c.preview === 'poll'}
							<span class="flex h-full w-full items-end justify-center gap-1.5">
								{#each [55, 85, 35, 65] as h, k}
									<span class="pv-bar bt-tile-{['a', 'b', 'c', 'd'][k]}" style="height:{h}%"></span>
								{/each}
							</span>
						{:else if c.preview === 'order'}
							<span class="flex w-full flex-col gap-1">
								{#each [1, 2, 3] as n}
									<span class="pv-line"><b class="bt-num">{n}</b><i></i></span>
								{/each}
							</span>
						{:else if c.preview === 'text'}
							<span class="pv-input">Type here<i></i></span>
						{:else if c.preview === 'range'}
							<span class="pv-range"><i></i><b></b></span>
						{/if}
					</span>
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
	.pv-tile {
		display: flex;
		align-items: center;
		gap: 6px;
		height: 24px;
		padding: 0 8px;
		border-radius: 7px;
		font-size: 11px;
	}
	.pv-tall {
		height: 52px;
		justify-content: center;
		letter-spacing: 1px;
	}
	.cloud {
		display: flex;
		flex-wrap: wrap;
		align-items: baseline;
		justify-content: center;
		gap: 2px 8px;
		line-height: 1;
	}
	.pv-bar {
		width: 16%;
		border-radius: 5px 5px 2px 2px;
	}
	.pv-line {
		display: flex;
		align-items: center;
		gap: 8px;
		height: 16px;
		padding: 0 8px;
		border-radius: 6px;
		background: var(--fill-glass-mid);
		font-size: 11px;
	}
	.pv-line i {
		flex: 1;
		height: 3px;
		border-radius: 2px;
		background: var(--fill-glass-strong);
	}
	.pv-input {
		display: flex;
		align-items: center;
		width: 100%;
		height: 34px;
		padding: 0 12px;
		border-radius: 12px;
		background: var(--fill-glass-mid);
		font-size: 12px;
		color: var(--ink-muted);
	}
	.pv-input i {
		width: 2px;
		height: 16px;
		margin-left: 3px;
		background: var(--accent-sky);
	}
	.pv-range {
		position: relative;
		width: 100%;
		height: 6px;
		border-radius: 3px;
		background: var(--fill-glass-strong);
	}
	.pv-range i {
		position: absolute;
		left: 30%;
		right: 30%;
		top: 0;
		bottom: 0;
		border-radius: 3px;
		background: linear-gradient(90deg, var(--accent-sky), var(--accent-green));
	}
	.pv-range b {
		position: absolute;
		left: 30%;
		top: -6px;
		width: 18px;
		height: 18px;
		border-radius: 999px;
		background: var(--ink);
	}
</style>
