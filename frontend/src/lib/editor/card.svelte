<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import type { EditorData, QuestionPoints } from '$lib/quiz_types';
	import { QuizQuestionType } from '$lib/quiz_types';
	import RangeEditor from '$lib/editor/RangeSelectorEditorPart.svelte';
	import ABCDEditor from '$lib/editor/ABCDEditorPart.svelte';
	import VotingEditor from '$lib/editor/VotingEditorPart.svelte';
	import TextEditor from '$lib/editor/TextEditorPart.svelte';
	import OrderEditor from '$lib/editor/OrderEditorPart.svelte';
	import WordCloudEditor from '$lib/editor/WordCloudEditorPart.svelte';
	import MediaComponent from '$lib/editor/MediaComponent.svelte';
	import Loading from '$lib/editor/Loading.svelte';
	import EdIcon from '$lib/editor/EdIcon.svelte';
	import {
		POINTS_OPTIONS,
		SCORED_TYPES,
		TIME_PRESETS,
		plainText,
		pointsOf,
		typeMeta
	} from '$lib/editor/editor_meta';

	interface Props {
		data: EditorData;
		selected_question: number;
		edit_id: string;
	}

	let {
		data = $bindable(),
		selected_question = $bindable(),
		edit_id = $bindable()
	}: Props = $props();

	let uppyOpen = $state(false);

	const question = $derived(data.questions[selected_question]);
	const type = $derived(question?.type ?? QuizQuestionType.ABCD);
	const meta = $derived(typeMeta(type));
	const scored = $derived(SCORED_TYPES.includes(String(type)));
	const points = $derived(question ? pointsOf(question) : 'standard');
	const time_num = $derived(parseInt(String(question?.time ?? ''), 10));

	const set_time = (value: string | number) => {
		const digits = String(value ?? '')
			.replace(/[^0-9]/g, '')
			.slice(0, 3);
		data.questions[selected_question].time = digits;
	};
	const set_points = (value: QuestionPoints) => {
		data.questions[selected_question].points = value;
	};

	// time is stored as a string; old data may hold a number
	$effect(() => {
		const q = data.questions[selected_question];
		if (q && typeof q.time !== 'string') {
			q.time = q.time === null || q.time === undefined ? '' : String(q.time);
		}
	});

	const position = $derived.by(() => {
		let n = 0;
		for (let i = 0; i <= selected_question; i++) {
			if (data.questions[i]?.type !== QuizQuestionType.SLIDE) n++;
		}
		return n;
	});
	const total = $derived(data.questions.filter((q) => q.type !== QuizQuestionType.SLIDE).length);
</script>

{#key selected_question}
	{#if question && type === QuizQuestionType.SLIDE}
		<section class="bt-glass bt-glass-faint mx-auto flex h-[calc(100dvh-140px)] min-h-[520px] max-w-[1180px] flex-col overflow-hidden p-0">
			<div class="flex items-center gap-4 px-6 pt-5 pb-3">
				<div class="flex-1">
					<span class="bt-eyebrow text-[11px] text-ink-muted">Slide {selected_question + 1}</span>
					<span class="block text-lg font-black uppercase">{plainText(question.question) || 'Slide'}</span>
				</div>
			</div>
			<div class="min-h-0 flex-1">
				{#await import('./slide.svelte')}
					<Loading label="Loading the slide editor" />
				{:then c}
					<c.default bind:data={data.questions[selected_question]} />
				{/await}
			</div>
		</section>
	{:else if question}
		<div class="mx-auto grid max-w-[1180px] gap-5 xl:grid-cols-[minmax(0,1fr)_300px]">
			<div class="flex min-w-0 flex-col gap-5">
				<!-- the question -->
				<section class="bt-glass bt-glass-faint p-5 lg:p-6">
					<div class="mb-3 flex flex-wrap items-center gap-x-3 gap-y-1">
						<span class="bt-eyebrow text-[11px] text-ink-muted">
							Question {position} of {total}
						</span>
						<span class="type-chip">{meta.name}</span>
					</div>
					<div class="q-title relative">
						{#await import('$lib/inline-editor.svelte')}
							<Loading />
						{:then c}
							<c.default bind:text={data.questions[selected_question].question} />
						{/await}
						{#if !plainText(question.question)}
							<span class="q-placeholder" aria-hidden="true">Type your question</span>
						{/if}
					</div>
					<p class="mt-2 text-xs text-ink-muted">
						Select words to make them bold or italic. Keep it short: it is read on a big
						screen and on phones.
					</p>
				</section>

				<!-- the answers -->
				<section class="bt-glass bt-glass-faint p-5 lg:p-6">
					{#if type === QuizQuestionType.ABCD || type === QuizQuestionType.CHECK}
						<ABCDEditor
							bind:data
							{selected_question}
							check_choice={type === QuizQuestionType.CHECK}
						/>
					{:else if type === QuizQuestionType.RANGE}
						<RangeEditor {selected_question} bind:data />
					{:else if type === QuizQuestionType.VOTING}
						<VotingEditor bind:data {selected_question} />
					{:else if type === QuizQuestionType.TEXT}
						<TextEditor bind:data {selected_question} />
					{:else if type === QuizQuestionType.ORDER}
						<OrderEditor bind:data {selected_question} />
					{:else if type === QuizQuestionType.WORD_CLOUD}
						<WordCloudEditor bind:data {selected_question} />
					{/if}
				</section>
			</div>

			<!-- settings of the question -->
			<aside class="flex min-w-0 flex-col gap-5">
				<section class="bt-glass bt-glass-faint p-5">
					<div class="mb-3 flex items-center gap-2">
						<EdIcon name="clock" size={16} class="text-ink-muted" />
						<span class="bt-eyebrow text-[11px] text-ink-muted">Time to answer</span>
					</div>
					<div class="flex flex-wrap gap-1.5" role="group" aria-label="Time presets">
						{#each TIME_PRESETS as preset}
							<button
								type="button"
								class="chip"
								class:chip-on={time_num === preset}
								aria-pressed={time_num === preset}
								onclick={() => set_time(preset)}>{preset}s</button
							>
						{/each}
					</div>
					<label class="mt-3 flex items-center gap-3">
						<input
							type="number"
							inputmode="numeric"
							min="1"
							max="999"
							class="bt-input time-input bt-num"
							value={question.time}
							oninput={(e) => set_time(e.currentTarget.value)}
							aria-label="Time in seconds"
						/>
						<span class="text-sm text-ink-muted">seconds, any value from 1 to 999</span>
					</label>
				</section>

				{#if scored}
					<section class="bt-glass bt-glass-faint p-5">
						<span class="bt-eyebrow mb-3 text-[11px] text-ink-muted">Points</span>
						<div class="seg" role="radiogroup" aria-label="Points">
							{#each POINTS_OPTIONS as opt}
								<button
									type="button"
									role="radio"
									aria-checked={points === opt.value}
									class="seg-item"
									class:seg-on={points === opt.value}
									onclick={() => set_points(opt.value)}
								>
									<span class="block text-[12px] leading-tight font-black uppercase tracking-[0.5px]">{opt.label}</span>
									<span class="block text-xs opacity-75 tabular-nums">{opt.hint}</span>
								</button>
							{/each}
						</div>
						<p class="mt-2 text-xs text-ink-muted">
							{#if points === 'double'}
								Up to 2000 for a fast correct answer, plus the streak bonus.
							{:else if points === 'none'}
								A warm-up: answers are checked but nobody scores.
							{:else}
								Up to 1000 for a fast correct answer, plus the streak bonus.
							{/if}
						</p>
					</section>
				{/if}

				<section class="bt-glass bt-glass-faint p-5">
					<div class="mb-3 flex items-center gap-2">
						<EdIcon name="image" size={16} class="text-ink-muted" />
						<span class="bt-eyebrow text-[11px] text-ink-muted">
							Image{#if type === QuizQuestionType.WORD_CLOUD}, optional{/if}
						</span>
					</div>
					{#if question.image}
						<div class="media relative">
							<MediaComponent
								src={question.image}
								css_classes="max-h-48 w-full rounded-[14px] object-contain"
							/>
							<button
								class="media-remove"
								type="button"
								aria-label="Remove the image"
								title="Remove the image"
								onclick={() => {
									data.questions[selected_question].image = null;
								}}><EdIcon name="trash" size={16} /></button
							>
						</div>
					{:else}
						{#await import('$lib/editor/uploader.svelte')}
							<Loading />
						{:then c}
							<c.default
								bind:modalOpen={uppyOpen}
								bind:data
								{selected_question}
								video_upload={true}
							/>
						{/await}
					{/if}
				</section>

				{#if type !== QuizQuestionType.WORD_CLOUD}
					<section class="bt-glass bt-glass-faint p-5">
						<label class="flex cursor-pointer items-center gap-3">
							<span class="flex-1">
								<span class="block text-sm font-bold">Hide the results</span>
								<span class="block text-xs text-ink-muted">
									Skip the answer chart on the big screen after this question.
								</span>
							</span>
							<input
								type="checkbox"
								class="switch"
								bind:checked={data.questions[selected_question].hide_results}
							/>
						</label>
					</section>
				{/if}
			</aside>
		</div>
	{/if}
{/key}

<style>
	.type-chip {
		padding: 4px 12px;
		border-radius: 999px;
		background: var(--fill-glass-mid);
		font-size: 12px;
		font-weight: 700;
		letter-spacing: 1.5px;
		text-transform: uppercase;
	}
	/* the rich text title (CKEditor balloon) on glass */
	.q-title > :global(div) {
		width: 100%;
		border: 0;
		border-radius: 18px;
	}
	.q-title :global(.ck.ck-editor__editable_inline),
	.q-title :global([contenteditable]) {
		width: 100%;
		min-height: 72px;
		padding: 16px 20px;
		border: 0 !important;
		border-radius: 18px;
		background: var(--fill-glass) !important;
		color: var(--ink) !important;
		font-family: var(--bt-font);
		font-size: 26px;
		font-weight: 900;
		line-height: 1.15;
		text-align: left;
		box-shadow: none !important;
	}
	.q-title :global(.ck.ck-editor__editable_inline.ck-focused),
	.q-title :global([contenteditable]:focus) {
		box-shadow: 0 0 0 3px var(--accent-sky) !important;
		outline: none;
	}
	.q-title :global(.ck.ck-editor__editable_inline > p) {
		margin: 0;
	}
	.q-placeholder {
		position: absolute;
		left: 21px;
		top: 50%;
		transform: translateY(-50%);
		font-size: 26px;
		font-weight: 900;
		color: var(--ink-muted);
		opacity: 0.55;
		pointer-events: none;
	}
	.chip {
		min-width: 48px;
		height: 36px;
		padding: 0 12px;
		border-radius: 999px;
		background: var(--fill-glass);
		font-weight: 700;
		font-size: 14px;
		font-variant-numeric: tabular-nums;
		transition: background-color 120ms ease;
	}
	.chip:hover {
		background: var(--fill-glass-strong);
	}
	.chip-on,
	.chip-on:hover {
		background: linear-gradient(90deg, var(--accent-sky) 0%, var(--accent-green) 100%);
		color: var(--ink-dark);
	}
	.chip:focus-visible,
	.seg-item:focus-visible,
	.media-remove:focus-visible {
		outline: 3px solid var(--accent-sky-tint);
		outline-offset: 2px;
	}
	.time-input {
		width: 96px;
		padding: 10px 14px;
		font-size: 24px;
		border-radius: 14px;
		text-align: center;
	}
	.seg {
		display: grid;
		grid-template-columns: repeat(3, minmax(0, 1fr));
		gap: 4px;
		padding: 4px;
		border-radius: 18px;
		background: var(--fill-deep);
	}
	.seg-item {
		padding: 8px 4px;
		border-radius: 14px;
		text-align: center;
		color: var(--ink-muted);
		transition: background-color 120ms ease;
	}
	.seg-item:hover {
		background: var(--fill-glass);
		color: var(--ink);
	}
	.seg-on,
	.seg-on:hover {
		background: var(--fill-glass-strong);
		color: var(--ink);
	}
	.media {
		border-radius: 14px;
		background: var(--fill-deep);
		padding: 6px;
	}
	.media-remove {
		position: absolute;
		top: 10px;
		right: 10px;
		display: grid;
		place-items: center;
		width: 34px;
		height: 34px;
		border-radius: 999px;
		background: var(--fill-deep);
		color: var(--ink);
	}
	.media-remove:hover {
		background: #6b1d6c;
	}
	.switch {
		appearance: none;
		flex: none;
		position: relative;
		width: 48px;
		height: 28px;
		border-radius: 999px;
		background: var(--fill-glass-strong);
		cursor: pointer;
		transition: background-color 150ms ease;
	}
	.switch::after {
		content: '';
		position: absolute;
		top: 3px;
		left: 3px;
		width: 22px;
		height: 22px;
		border-radius: 999px;
		background: var(--ink);
		transition: transform 150ms ease;
	}
	.switch:checked {
		background: linear-gradient(90deg, var(--accent-sky) 0%, var(--accent-green) 100%);
	}
	.switch:checked::after {
		transform: translateX(20px);
		background: var(--ink-dark);
	}
	.switch:focus-visible {
		outline: 3px solid var(--accent-sky-tint);
		outline-offset: 2px;
	}
</style>
