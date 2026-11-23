<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!--
	The big screen frame: a 1920x1080 stage, scaled to fit any window (projector,
	1280x720, laptop) over a full-bleed colour world. Children are laid out in
	stage pixels. `overlay` renders outside the scaled stage (host controls).
-->
<script lang="ts">
	import type { Snippet } from 'svelte';
	import World from '$lib/brand/World.svelte';
	import Logo from '$lib/brand/Logo.svelte';
	import type { World as WorldName } from '$lib/brand/answers';
	import { worldFor } from './worlds';

	interface Props {
		world: WorldName;
		mesh?: boolean;
		page?: string;
		/** question strip: number of questions and the current index */
		strip?: { count: number; current: number } | null;
		children?: Snippet;
		overlay?: Snippet;
	}

	let { world, mesh = false, page, strip = null, children, overlay }: Props = $props();

	let w = $state(1920);
	let h = $state(1080);
	const scale = $derived(Math.max(0.2, Math.min(w / 1920, h / 1080)));
</script>

<svelte:window bind:innerWidth={w} bind:innerHeight={h} />

<World {world} {mesh} fullscreen={false} class="h-dvh host-world">
	<div class="h-stage" style="transform: translate(-50%, -50%) scale({scale})">
		{@render children?.()}
		<div class="h-logo"><Logo width={210} /></div>
		{#if page}<div class="h-page">{page}</div>{/if}
		{#if strip && strip.count > 1}
			<div class="h-strip" aria-label="Question worlds">
				{#each Array(strip.count) as _, i}
					<span
						class="h-strip__tab w-{worldFor(i)}"
						class:h-strip__tab--now={i === strip.current}
						class:h-strip__tab--next={i > strip.current}
					></span>
				{/each}
			</div>
		{/if}
	</div>
	{@render overlay?.()}
</World>

<style>
	:global(.host-world) {
		transition: background-color 600ms ease;
	}
	.h-stage {
		position: absolute;
		left: 50%;
		top: 50%;
		width: 1920px;
		height: 1080px;
		transform-origin: 50% 50%;
		font-size: 22px;
		line-height: 1.2;
		-webkit-font-smoothing: antialiased;
		text-rendering: geometricPrecision;
	}
	.h-logo {
		position: absolute;
		z-index: 5;
		left: 70px;
		top: 976px;
	}
	.h-page {
		position: absolute;
		z-index: 5;
		right: 39px;
		top: 1035px;
		transform: translateY(-50%);
		font-size: 20px;
	}
	.h-strip {
		position: absolute;
		z-index: 4;
		left: 300px;
		right: 300px;
		bottom: 0;
		height: 38px;
		display: flex;
		align-items: flex-end;
		gap: 6px;
	}
	.h-strip__tab {
		flex: 1;
		height: 10px;
		transition: height 400ms ease;
	}
	.h-strip__tab--now {
		height: 22px;
	}
	.h-strip__tab--next {
		opacity: 0.35;
	}
	.w-indigo {
		background: linear-gradient(90deg, #4e3ac0, #d87acd);
	}
	.w-teal {
		background: linear-gradient(90deg, #24535b, #b4eccd);
	}
	.w-violet {
		background: linear-gradient(90deg, #6731b0, #ec91d4);
	}
	.w-midnight {
		background: linear-gradient(90deg, #1f285d, #516487);
	}
	.w-cobalt {
		background: linear-gradient(90deg, #0d458a, #5ab2da);
	}
	.w-ultraviolet {
		background: linear-gradient(90deg, #231049, #48669c);
	}

	/* ---------- shared stage typography (used by every host screen) ---------- */
	.h-stage :global(.h-title) {
		position: absolute;
		z-index: 3;
		left: 84px;
		top: 81px;
		margin: 0;
		text-transform: uppercase;
	}
	.h-stage :global(.h-kicker) {
		display: block;
		font-weight: 400;
		font-size: 30px;
		line-height: 1.2;
	}
	.h-stage :global(.h-headline) {
		display: block;
		font-weight: 900;
		font-size: 72px;
		line-height: 1.08;
		margin-top: 10px;
		overflow-wrap: anywhere;
	}
	.h-stage :global(.h-label) {
		display: block;
		font-weight: 400;
		font-size: 21px;
		line-height: 1.2;
		letter-spacing: 6px;
		text-transform: uppercase;
	}
	.h-stage :global(.h-num) {
		font-weight: 900;
		line-height: 0.84;
		font-variant-numeric: tabular-nums;
		font-feature-settings: 'tnum' 1;
	}
	.h-stage :global(.h-muted) {
		color: var(--ink-muted);
	}
	.h-stage :global(.h-mark) {
		flex: none;
		display: flex;
		align-items: center;
		justify-content: center;
		border-radius: 12px;
		background: var(--fill-deep);
		color: var(--ink);
	}
</style>
