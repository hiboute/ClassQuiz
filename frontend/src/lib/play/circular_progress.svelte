<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!--
	Countdown ring: a sky-to-green arc on a deep disc, the seconds left in the
	middle. `progress` is the elapsed fraction (0 = full ring, 1 = empty).
	`color` is kept for older callers; when set it paints the arc flat.
-->
<script lang="ts">
	interface Props {
		progress: number;
		text: string | number;
		color?: string;
		size?: number;
	}

	let { progress, text, color, size = 92 }: Props = $props();

	const uid = `ring-${Math.random().toString(36).slice(2, 9)}`;
	const R = 40;
	const C = 2 * Math.PI * R;
	const clamped = $derived(Math.min(1, Math.max(0, Number(progress) || 0)));
	const offset = $derived(C * clamped);
	const flat = $derived(color && color !== '#ef4444' ? color : undefined);
	const digits = $derived(String(text ?? '').length);
</script>

<div
	id="progress-circle"
	class="ring"
	style="width:{size}px;height:{size}px;--ring-font:{Math.round(size * (digits > 2 ? 0.36 : 0.5))}px"
	role="timer"
	aria-label="{text} seconds left"
>
	<svg viewBox="0 0 92 92" aria-hidden="true">
		<defs>
			<linearGradient id={uid} x1="0" y1="0" x2="1" y2="1">
				<stop offset="0" stop-color="#5db5df" />
				<stop offset="1" stop-color="#27be82" />
			</linearGradient>
		</defs>
		<circle cx="46" cy="46" r={R} fill="none" stroke="rgba(254,255,255,0.17)" stroke-width="6" />
		<circle
			class="ring-arc"
			cx="46"
			cy="46"
			r={R}
			fill="none"
			stroke={flat ?? `url(#${uid})`}
			stroke-width="6"
			stroke-linecap="round"
			stroke-dasharray={C}
			stroke-dashoffset={offset}
			transform="rotate(-90 46 46)"
		/>
	</svg>
	<span class="ring-num bt-text-aurora">{text}</span>
</div>

<style>
	.ring {
		position: relative;
		flex: none;
		border-radius: 50%;
		background: var(--fill-deep);
	}
	.ring svg {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
	}
	.ring-arc {
		transition: stroke-dashoffset 300ms linear;
	}
	.ring-num {
		position: absolute;
		inset: 0;
		display: flex;
		align-items: center;
		justify-content: center;
		padding-top: 2px;
		font-size: var(--ring-font);
		font-weight: 900;
		line-height: 1;
		font-variant-numeric: tabular-nums;
	}
</style>
