<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import World from '$lib/brand/World.svelte';
</script>

<svelte:head>
	<title>India Tech Hub Live Quiz - Controllers</title>
</svelte:head>

<World world="midnight" fullscreen={false} class="min-h-[calc(100dvh-4rem)] flex items-center">
	<div class="bt-glass max-w-xl mx-4 sm:mx-auto my-12 px-8 py-10 text-center">
		<span class="bt-eyebrow text-ink-muted">Live Quiz</span>
		<h1 class="mt-3 text-4xl font-black uppercase tracking-wide">Hardware controllers</h1>
		<p class="mt-4 text-ink-muted">
			Hardware controllers are not used at this event. Players answer from their phones.
		</p>
		<a href="/play" class="bt-btn-primary bt-btn-lg mt-8">Join a game</a>
	</div>
</World>
