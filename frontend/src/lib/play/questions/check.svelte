<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!--
	Multiple choice (CHECK): tap tiles to select or unselect them, then lock in.
	The answer sent is the selected indexes as one string, e.g. "02".
-->
<script lang="ts">
	import ShapeMark from '$lib/brand/ShapeMark.svelte';
	import { answerStyle } from '$lib/brand/answers';

	interface Props {
		answers: Array<{ answer: string }>;
		shapes: boolean;
		disabled?: boolean;
		onsubmit: (answer: string, label: string) => void;
	}

	let { answers, shapes, disabled = false, onsubmit }: Props = $props();

	// svelte-ignore state_referenced_locally
	let selected: boolean[] = $state(answers.map(() => false));
	const count = $derived(selected.filter(Boolean).length);

	const toggle = (i: number) => {
		if (disabled) return;
		selected[i] = !selected[i];
	};

	const submit = () => {
		if (disabled || count === 0) return;
		let answer = '';
		const labels: string[] = [];
		selected.forEach((on, i) => {
			if (on) {
				answer += String(i);
				labels.push(shapes ? answerStyle(i).label : answers[i].answer);
			}
		});
		onsubmit(answer, labels.join(', '));
	};
</script>

<div class="pc-wrap">
	<div class="pc-list" class:pc-grid={shapes} data-testid="answer-list">
		{#each answers as answer, i (i)}
			{@const st = answerStyle(i)}
			<button
				type="button"
				class="{st.className} pc-tile"
				class:pc-off={!selected[i]}
				data-testid="answer-tile"
				data-answer-index={i}
				aria-pressed={selected[i]}
				aria-label={shapes ? st.label : `${st.label}: ${answer.answer}`}
				{disabled}
				onclick={() => toggle(i)}
			>
				<span class="bt-tile-mark pc-mark">
					<ShapeMark index={i} size={shapes ? 56 : 40} />
				</span>
				{#if !shapes}
					<span class="pc-label">{answer.answer}</span>
				{/if}
				<span class="pc-check" aria-hidden="true">
					{#if selected[i]}
						<svg viewBox="0 0 24 24" width="22" height="22"
							><path
								d="M5 12.5l4.2 4.2L19 7"
								fill="none"
								stroke="currentColor"
								stroke-width="3.2"
								stroke-linecap="round"
								stroke-linejoin="round"
							/></svg
						>
					{/if}
				</span>
			</button>
		{/each}
	</div>
	<button
		type="button"
		class="bt-btn-primary bt-btn-lg bt-btn-block pc-submit"
		data-testid="answer-submit"
		disabled={disabled || count === 0}
		onclick={submit}
	>
		{count === 0 ? 'Pick one or more' : `Lock in ${count}`}
	</button>
</div>

<style>
	.pc-wrap {
		flex: 1 1 auto;
		display: flex;
		flex-direction: column;
		justify-content: flex-end;
		gap: 12px;
		min-height: 0;
	}
	.pc-list {
		display: flex;
		flex-direction: column;
		gap: 10px;
	}
	.pc-tile {
		width: 100%;
		min-height: 96px;
		padding: 0 16px 0 14px;
		gap: 16px;
		font-size: 21px;
		text-align: left;
		cursor: pointer;
		user-select: none;
		-webkit-user-select: none;
		transition:
			opacity 120ms ease,
			transform 120ms ease;
	}
	.pc-tile:active:not(:disabled) {
		transform: scale(0.98);
	}
	.pc-tile:focus-visible {
		outline: 3px solid var(--ink);
		outline-offset: 3px;
	}
	.pc-off {
		opacity: 0.55;
	}
	.pc-mark {
		width: 68px;
		height: 68px;
	}
	.pc-label {
		flex: 1 1 auto;
		min-width: 0;
		overflow-wrap: anywhere;
	}
	.pc-check {
		flex: none;
		margin-left: auto;
		width: 34px;
		height: 34px;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--fill-deep);
		color: var(--ink);
		box-shadow: inset 0 0 0 2px rgba(254, 255, 255, 0.5);
	}
	.pc-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		grid-auto-rows: 140px;
	}
	.pc-grid .pc-tile {
		justify-content: center;
		padding: 0;
	}
	.pc-grid .pc-mark {
		width: 90px;
		height: 90px;
		background: transparent;
		color: inherit;
	}
	.pc-grid .pc-check {
		position: absolute;
		top: 10px;
		right: 10px;
	}
</style>
