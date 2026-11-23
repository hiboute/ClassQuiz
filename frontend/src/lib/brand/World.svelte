<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!--
	Full-bleed colour-world ground. Sets data-world (so --ground, --ground-mid,
	--ground-glow and --fill-card follow it for everything inside), paints the
	world bloom, and optionally a photographic ground (`image`) or the mesh wave
	(`mesh`, plain grounds only).
-->
<script lang="ts">
	import type { Snippet } from 'svelte';
	import type { World } from './answers';

	interface Props {
		world?: World;
		mesh?: boolean;
		image?: string;
		fullscreen?: boolean;
		class?: string;
		children?: Snippet;
	}

	let {
		world = 'midnight',
		mesh = false,
		image,
		fullscreen = true,
		class: klass = '',
		children
	}: Props = $props();
</script>

<div
	data-world={world}
	class="bt-world-ground relative isolate w-full overflow-hidden {klass}"
	class:min-h-dvh={fullscreen}
>
	{#if image}
		<div
			class="absolute inset-0 -z-10 bg-cover bg-center"
			style="background-image:url('{image}')"
			aria-hidden="true"
		></div>
	{/if}
	{#if mesh && !image}
		<img src="/brand/mesh-wave.svg" alt="" aria-hidden="true" class="bt-mesh -z-10" />
	{/if}
	{@render children?.()}
</div>
