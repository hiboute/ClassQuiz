<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!-- Full error screen in the midnight world: huge status, a plain sentence, ways out. -->
<script lang="ts">
	import World from '$lib/brand/World.svelte';

	interface Props {
		status: number;
		headline: string;
		message: string;
	}

	let { status, headline, message }: Props = $props();
</script>

<svelte:head>
	<title>{status} - India Tech Hub Live Quiz</title>
</svelte:head>

<World world="midnight" mesh fullscreen={false} class="min-h-[calc(100dvh-4rem)] flex items-center">
	<main class="w-full max-w-5xl mx-auto px-4 sm:px-6 lg:px-10 py-16">
		<span class="bt-eyebrow text-ink-muted mb-6">Error {status}</span>
		<p class="bt-num bt-text-display text-[120px] sm:text-[200px]" aria-hidden="true">{status}</p>
		<h1 class="bt-headline text-[30px] sm:text-[44px] mt-6">{headline}</h1>
		<p class="mt-3 text-ink-muted max-w-xl">{message}</p>
		<div class="mt-8 flex flex-wrap gap-3">
			<a href="/play" class="bt-btn-primary">Join a game</a>
			<a href="/dashboard" class="bt-btn-ghost">Dashboard</a>
		</div>
	</main>
</World>
