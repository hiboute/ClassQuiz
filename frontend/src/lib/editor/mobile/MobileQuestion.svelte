<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!--
	Phone question editor: one question on a full screen in its colour world.
	Back arrow, page dots (problems in orchid), type chip, question text,
	answers, time chips, points, image. Previous and Next in the bottom bar,
	or a horizontal swipe on the page.
-->
<script lang="ts">
	import type { EditorData, QuestionPoints } from '$lib/quiz_types';
	import { QuizQuestionType } from '$lib/quiz_types';
	import { fly } from 'svelte/transition';
	import World from '$lib/brand/World.svelte';
	import { questionWorld } from '$lib/brand/answers';
	import EdIcon from '$lib/editor/EdIcon.svelte';
	import Loading from '$lib/editor/Loading.svelte';
	import MediaComponent from '$lib/editor/MediaComponent.svelte';
	import RangeEditor from '$lib/editor/RangeSelectorEditorPart.svelte';
	import TextEditor from '$lib/editor/TextEditorPart.svelte';
	import OrderEditor from '$lib/editor/OrderEditorPart.svelte';
	import WordCloudEditor from '$lib/editor/WordCloudEditorPart.svelte';
	import MobileAnswers from './MobileAnswers.svelte';
	import Sheet from './Sheet.svelte';
	import SaveState from './SaveState.svelte';
	import ProblemChip from './ProblemChip.svelte';
	import {
		SCORED_TYPES,
		TIME_PRESETS,
		plainText,
		pointsOf,
		questionTypeName
	} from '$lib/editor/editor_meta';

	interface Props {
		data: EditorData;
		index: number;
		edit_id: string;
		issues: (string | null)[];
		problem_count: number;
		save_tone: 'bad' | 'ok' | 'busy';
		save_label: string;
		onback: () => void;
		ongo: (index: number) => void;
		onadd: () => void;
		onchangetype: () => void;
		onproblems: () => void;
		onmove: (from: number, to: number) => void;
		onduplicate: (index: number) => void;
		ondelete: (index: number) => void;
	}

	let {
		data = $bindable(),
		index,
		edit_id = $bindable(),
		issues,
		problem_count,
		save_tone,
		save_label,
		onback,
		ongo,
		onadd,
		onchangetype,
		onproblems,
		onmove,
		onduplicate,
		ondelete
	}: Props = $props();

	const question = $derived(data.questions[index]);
	const type = $derived(question?.type ?? QuizQuestionType.ABCD);
	const is_slide = $derived(type === QuizQuestionType.SLIDE);
	const scored = $derived(SCORED_TYPES.includes(String(type)));
	const points = $derived(question ? pointsOf(question) : 'standard');
	const time_num = $derived(parseInt(String(question?.time ?? ''), 10));
	const last = $derived(index >= data.questions.length - 1);
	const issue = $derived(issues[index] ?? null);

	const position = $derived.by(() => {
		let n = 0;
		for (let i = 0; i <= index; i++) {
			if (data.questions[i]?.type !== QuizQuestionType.SLIDE) n++;
		}
		return n;
	});
	const total = $derived(data.questions.filter((q) => q.type !== QuizQuestionType.SLIDE).length);

	// direction of the last move, so the new question slides in from that side
	let dir = $state(0);
	const go = (to: number) => {
		if (to < 0 || to >= data.questions.length || to === index) return;
		dir = to > index ? 1 : -1;
		ongo(to);
	};

	let custom_open = $state(false);
	let more_open = $state(false);
	let uppy_open = $state(false);
	$effect(() => {
		// a time outside the presets opens the custom field
		if (question && !is_slide && !TIME_PRESETS.includes(time_num as never)) custom_open = true;
	});

	// time is stored as a string; old data may hold a number
	$effect(() => {
		const q = data.questions[index];
		if (q && typeof q.time !== 'string') {
			q.time = q.time === null || q.time === undefined ? '' : String(q.time);
		}
	});

	const set_time = (value: string | number) => {
		data.questions[index].time = String(value ?? '')
			.replace(/[^0-9]/g, '')
			.slice(0, 3);
	};
	const set_points = (value: QuestionPoints) => {
		data.questions[index].points = value;
	};
	const POINTS: { value: QuestionPoints; label: string; hint: string }[] = [
		{ value: 'standard', label: 'Standard', hint: '1000' },
		{ value: 'double', label: 'Double', hint: '2000' },
		{ value: 'none', label: 'None', hint: '0' }
	];

	// horizontal swipe on the page moves between questions
	let touch: { x: number; y: number; t: number } | null = null;
	const NO_SWIPE =
		'input, textarea, select, [contenteditable], .ck, .noswipe, .rangeSlider, .slide-box';
	const on_touch_start = (e: TouchEvent) => {
		const target = e.target as HTMLElement;
		touch =
			e.touches.length === 1 && !target.closest(NO_SWIPE)
				? { x: e.touches[0].clientX, y: e.touches[0].clientY, t: Date.now() }
				: null;
	};
	const on_touch_end = (e: TouchEvent) => {
		if (!touch) return;
		const dx = e.changedTouches[0].clientX - touch.x;
		const dy = e.changedTouches[0].clientY - touch.y;
		const quick = Date.now() - touch.t < 700;
		touch = null;
		if (quick && Math.abs(dx) > 70 && Math.abs(dx) > Math.abs(dy) * 1.8) {
			go(dx < 0 ? index + 1 : index - 1);
		}
	};
</script>

<World world={questionWorld(index)} class="mq-screen">
	<header class="top">
		<button type="button" class="ib" aria-label="Back to the question list" onclick={onback}>
			<EdIcon name="back" size={22} />
		</button>
		<span class="lbl flex-1 text-center text-ink">
			{#if is_slide}Slide{:else}Question {position} of {total}{/if}
		</span>
		{#if problem_count > 0}
			<ProblemChip count={problem_count} onclick={onproblems} />
		{/if}
		<button
			type="button"
			class="ib"
			aria-label="More: move, duplicate, delete"
			onclick={() => (more_open = true)}
		>
			<EdIcon name="more" size={22} stroke={3.2} />
		</button>
	</header>
	<div class="pager" aria-hidden="true">
		{#each data.questions as _q, i}
			<i class:on={i === index} class:warn={i !== index && issues[i]}></i>
		{/each}
	</div>

	<div
		class="scroll"
		role="presentation"
		ontouchstart={on_touch_start}
		ontouchend={on_touch_end}
	>
		{#key index}
			<div class="wrap" in:fly={{ x: dir * 48, duration: 200 }}>
				{#if question && is_slide}
					<p class="note">
						A content slide shows text and shapes between questions. Slides are easier to
						lay out on a bigger screen.
					</p>
					<div class="slide-box">
						{#await import('$lib/editor/slide.svelte')}
							<Loading label="Loading the slide editor" />
						{:then c}
							<c.default bind:data={data.questions[index]} />
						{/await}
					</div>
				{:else if question}
					<button type="button" class="type-chip" onclick={onchangetype}>
						{questionTypeName(question)}
						<EdIcon name="down" size={16} stroke={2.5} />
					</button>

					<div class="field q-title relative">
						{#await import('$lib/inline-editor.svelte')}
							<Loading />
						{:then c}
							<c.default bind:text={data.questions[index].question} />
						{/await}
						{#if !plainText(question.question)}
							<span class="q-placeholder" aria-hidden="true">Type your question</span>
						{/if}
					</div>
					{#if issue}
						<p class="issue"><EdIcon name="warn" size={15} /> {issue}</p>
					{/if}

					<section class="mt-5">
						{#if type === QuizQuestionType.ABCD || type === QuizQuestionType.CHECK || type === QuizQuestionType.VOTING}
							<MobileAnswers bind:question={data.questions[index]} />
						{:else}
							<div class="parts">
								{#if type === QuizQuestionType.RANGE}
									<RangeEditor selected_question={index} bind:data />
								{:else if type === QuizQuestionType.TEXT}
									<TextEditor bind:data selected_question={index} />
								{:else if type === QuizQuestionType.ORDER}
									<OrderEditor bind:data selected_question={index} />
								{:else if type === QuizQuestionType.WORD_CLOUD}
									<WordCloudEditor bind:data selected_question={index} />
								{/if}
							</div>
						{/if}
					</section>

					<div class="sec-head">
						<span class="lbl">Time to answer</span>
						<button
							type="button"
							class="link"
							aria-expanded={custom_open}
							onclick={() => (custom_open = !custom_open)}>Custom</button
						>
					</div>
					<div class="chips noswipe" role="group" aria-label="Time presets">
						{#each TIME_PRESETS as preset}
							<button
								type="button"
								class="tchip"
								class:tchip-on={time_num === preset}
								aria-pressed={time_num === preset}
								onclick={() => set_time(preset)}>{preset}s</button
							>
						{/each}
					</div>
					{#if custom_open}
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
							<span class="text-sm text-ink-muted">seconds, 1 to 999</span>
						</label>
					{/if}

					{#if scored}
						<div class="sec-head"><span class="lbl">Points</span></div>
						<div class="seg" role="radiogroup" aria-label="Points">
							{#each POINTS as opt}
								<button
									type="button"
									role="radio"
									aria-checked={points === opt.value}
									class="seg-item"
									class:seg-on={points === opt.value}
									onclick={() => set_points(opt.value)}
								>
									<span class="seg-label">{opt.label}</span>
									<span class="seg-hint">{opt.hint}</span>
								</button>
							{/each}
						</div>
					{/if}

					<div class="sec-head">
						<span class="lbl">Image{#if type === QuizQuestionType.WORD_CLOUD}, optional{/if}</span>
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
								onclick={() => {
									data.questions[index].image = null;
								}}><EdIcon name="trash" size={18} /></button
							>
						</div>
					{:else}
						<div class="uploader">
							{#await import('$lib/editor/uploader.svelte')}
								<Loading />
							{:then c}
								<c.default
									bind:modalOpen={uppy_open}
									bind:data
									selected_question={index}
									video_upload={true}
								/>
							{/await}
						</div>
					{/if}

					{#if type !== QuizQuestionType.WORD_CLOUD}
						<label class="switch-row">
							<span class="flex-1">
								<span class="block text-[15px] font-bold">Hide the results</span>
								<span class="block text-[13px] text-ink-muted">
									Skip the answer chart on the big screen after this question.
								</span>
							</span>
							<input
								type="checkbox"
								class="switch"
								bind:checked={data.questions[index].hide_results}
							/>
						</label>
					{/if}
				{/if}
			</div>
		{/key}
	</div>

	<footer class="bar">
		<button
			type="button"
			class="ib ib-lg"
			aria-label="Previous question"
			disabled={index === 0}
			onclick={() => go(index - 1)}
		>
			<EdIcon name="left" size={24} />
		</button>
		<div class="min-w-0 flex-1 text-center">
			<SaveState tone={save_tone} label={save_label} center />
			<span class="block truncate text-[12px] text-ink-muted">
				{last ? 'Last one' : 'Swipe for the next one'}
			</span>
		</div>
		{#if last}
			<button type="button" class="bt-btn-primary bar-btn" onclick={onadd}>
				<EdIcon name="plus" size={20} stroke={3} /> Question
			</button>
		{:else}
			<button type="button" class="bt-btn-primary bar-btn" onclick={() => go(index + 1)}>
				Next <EdIcon name="right" size={20} stroke={3} />
			</button>
		{/if}
	</footer>
</World>

{#if more_open}
	<Sheet
		kicker={is_slide ? 'Slide' : `Question ${position}`}
		title="Question actions"
		onclose={() => (more_open = false)}
	>
		<div class="flex flex-col gap-2">
			<button
				type="button"
				class="act"
				disabled={index === 0}
				onclick={() => {
					more_open = false;
					dir = -1;
					onmove(index, index - 1);
				}}><EdIcon name="up" size={20} /> Move earlier</button
			>
			<button
				type="button"
				class="act"
				disabled={last}
				onclick={() => {
					more_open = false;
					dir = 1;
					onmove(index, index + 1);
				}}><EdIcon name="down" size={20} /> Move later</button
			>
			<button
				type="button"
				class="act"
				onclick={() => {
					more_open = false;
					dir = 1;
					onduplicate(index);
				}}><EdIcon name="copy" size={20} /> Duplicate</button
			>
			<button
				type="button"
				class="act act-danger"
				onclick={() => {
					more_open = false;
					ondelete(index);
				}}><EdIcon name="trash" size={20} /> Delete</button
			>
		</div>
	</Sheet>
{/if}

<style>
	:global(.mq-screen) {
		position: fixed !important;
		inset: 0;
		z-index: 40;
		display: flex;
		flex-direction: column;
		height: 100dvh;
	}
	.top {
		display: flex;
		align-items: center;
		gap: 8px;
		padding: max(8px, env(safe-area-inset-top)) 16px 0;
		min-height: 60px;
	}
	.lbl {
		font-size: 12px;
		letter-spacing: 3px;
		text-transform: uppercase;
		color: var(--ink-muted);
	}
	.top .lbl {
		color: var(--ink);
	}
	.ib {
		display: inline-grid;
		place-items: center;
		flex: none;
		width: 44px;
		height: 44px;
		border-radius: 999px;
		background: var(--fill-glass-mid);
		color: var(--ink);
	}
	.ib:disabled {
		opacity: 0.4;
	}
	.ib-lg {
		width: 56px;
		height: 56px;
	}
	.ib:focus-visible,
	.type-chip:focus-visible,
	.tchip:focus-visible,
	.seg-item:focus-visible,
	.link:focus-visible,
	.act:focus-visible {
		outline: 3px solid var(--accent-sky-tint);
		outline-offset: 2px;
	}
	.pager {
		display: flex;
		justify-content: center;
		gap: 6px;
		margin: 4px 16px 10px;
	}
	.pager i {
		display: block;
		flex: 0 1 6px;
		min-width: 3px;
		height: 6px;
		border-radius: 9px;
		background: rgba(255, 255, 255, 0.3);
	}
	.pager i.warn {
		background: var(--accent-orchid);
	}
	.pager i.on {
		flex: 0 0 22px;
		background: var(--ink);
	}
	.scroll {
		min-height: 0;
		flex: 1;
		overflow-x: hidden;
		overflow-y: auto;
		overscroll-behavior: contain;
	}
	.wrap {
		padding: 0 16px 24px;
	}
	.type-chip {
		display: inline-flex;
		align-items: center;
		gap: 8px;
		min-height: 44px;
		padding: 0 16px;
		border-radius: 999px;
		background: var(--fill-glass-mid);
		font-size: 13px;
		font-weight: 700;
		letter-spacing: 2px;
		text-transform: uppercase;
	}
	.field {
		margin-top: 12px;
	}
	/* the rich text question (CKEditor balloon) */
	.q-title > :global(div) {
		width: 100%;
		border: 0;
		border-radius: 22px;
	}
	.q-title :global(.ck.ck-editor__editable_inline),
	.q-title :global([contenteditable]) {
		width: 100%;
		min-height: 96px;
		padding: 14px 16px;
		border: 0 !important;
		border-radius: 22px;
		background: var(--fill-glass-mid) !important;
		color: var(--ink) !important;
		font-family: var(--bt-font);
		font-size: 19px;
		font-weight: 700;
		line-height: 1.28;
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
		left: 17px;
		top: 15px;
		font-size: 19px;
		font-weight: 700;
		color: var(--ink);
		opacity: 0.5;
		pointer-events: none;
	}
	.issue {
		display: flex;
		align-items: center;
		gap: 8px;
		margin-top: 10px;
		font-size: 14px;
		color: var(--accent-orchid-tint);
	}
	.sec-head {
		display: flex;
		align-items: center;
		justify-content: space-between;
		min-height: 44px;
		margin-top: 12px;
	}
	.link {
		min-height: 44px;
		padding: 0 4px;
		font-size: 14px;
		font-weight: 700;
		color: var(--accent-sky-tint);
	}
	.chips {
		display: flex;
		gap: 8px;
		margin: 0 -16px;
		padding: 0 16px 4px;
		overflow-x: auto;
		scrollbar-width: none;
		overscroll-behavior-x: contain;
	}
	.chips::-webkit-scrollbar {
		display: none;
	}
	.tchip {
		flex: none;
		min-width: 60px;
		height: 48px;
		padding: 0 14px;
		border-radius: 999px;
		background: var(--fill-glass-mid);
		font-size: 16px;
		font-weight: 700;
		font-variant-numeric: tabular-nums;
	}
	.tchip-on {
		background: linear-gradient(90deg, var(--accent-sky), var(--accent-green));
		color: var(--ink-dark);
		font-weight: 900;
	}
	.time-input {
		width: 104px;
		padding: 10px 14px;
		border-radius: 16px;
		font-size: 22px;
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
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 52px;
		border-radius: 14px;
		color: var(--ink-muted);
	}
	.seg-on {
		background: var(--fill-glass-strong);
		color: var(--ink);
	}
	.seg-label {
		font-size: 13px;
		font-weight: 900;
		letter-spacing: 1.5px;
		text-transform: uppercase;
	}
	.seg-hint {
		margin-top: 2px;
		font-size: 12px;
		font-variant-numeric: tabular-nums;
		opacity: 0.8;
	}
	.media {
		padding: 6px;
		border-radius: 18px;
		background: var(--fill-deep);
	}
	.media-remove {
		position: absolute;
		top: 10px;
		right: 10px;
		display: grid;
		place-items: center;
		width: 44px;
		height: 44px;
		border-radius: 999px;
		background: var(--fill-deep);
	}
	.switch-row {
		display: flex;
		align-items: center;
		gap: 12px;
		min-height: 64px;
		margin-top: 16px;
		padding: 12px 14px;
		border-radius: 18px;
		background: var(--fill-glass);
		cursor: pointer;
	}
	.switch {
		appearance: none;
		flex: none;
		position: relative;
		width: 52px;
		height: 32px;
		border-radius: 999px;
		background: var(--fill-glass-strong);
		cursor: pointer;
	}
	.switch::after {
		content: '';
		position: absolute;
		top: 4px;
		left: 4px;
		width: 24px;
		height: 24px;
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
	.note {
		margin: 4px 0 12px;
		font-size: 14px;
		color: var(--ink-muted);
	}
	.slide-box {
		height: 62dvh;
		min-height: 380px;
		border-radius: 22px;
		background: var(--fill-glass);
		overflow: hidden;
	}
	/* the shared answer parts, sized for thumbs */
	.parts :global(input) {
		font-size: max(16px, 1em);
	}
	.parts :global(button.tool),
	.parts :global(button.remove),
	.parts :global(button.case) {
		min-width: 44px;
		height: 44px;
	}
	.parts :global(button.add) {
		height: 48px;
	}
	.parts :global(.num-input) {
		min-height: 48px;
		font-size: 22px;
	}
	/* type answer: the case toggle keeps only its "Aa" mark */
	.parts :global(button.case) {
		justify-content: center;
		padding: 0;
		font-size: 0;
		gap: 0;
	}
	.parts :global(button.case > span) {
		font-size: 15px;
	}
	/* slider: label only the ends and the two handles */
	.parts :global(.rsPip:not(.rsPip--first):not(.rsPip--last):not(.rsSelected) .rsPipVal) {
		display: none;
	}
	/* the slide toolbar wraps on a phone */
	.slide-box :global(button.tbtn),
	.slide-box :global(button.ebtn) {
		min-width: 44px;
		min-height: 44px;
	}
	.slide-box :global(.toolbar) {
		display: flex;
		flex-wrap: wrap;
		justify-content: space-between;
		margin-top: 12px;
	}
	.uploader :global(button) {
		min-height: 44px;
	}
	.bar {
		display: flex;
		align-items: center;
		gap: 10px;
		padding: 18px 16px max(14px, env(safe-area-inset-bottom));
		background: linear-gradient(
			to bottom,
			transparent 0,
			color-mix(in srgb, var(--ground) 88%, transparent) 30%,
			color-mix(in srgb, var(--ground) 96%, transparent)
		);
	}
	.bar-btn {
		min-height: 56px;
		padding: 0 20px;
		font-size: 16px;
	}
	.act {
		display: flex;
		align-items: center;
		gap: 14px;
		min-height: 56px;
		padding: 0 18px;
		border-radius: 18px;
		background: var(--fill-glass);
		font-size: 16px;
		font-weight: 700;
		text-align: left;
	}
	.act:disabled {
		opacity: 0.4;
	}
	.act-danger {
		color: #ffb3d9;
	}
</style>
