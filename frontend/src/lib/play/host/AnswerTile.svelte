<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!--
	One brand answer tile for the big screen: gradient, shape mark, text that
	shrinks to fit two lines. Always the brand tiles, never the quiz colours.
-->
<script lang="ts">
	import ShapeMark from '$lib/brand/ShapeMark.svelte';
	import { answerStyle } from '$lib/brand/answers';
	import { fitText } from './fit';

	interface Props {
		index: number;
		text: string;
		height?: number;
		fontMax?: number;
		dim?: boolean;
		correct?: boolean;
		/** right side figure, such as a vote count */
		figure?: string | null;
	}

	let {
		index,
		text,
		height = 196,
		fontMax = 52,
		dim = false,
		correct = false,
		figure = null
	}: Props = $props();

	const style = $derived(answerStyle(index));
	const mark = $derived(Math.max(64, Math.min(136, height - 60)));
</script>

<div
	class="tile {style.className}"
	class:bt-tile-dim={dim}
	class:tile--correct={correct}
	style="height: {height}px; gap: {Math.round(mark / 4)}px"
>
	<span class="h-mark" style="width: {mark}px; height: {mark}px">
		<ShapeMark index={index} size={Math.round(mark * 0.59)} color="#feffff" title={style.label} />
	</span>
	<span class="tile-text" use:fitText={{ max: fontMax, min: 24, lines: 2, key: text + height }}
		>{text}</span
	>
	{#if figure !== null}
		<span class="tile-figure h-num">{figure}</span>
	{/if}
	{#if correct}
		<span class="tile-check" aria-label="Correct answer">
			<svg viewBox="0 0 24 24" width="40" height="40" aria-hidden="true">
				<path
					d="M5 12.5l4.5 4.5L19 7.5"
					fill="none"
					stroke="currentColor"
					stroke-width="3.4"
					stroke-linecap="round"
					stroke-linejoin="round"
				/>
			</svg>
		</span>
	{/if}
</div>

<style>
	.tile {
		padding: 0 40px 0 30px;
		transition:
			opacity 500ms ease,
			transform 500ms ease;
	}
	.tile--correct {
		transform: scale(1.015);
		box-shadow: 0 18px 60px -12px rgba(0, 0, 0, 0.45);
	}
	.tile-text {
		flex: 1;
		min-width: 0;
		font-size: 52px;
		line-height: 1.08;
		overflow: hidden;
		overflow-wrap: anywhere;
	}
	.tile-figure {
		flex: none;
		font-size: 64px;
		line-height: 1;
	}
	.tile-check {
		flex: none;
		width: 64px;
		height: 64px;
		border-radius: 50%;
		display: grid;
		place-items: center;
		background: var(--fill-deep);
		color: var(--accent-green-tint);
	}
</style>
