<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!--
	RANGE: pick a number on a big slider (plus and minus buttons for precise
	steps), then lock it in. The parent sends the current value when time is up.
-->
<script lang="ts">
	import { formatPoints } from '$lib/play/phone/phone';

	// years and small numbers read better without grouping
	const fmt = (n: number) => (Math.abs(n) < 10000 ? String(n) : formatPoints(n));

	interface Props {
		min: number;
		max: number;
		value: number;
		disabled?: boolean;
		onsubmit: (answer: string) => void;
	}

	let { min, max, value = $bindable(), disabled = false, onsubmit }: Props = $props();

	const lo = $derived(Math.min(Number(min) || 0, Number(max) || 0));
	const hi = $derived(Math.max(Number(min) || 0, Number(max) || 0));
	const span = $derived(hi - lo);
	const step = $derived(span > 1000 ? Math.pow(10, Math.floor(Math.log10(span)) - 2) : 1);
	const pct = $derived(span === 0 ? 0 : ((value - lo) / span) * 100);

	const nudge = (d: number) => {
		if (disabled) return;
		value = Math.min(hi, Math.max(lo, Math.round(value + d * step)));
	};
</script>

<div class="pr-wrap">
	<div class="pr-value bt-num" aria-live="polite">{fmt(value)}</div>
	<div class="pr-slider">
		<button
			type="button"
			class="pr-nudge"
			aria-label="Less"
			{disabled}
			onclick={() => nudge(-1)}>-</button
		>
		<input
			type="range"
			class="pr-input"
			data-testid="range-answer"
			min={lo}
			max={hi}
			{step}
			bind:value
			{disabled}
			style="--pct:{pct}%"
			aria-label="Your answer"
		/>
		<button
			type="button"
			class="pr-nudge"
			aria-label="More"
			{disabled}
			onclick={() => nudge(1)}>+</button
		>
	</div>
	<div class="pr-ends">
		<span>{fmt(lo)}</span>
		<span>{fmt(hi)}</span>
	</div>
	<button
		type="button"
		class="bt-btn-primary bt-btn-lg bt-btn-block"
		data-testid="answer-submit"
		{disabled}
		onclick={() => onsubmit(String(value))}
	>
		Lock in
	</button>
</div>

<style>
	.pr-wrap {
		margin-top: auto;
		display: flex;
		flex-direction: column;
		gap: 16px;
	}
	.pr-value {
		text-align: center;
		font-size: 96px;
		padding: 8px 0 12px;
	}
	.pr-slider {
		display: flex;
		align-items: center;
		gap: 12px;
		border-radius: var(--radius-bt-xl);
		background: var(--fill-glass-mid);
		padding: 18px 14px;
	}
	.pr-nudge {
		flex: none;
		width: 48px;
		height: 48px;
		border: 0;
		border-radius: 50%;
		background: var(--fill-deep);
		color: var(--ink);
		font: 900 26px/1 var(--bt-font);
	}
	.pr-nudge:disabled {
		opacity: 0.4;
	}
	.pr-input {
		flex: 1 1 auto;
		min-width: 0;
		height: 48px;
		margin: 0;
		background: transparent;
		-webkit-appearance: none;
		appearance: none;
		touch-action: pan-y;
	}
	.pr-input::-webkit-slider-runnable-track {
		height: 12px;
		border-radius: 9999px;
		background: linear-gradient(90deg, var(--accent-sky), var(--accent-green)) 0 / var(--pct)
				100% no-repeat,
			rgba(254, 255, 255, 0.17);
	}
	.pr-input::-moz-range-track {
		height: 12px;
		border-radius: 9999px;
		background: rgba(254, 255, 255, 0.17);
	}
	.pr-input::-moz-range-progress {
		height: 12px;
		border-radius: 9999px;
		background: linear-gradient(90deg, var(--accent-sky), var(--accent-green));
	}
	.pr-input::-webkit-slider-thumb {
		-webkit-appearance: none;
		width: 40px;
		height: 40px;
		margin-top: -14px;
		border-radius: 50%;
		background: var(--ink);
		box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35);
	}
	.pr-input::-moz-range-thumb {
		width: 40px;
		height: 40px;
		border: 0;
		border-radius: 50%;
		background: var(--ink);
	}
	.pr-ends {
		display: flex;
		justify-content: space-between;
		padding: 0 6px;
		margin-top: -6px;
		font-size: 15px;
		color: var(--ink-muted);
	}
</style>
