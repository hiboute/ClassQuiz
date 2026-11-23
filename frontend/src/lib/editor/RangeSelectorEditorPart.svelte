<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import type { EditorData, RangeQuizAnswer } from '../quiz_types';
	import Loading from '$lib/editor/Loading.svelte';

	interface Props {
		selected_question: number;
		data: EditorData;
	}

	let { selected_question, data = $bindable() }: Props = $props();

	const initial = data.questions[selected_question].answers as RangeQuizAnswer;
	if (!initial || initial.max === undefined || initial.min_correct === undefined) {
		data.questions[selected_question].answers = {
			max: 10,
			min: 0,
			max_correct: 7,
			min_correct: 3
		};
	}

	const answer = $derived(data.questions[selected_question].answers as RangeQuizAnswer);
	let range_arr = $state([
		(data.questions[selected_question].answers as RangeQuizAnswer).min_correct,
		(data.questions[selected_question].answers as RangeQuizAnswer).max_correct
	]);

	$effect(() => {
		const a = data.questions[selected_question].answers as RangeQuizAnswer;
		a.min_correct = range_arr[0];
		a.max_correct = range_arr[1];
	});

	const set_bound = (key: 'min' | 'max', raw: string) => {
		const a = data.questions[selected_question].answers as RangeQuizAnswer;
		const n = parseInt(raw, 10);
		a[key] = Number.isFinite(n) ? n : 0;
		// keep the correct range inside the bounds
		range_arr = [
			Math.min(Math.max(range_arr[0], a.min), a.max),
			Math.max(Math.min(range_arr[1], a.max), a.min)
		];
	};

	function sleep(ms: number) {
		return new Promise((resolve) => setTimeout(resolve, ms));
	}
</script>

<div class="mb-4 flex flex-wrap items-center gap-x-4 gap-y-2">
	<span class="bt-eyebrow text-[11px] text-ink-muted">Slider</span>
	<span class="text-xs text-ink-muted">
		Set the ends of the slider, then drag the two handles over the values that count as
		correct.
	</span>
</div>

<div class="grid grid-cols-2 gap-3 sm:grid-cols-4">
	<label class="field">
		<span class="bt-eyebrow text-[10px] text-ink-muted">Slider from</span>
		<input
			type="number"
			class="bt-input num-input bt-num"
			value={answer.min}
			max={answer.max - 2}
			oninput={(e) => set_bound('min', e.currentTarget.value)}
		/>
	</label>
	<label class="field">
		<span class="bt-eyebrow text-[10px] text-ink-muted">Slider to</span>
		<input
			type="number"
			class="bt-input num-input bt-num"
			value={answer.max}
			min={answer.min + 2}
			oninput={(e) => set_bound('max', e.currentTarget.value)}
		/>
	</label>
	<div class="field field-correct">
		<span class="bt-eyebrow text-[10px]">Correct from</span>
		<span class="bt-num text-[28px]">{range_arr[0]}</span>
	</div>
	<div class="field field-correct">
		<span class="bt-eyebrow text-[10px]">Correct to</span>
		<span class="bt-num text-[28px]">{range_arr[1]}</span>
	</div>
</div>

<div class="slider mt-6 px-2 pb-2">
	{#await import('svelte-range-slider-pips')}
		<Loading />
	{:then c}
		{#await sleep(100)}
			<Loading />
		{:then _}
			<c.default
				bind:values={range_arr}
				min={answer.min}
				max={answer.max}
				pips
				float
				all="label"
				range
			/>
		{/await}
	{/await}
</div>

<style>
	.field {
		display: flex;
		flex-direction: column;
		gap: 8px;
		padding: 12px;
		border-radius: 16px;
		background: var(--fill-glass);
	}
	.field-correct {
		background: linear-gradient(120deg, rgba(39, 190, 130, 0.35), rgba(93, 181, 223, 0.35));
		justify-content: space-between;
	}
	.num-input {
		padding: 8px 12px;
		border-radius: 12px;
		font-size: 24px;
	}
	.slider {
		--range-slider: rgba(255, 255, 255, 0.24);
		--range-handle-inactive: #feffff;
		--range-handle: #feffff;
		--range-handle-focus: #9ed3ec;
		--range-handle-border: #feffff;
		--range-range-inactive: #27be82;
		--range-range: #27be82;
		--range-float-inactive: #27be82;
		--range-float: #27be82;
		--range-float-text: #000000;
		--range-pip: rgba(254, 255, 255, 0.5);
		--range-pip-text: #cbd5e1;
		--range-pip-active: #feffff;
		--range-pip-active-text: #feffff;
		--range-pip-hover: #feffff;
		--range-pip-hover-text: #feffff;
		--range-pip-in-range: #73e2b6;
		--range-pip-in-range-text: #73e2b6;
		font-family: var(--bt-font);
	}
</style>
