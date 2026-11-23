<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import type { EditorData, Question } from '../quiz_types';
	import { QuizQuestionType } from '$lib/quiz_types';
	import { reach, type Schema } from 'yup';
	import { dataSchema } from '../yupSchemas';
	import AddNewQuestionPopup from '$lib/editor/AddNewQuestionPopup.svelte';
	import EdIcon from '$lib/editor/EdIcon.svelte';
	import ShapeMark from '$lib/brand/ShapeMark.svelte';
	import { answerStyle } from '$lib/brand/answers';
	import { plainText, pointsOf, questionIssue, typeMeta } from '$lib/editor/editor_meta';
	import { flip } from 'svelte/animate';

	interface Props {
		data: EditorData;
		selected_question?: number;
	}

	let { data = $bindable(), selected_question = $bindable(-1) }: Props = $props();

	let arr_of_cards: HTMLElement[] = $state([]);
	let propertyCard: HTMLElement = $state();
	let add_new_question_popup_open = $state(false);

	const titleSchema = reach(dataSchema, 'title') as Schema;
	const descriptionSchema = reach(dataSchema, 'description') as Schema;
	const settingsValid = $derived.by(() => {
		try {
			return (
				titleSchema.isValidSync(data.title) && descriptionSchema.isValidSync(data.description)
			);
		} catch {
			return false;
		}
	});

	// stable keys for the animated list (questions have no id of their own)
	let keys = new WeakMap<object, number>();
	let next_key = 0;
	const keyOf = (q: object): number => {
		if (!keys.has(q)) keys.set(q, next_key++);
		return keys.get(q);
	};

	const swap = (a: number, b: number) => {
		if (b < 0 || b >= data.questions.length) return;
		const arr = [...data.questions];
		[arr[a], arr[b]] = [arr[b], arr[a]];
		data.questions = arr;
		if (selected_question === a) selected_question = b;
		else if (selected_question === b) selected_question = a;
	};

	const duplicate = (index: number) => {
		const copy = JSON.parse(JSON.stringify($state.snapshot(data.questions[index])));
		const arr = [...data.questions];
		arr.splice(index + 1, 0, copy);
		data.questions = arr;
		selected_question = index + 1;
	};

	const remove = (index: number) => {
		const label = plainText(data.questions[index].question) || 'this question';
		if (!confirm(`Delete "${label}"?`)) return;
		const arr = [...data.questions];
		arr.splice(index, 1);
		data.questions = arr;
		if (selected_question === index) selected_question = -1;
		else if (selected_question > index) selected_question -= 1;
	};

	const setSelectedQuestion = (index: number): void => {
		selected_question = index;
		const el = index === -1 ? propertyCard : arr_of_cards[index];
		el?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
	};

	const add_slide = () => {
		data.questions = [
			...data.questions,
			{
				type: QuizQuestionType.SLIDE,
				time: '120',
				question: 'Slide',
				image: undefined,
				answers: ''
			}
		];
		selected_question = data.questions.length - 1;
	};

	const answerList = (q: Question): { answer: string; right?: boolean }[] =>
		Array.isArray(q.answers) ? (q.answers as { answer: string; right?: boolean }[]) : [];
</script>

<div class="bt-glass bt-glass-deep sidebar flex h-full flex-col">
	<div class="px-5 pt-5 pb-3">
		<span class="bt-eyebrow text-[11px] text-ink-muted">Live Quiz</span>
		<span class="block text-lg font-black uppercase leading-tight">Questions</span>
	</div>

	<div class="min-h-0 flex-1 overflow-y-auto px-3 pb-3" role="list">
		<!-- quiz settings -->
		<button
			type="button"
			bind:this={propertyCard}
			class="row w-full text-left"
			class:row-active={selected_question === -1}
			onclick={() => setSelectedQuestion(-1)}
			aria-current={selected_question === -1}
		>
			<span class="badge"><EdIcon name="settings" size={18} /></span>
			<span class="min-w-0 flex-1">
				<span class="bt-eyebrow text-[10px] tracking-[3px] text-ink-muted">Quiz settings</span>
				<span class="block truncate font-bold">
					{plainText(data.title) || 'Untitled quiz'}
				</span>
				<span class="mt-1 flex items-center gap-1.5 text-xs text-ink-muted">
					<EdIcon name={data.public ? 'globe' : 'lock'} size={13} />
					{data.public ? 'Public' : 'Private'}
				</span>
			</span>
			{#if !settingsValid}
				<span class="warn" title="Title or description missing"><EdIcon name="warn" size={16} /></span>
			{/if}
		</button>

		<div class="mt-3 flex flex-col gap-2">
			{#each data.questions as question, index (keyOf(question))}
				{@const meta = typeMeta(question.type)}
				{@const issue = questionIssue(question)}
				{@const pts = pointsOf(question)}
				<div
					animate:flip={{ duration: 180 }}
					bind:this={arr_of_cards[index]}
					class="row group relative"
					class:row-active={index === selected_question}
					role="listitem"
				>
					<button
						type="button"
						class="absolute inset-0 rounded-[18px]"
						aria-label="Edit question {index + 1}"
						onclick={() => setSelectedQuestion(index)}
					></button>
					<span class="badge bt-num pointer-events-none">{index + 1}</span>
					<span class="pointer-events-none min-w-0 flex-1">
						<span class="flex items-center gap-2 text-[10px] text-ink-muted">
							<span class="bt-eyebrow text-[10px] tracking-[2.5px]">{meta.short}</span>
							{#if question.type !== QuizQuestionType.SLIDE}
								<span class="tabular-nums">{question.time}s</span>
							{/if}
							{#if issue}
								<span class="warn" title={issue}><EdIcon name="warn" size={13} /></span>
							{/if}
							{#if pts === 'double'}
								<span class="chip-mini">2x</span>
							{:else if pts === 'none' && question.type !== QuizQuestionType.SLIDE && question.type !== QuizQuestionType.VOTING && question.type !== QuizQuestionType.WORD_CLOUD}
								<span class="chip-mini">0 pts</span>
							{/if}
						</span>
						<span class="mt-0.5 block truncate text-sm font-bold" class:italic={!question.question}>
							{plainText(question.question) || 'No question yet'}
						</span>
						{#if question.type === QuizQuestionType.ABCD || question.type === QuizQuestionType.CHECK || question.type === QuizQuestionType.VOTING}
							<span class="mt-1.5 flex gap-1">
								{#each answerList(question) as answer, ai}
									<span
										class="mini-tile {answerStyle(ai).className}"
										class:mini-right={answer.right}
										title={answer.answer}
									>
										<ShapeMark index={ai} size={9} />
										{#if answer.right}<EdIcon name="check" size={10} stroke={3} />{/if}
									</span>
								{/each}
							</span>
						{/if}
					{#if index === selected_question}
							<span class="row-tools pointer-events-auto">
						<button
							type="button"
							class="tool"
							aria-label="Move up"
							title="Move up"
							disabled={index === 0}
							onclick={() => swap(index, index - 1)}><EdIcon name="up" size={16} /></button
						>
						<button
							type="button"
							class="tool"
							aria-label="Move down"
							title="Move down"
							disabled={index === data.questions.length - 1}
							onclick={() => swap(index, index + 1)}><EdIcon name="down" size={16} /></button
						>
						<button
							type="button"
							class="tool"
							aria-label="Duplicate"
							title="Duplicate"
							onclick={() => duplicate(index)}><EdIcon name="copy" size={15} /></button
						>
						<button
							type="button"
							class="tool tool-danger"
							aria-label="Delete"
							title="Delete"
							onclick={() => remove(index)}><EdIcon name="trash" size={15} /></button
						>
					</span>
						{/if}
					</span>
				</div>
			{/each}
		</div>
		{#if data.questions.length === 0}
			<p class="px-3 py-6 text-center text-sm text-ink-muted">
				No questions yet. Add the first one below.
			</p>
		{/if}
	</div>

	<div class="flex gap-2 p-3">
		<button
			type="button"
			class="bt-btn-primary flex-1 add-btn"
			onclick={() => (add_new_question_popup_open = true)}
		>
			<EdIcon name="plus" size={18} stroke={2.5} /> Question
		</button>
		<button type="button" class="bt-btn-ghost add-btn" onclick={add_slide} title="Add a slide">
			<EdIcon name="slide" size={18} /> Slide
		</button>
	</div>
</div>
{#if add_new_question_popup_open}
	<AddNewQuestionPopup
		bind:questions={data.questions}
		bind:open={add_new_question_popup_open}
		bind:selected_question
	/>
{/if}

<style>
	.sidebar {
		border-radius: 0;
	}
	@media (min-width: 768px) {
		.sidebar {
			border-radius: 0 25px 25px 0;
		}
	}
	.row {
		display: flex;
		align-items: flex-start;
		gap: 12px;
		padding: 12px;
		border-radius: 18px;
		background: var(--fill-glass-faint);
		transition: background-color 120ms ease;
		cursor: pointer;
	}
	.row:hover {
		background: var(--fill-glass);
	}
	.row-active,
	.row-active:hover {
		background: var(--fill-glass-strong);
		box-shadow: inset 3px 0 0 var(--accent-sky);
	}
	.badge {
		flex: none;
		display: grid;
		place-items: center;
		width: 34px;
		height: 34px;
		border-radius: 12px;
		background: var(--fill-glass-mid);
		font-size: 15px;
		line-height: 1;
	}
	.row-active .badge {
		background: linear-gradient(90deg, var(--accent-sky) 0%, var(--accent-green) 100%);
		color: var(--ink-dark);
	}
	.warn {
		flex: none;
		color: var(--accent-pink);
	}
	.chip-mini {
		padding: 1px 6px;
		border-radius: 999px;
		background: var(--fill-glass-mid);
		color: var(--ink);
		font-weight: 700;
		font-size: 10px;
	}
	.mini-tile {
		display: inline-flex;
		align-items: center;
		gap: 2px;
		height: 16px;
		min-width: 22px;
		padding: 0 4px;
		border-radius: 5px;
		gap: 2px;
	}
	.mini-tile:not(.mini-right) {
		opacity: 0.55;
	}
	.mini-right {
		box-shadow: 0 0 0 1.5px var(--ink);
	}
	.row-tools {
		position: relative;
		z-index: 1;
		display: flex;
		gap: 4px;
		margin-top: 10px;
	}
	.tool {
		display: grid;
		place-items: center;
		width: 32px;
		height: 32px;
		border-radius: 999px;
		background: var(--fill-deep);
		color: var(--ink);
	}
	.tool:hover:not(:disabled) {
		background: var(--fill-glass-strong);
	}
	.tool:disabled {
		opacity: 0.3;
		cursor: not-allowed;
	}
	.tool-danger:hover:not(:disabled) {
		background: rgba(249, 130, 250, 0.3);
	}
	.tool:focus-visible {
		outline: 2px solid var(--accent-sky-tint);
	}
	.add-btn {
		min-height: 46px;
		padding: 0 18px;
		font-size: 14px;
		letter-spacing: 2px;
	}
</style>
