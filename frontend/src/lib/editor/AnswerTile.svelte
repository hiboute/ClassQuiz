<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!--
	One answer in the editor, painted as the brand answer tile it becomes in the
	game (gradient, ink and shape mark by index). An author's own colour stays in
	the data (answer.color) and shows as a small swatch only.
-->
<script lang="ts">
	import ShapeMark from '$lib/brand/ShapeMark.svelte';
	import { answerStyle } from '$lib/brand/answers';
	import EdIcon from '$lib/editor/EdIcon.svelte';
	import { isCustomColor } from '$lib/editor/editor_meta';

	interface Props {
		answer: { answer: string; right?: boolean; color?: string | null };
		index: number;
		/** show the correct-answer toggle (quiz types) */
		correct_toggle?: boolean;
		/** tick-box look for multiple select */
		check_style?: boolean;
		placeholder?: string;
		removable?: boolean;
		onremove?: () => void;
	}

	let {
		answer = $bindable(),
		index,
		correct_toggle = true,
		check_style = false,
		placeholder,
		removable = true,
		onremove
	}: Props = $props();

	const style = $derived(answerStyle(index));
	const custom = $derived(isCustomColor(answer.color));
</script>

<div
	class="tile {style.className}"
	class:tile-right={correct_toggle && answer.right}
	class:tile-wrong={correct_toggle && !answer.right}
>
	<span class="bt-tile-mark mark"><ShapeMark index={index} size={22} /></span>
	<span class="flex min-w-0 flex-1 flex-col self-stretch justify-center">
		{#if correct_toggle && answer.right}
			<span class="right-label">Correct answer</span>
		{/if}
		<input
			bind:value={answer.answer}
			type="text"
			class="tile-input"
			placeholder={placeholder ?? `Answer ${index + 1}`}
			aria-label="Answer {index + 1} ({style.label})"
			maxlength="200"
		/>
	</span>
	<span class="tools">
		<label
			class="tool swatch"
			title={custom
				? 'Custom colour (right-click to remove). Game screens keep the brand tiles.'
				: 'Custom colour (optional). Game screens keep the brand tiles.'}
			oncontextmenu={(e) => {
				e.preventDefault();
				answer.color = undefined;
			}}
		>
			{#if custom}
				<span class="dot" style="background:{answer.color}"></span>
			{:else}
				<EdIcon name="palette" size={15} />
			{/if}
			<input
				type="color"
				class="sr-only"
				value={custom ? answer.color : '#ffffff'}
				onchange={(e) => (answer.color = e.currentTarget.value)}
			/>
		</label>
		{#if removable}
			<button type="button" class="tool" aria-label="Remove answer {index + 1}" title="Remove" onclick={() => onremove?.()}>
				<EdIcon name="x" size={16} />
			</button>
		{/if}
	</span>
	{#if correct_toggle}
		<button
			type="button"
			class="correct"
			class:correct-on={answer.right}
			class:correct-box={check_style}
			aria-pressed={answer.right}
			aria-label={answer.right ? 'Correct answer, click to mark as wrong' : 'Wrong answer, click to mark as correct'}
			title={answer.right ? 'Correct' : 'Mark as correct'}
			onclick={() => (answer.right = !answer.right)}
		>
			<EdIcon name="check" size={20} stroke={3} />
		</button>
	{/if}
</div>

<style>
	.tile {
		min-height: 92px;
		padding: 14px 14px 14px 14px;
		padding-right: 12px;
		gap: 14px;
		text-transform: none;
		transition:
			box-shadow 120ms ease,
			filter 120ms ease;
	}
	.tile-wrong {
		filter: saturate(0.8);
	}
	.tile-right {
		box-shadow:
			inset 0 0 0 3px var(--ink),
			0 0 0 3px rgba(115, 226, 182, 0.55);
	}
	.mark {
		width: 48px;
		height: 48px;
	}
	.right-label {
		padding: 0 4px;
		font-size: 10px;
		font-weight: 700;
		letter-spacing: 2.5px;
		text-transform: uppercase;
		opacity: 0.85;
	}
	.tile-input {
		width: 100%;
		min-width: 0;
		height: 40px;
		padding: 0 4px;
		border: 0;
		border-bottom: 2px solid transparent;
		background: transparent;
		color: inherit;
		font-family: var(--bt-font);
		font-weight: 800;
		font-size: 20px;
		line-height: 1.2;
		outline: none;
	}
	.tile-input::placeholder {
		color: currentColor;
		opacity: 0.55;
		font-weight: 700;
	}
	.tile-input:focus {
		border-bottom-color: currentColor;
	}
	.tools {
		position: absolute;
		top: 6px;
		right: 8px;
		display: flex;
		gap: 2px;
		opacity: 0;
		transition: opacity 120ms ease;
	}
	.tile:hover .tools,
	.tile:focus-within .tools {
		opacity: 1;
	}
	@media (hover: none) {
		.tools {
			opacity: 1;
		}
	}
	.tool {
		display: grid;
		place-items: center;
		width: 28px;
		height: 28px;
		border-radius: 999px;
		background: var(--fill-deep);
		color: var(--ink);
		cursor: pointer;
	}
	.tool:hover {
		background: rgba(10, 5, 31, 0.9);
	}
	.swatch:focus-within,
	.tool:focus-visible,
	.correct:focus-visible {
		outline: 2px solid var(--ink);
		outline-offset: 2px;
	}
	.dot {
		width: 14px;
		height: 14px;
		border-radius: 999px;
		box-shadow: 0 0 0 2px var(--ink);
	}
	.correct {
		display: grid;
		place-items: center;
		flex: none;
		width: 44px;
		height: 44px;
		margin-top: 16px;
		border-radius: 999px;
		background: var(--fill-deep);
		color: rgba(254, 255, 255, 0.35);
	}
	.correct-box {
		border-radius: 10px;
	}
	.correct:hover {
		color: var(--ink);
	}
	.correct-on,
	.correct-on:hover {
		background: var(--ink);
		color: var(--ink-dark);
	}
</style>
