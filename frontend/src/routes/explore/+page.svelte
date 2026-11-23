<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { navbarVisible } from '$lib/stores.svelte.ts';
	import SearchCard from '$lib/search-card.svelte';
	import PageHeader from '$lib/components/organiser/PageHeader.svelte';
	import Footer from '$lib/footer.svelte';
	import type { PageData } from './$types';

	navbarVisible.visible = true;

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	const hits = $derived(Array.isArray(data.results?.hits) ? data.results.hits : []);
</script>

<svelte:head>
	<title>Explore - India Tech Hub Live Quiz</title>
</svelte:head>

<main class="min-h-[calc(100dvh-4rem)] w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-10 pt-8 lg:pt-14 pb-16">
	<PageHeader eyebrow="Public quizzes" kicker="Ready to host" headline="Explore">
		{#snippet actions()}
			<a href="/search" class="bt-btn-ghost">Search</a>
		{/snippet}
	</PageHeader>
	{#if hits.length === 0}
		<p class="mt-10 text-ink-muted">No public quiz yet.</p>
	{:else}
		<ul class="mt-10 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
			{#each hits as quiz (quiz.id)}
				<li><SearchCard {quiz} /></li>
			{/each}
		</ul>
	{/if}
</main>
<Footer />
