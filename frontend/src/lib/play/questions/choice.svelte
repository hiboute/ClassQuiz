<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!--
	Single choice (ABCD and VOTING): one big brand tile per answer, shape mark
	on the left. In shapes mode the tiles carry only the shapes, the answers
	being on the big screen.
-->
<script lang="ts">
	import ShapeMark from '$lib/brand/ShapeMark.svelte';
	import { answerStyle } from '$lib/brand/answers';

	interface Props {
		answers: Array<{ answer: string }>;
		shapes: boolean;
		disabled?: boolean;
		onpick: (answer: string, index: number) => void;
	}

	let { answers, shapes, disabled = false, onpick }: Props = $props();

	const size_class = (text: string): string => {
		const n = (text ?? '').length;
		if (n > 60) return 'pa-xs';
		if (n > 34) return 'pa-sm';
		return '';
	};
</script>

<div
	class="pa-list"
	class:pa-grid={shapes}
	class:pa-many={answers.length > 4}
	data-testid="answer-list"
>
	{#each answers as answer, i (i)}
		{@const st = answerStyle(i)}
		<button
			type="button"
			class="{st.className} pa-tile {size_class(answer.answer)}"
			data-testid="answer-tile"
			data-answer-index={i}
			{disabled}
			aria-label={shapes ? `${st.label}` : `${st.label}: ${answer.answer}`}
			onclick={() => onpick(answer.answer, i)}
		>
			<span class="bt-tile-mark pa-mark">
				<ShapeMark index={i} size={shapes ? 72 : 48} />
			</span>
			{#if !shapes}
				<span class="pa-label">{answer.answer}</span>
			{/if}
		</button>
	{/each}
</div>

<style>
	.pa-list {
		flex: 1 1 auto;
		display: flex;
		flex-direction: column;
		justify-content: flex-end;
		gap: 12px;
		min-height: 0;
	}
	.pa-tile {
		flex: 1 1 0;
		min-height: 112px;
		max-height: 150px;
		width: 100%;
		padding: 0 18px 0 16px;
		gap: 18px;
		font-size: 24px;
		text-align: left;
		cursor: pointer;
		user-select: none;
		-webkit-user-select: none;
		transition:
			transform 120ms ease,
			filter 120ms ease;
	}
	.pa-tile:active:not(:disabled) {
		transform: scale(0.97);
	}
	.pa-tile:focus-visible {
		outline: 3px solid var(--ink);
		outline-offset: 3px;
	}
	.pa-tile:disabled {
		cursor: default;
	}
	.pa-sm {
		font-size: 19px;
	}
	.pa-xs {
		font-size: 16px;
		line-height: 1.12;
	}
	.pa-mark {
		width: 80px;
		height: 80px;
	}
	.pa-label {
		flex: 1 1 auto;
		min-width: 0;
		overflow-wrap: anywhere;
		display: -webkit-box;
		-webkit-line-clamp: 3;
		line-clamp: 3;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
	/* more than four answers: shorter tiles so they still fit */
	.pa-many .pa-tile {
		min-height: 76px;
	}
	.pa-many .pa-mark {
		width: 56px;
		height: 56px;
	}

	/* shapes mode: a 2x2 grid of big shapes */
	.pa-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		grid-auto-rows: minmax(150px, 1fr);
		align-content: stretch;
	}
	.pa-grid .pa-tile {
		max-height: none;
		justify-content: center;
		padding: 0;
	}
	.pa-grid .pa-mark {
		width: 112px;
		height: 112px;
		background: transparent;
		color: inherit;
	}
</style>
