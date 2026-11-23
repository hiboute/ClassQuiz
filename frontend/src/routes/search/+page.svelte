<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->
<script lang="ts">
	import { getLocalization } from '$lib/i18n';
	const { t } = getLocalization();
	import SearchCard from '$lib/search-card.svelte';
	import PageHeader from '$lib/components/organiser/PageHeader.svelte';
	import { onMount } from 'svelte';
	let search_term = $state('');
	let resp_data = $state(null);

	const submit = async () => {
		const res = await fetch('/api/v1/search/', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({
				q: search_term,
				attributesToHighlight: ['*']
			})
		});
		if (res.status === 200) {
			let resp_data_temp: string = await res.text();
			resp_data_temp = resp_data_temp.replaceAll('<em>', '<mark>');
			resp_data_temp = resp_data_temp.replaceAll('</em>', '</mark>');
			resp_data = JSON.parse(resp_data_temp);
			const url = new URLSearchParams(window.location.search);
			url.set('q', search_term);
			history.pushState(null, null, '?' + url.toString());
		} else {
			console.error('Search failed', res.status);
		}
	};
	onMount(() => {
		const url = new URLSearchParams(window.location.search);
		search_term = url.get('q') ?? '';
		if (search_term.length > 2) submit();
	});
</script>

<svelte:head>
	<title>Search - India Tech Hub Live Quiz</title>
</svelte:head>

<main class="min-h-[calc(100dvh-4rem)] w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-10 pt-8 lg:pt-14 pb-16">
	<PageHeader eyebrow="Public quizzes" kicker="Find a quiz" headline="Search" />
	<form
		class="mt-8 flex gap-3 max-w-2xl"
		role="search"
		onsubmit={(e: Event) => {
			e.preventDefault();
			submit();
		}}
	>
		<input
			type="search"
			class="bt-input flex-1 min-w-0"
			placeholder={$t('search_page.at_least_3_characters')}
			aria-label="Search quizzes"
			bind:value={search_term}
		/>
		<button class="bt-btn-primary shrink-0" aria-label="Search" disabled={search_term.length <= 2} type="submit">
			<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" aria-hidden="true"
				><circle cx="11" cy="11" r="7" /><path stroke-linecap="round" d="M20 20l-3.5-3.5" /></svg
			>
			<span class="hidden sm:inline">Search</span>
		</button>
	</form>

	{#if resp_data}
		{#if resp_data.hits.length !== 0}
			<ul class="mt-10 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
				{#each resp_data.hits as quiz}
					<li><SearchCard quiz={quiz._formatted} /></li>
				{/each}
			</ul>
		{:else}
			<section class="bt-glass bt-glass-faint mt-10 p-8 max-w-2xl">
				<p class="bt-headline text-2xl">No quiz found</p>
				<p class="mt-3 text-ink-muted">
					Try another word, or <a href="/import" class="text-ink underline underline-offset-4">import</a>
					a .cqa or .xlsx quiz file.
				</p>
			</section>
		{/if}
	{/if}
</main>
