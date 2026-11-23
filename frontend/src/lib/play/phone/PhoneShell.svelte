<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!--
	Full-height phone frame in a colour world: exactly one viewport tall
	(100dvh, no page scroll unless the content needs it), with safe-area
	insets and the 20px side gutter of the mockups.
-->
<script lang="ts">
	import type { Snippet } from 'svelte';
	import World from '$lib/brand/World.svelte';
	import type { World as WorldName } from '$lib/brand/answers';

	interface Props {
		world?: WorldName;
		mesh?: boolean;
		state?: string;
		class?: string;
		children?: Snippet;
	}

	let { world = 'indigo', mesh = false, state, class: klass = '', children }: Props = $props();
</script>

<World {world} {mesh} fullscreen={false} class="phone-shell">
	<div class="phone-pad {klass}" data-phone-state={state}>
		{@render children?.()}
	</div>
</World>

<style>
	:global(.phone-shell) {
		min-height: 100vh;
		min-height: 100dvh;
		display: flex;
		flex-direction: column;
		font-family: var(--bt-font, 'LOREAL Essentielle', sans-serif);
		line-height: 1.2;
		-webkit-tap-highlight-color: transparent;
		touch-action: manipulation;
		overscroll-behavior: none;
		-webkit-user-select: none;
		user-select: none;
		-webkit-touch-callout: none;
	}
	:global(.phone-shell input),
	:global(.phone-shell textarea) {
		-webkit-user-select: text;
		user-select: text;
	}
	.phone-pad {
		position: relative;
		z-index: 1;
		flex: 1 1 auto;
		display: flex;
		flex-direction: column;
		width: 100%;
		max-width: 520px;
		margin: 0 auto;
		box-sizing: border-box;
		min-height: 100vh;
		min-height: 100dvh;
		padding: max(28px, calc(env(safe-area-inset-top) + 16px))
			max(20px, calc(env(safe-area-inset-right) + 12px))
			max(24px, calc(env(safe-area-inset-bottom) + 12px))
			max(20px, calc(env(safe-area-inset-left) + 12px));
	}
	.phone-pad :global(*),
	.phone-pad :global(*::before),
	.phone-pad :global(*::after) {
		box-sizing: border-box;
	}
</style>
