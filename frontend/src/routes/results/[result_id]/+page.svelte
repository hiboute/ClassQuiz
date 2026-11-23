<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import type { PageData } from './$types';
	import PlayerOverview from './player_overview.svelte';
	import QuestionOverview from './question_overview.svelte';
	import GeneralOverview from './general_overview.svelte';
	import { fade } from 'svelte/transition';
	import Footer from '$lib/footer.svelte';


	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	type Tab = 'overview' | 'players' | 'questions';
	let selected_tab: Tab = $state('overview');

	const tabs: { id: Tab; label: () => string }[] = [
		{ id: 'overview', label: () => 'Overview' },
		{ id: 'players', label: () => 'Players' },
		{ id: 'questions', label: () => 'Questions' }
	];

	const fmt = (ts: string) =>
		new Date(ts).toLocaleString(undefined, {
			day: 'numeric',
			month: 'short',
			year: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
</script>

<svelte:head>
	<title>Results - India Tech Hub Live Quiz</title>
</svelte:head>

<main class="min-h-[calc(100dvh-4rem)] w-full max-w-6xl mx-auto px-4 sm:px-6 lg:px-10 pt-8 lg:pt-14 pb-16">
	{#if !data.results}
		<section class="bt-glass bt-glass-faint p-8 lg:p-12 max-w-2xl">
			<span class="bt-eyebrow text-ink-muted mb-3">Results</span>
			<h1 class="bt-headline text-2xl lg:text-3xl">These results were not found</h1>
			<p class="mt-3 text-ink-muted">They may have been deleted, or belong to another account.</p>
			<a href="/results" class="bt-btn-ghost mt-6">All results</a>
		</section>
	{:else}
		<a href="/results" class="text-sm text-ink-muted hover:text-ink hover:underline underline-offset-4"
			>All results</a
		>
		<header class="mt-4 flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
			<div class="min-w-0">
				<span class="bt-eyebrow text-ink-muted mb-4">{fmt(data.results.timestamp)}</span>
				<h1 class="bt-headline text-[30px] lg:text-[48px] break-words">
					{@html data.results.title}
				</h1>
				{#if data.results.note}
					<p class="mt-2 text-ink-muted">{data.results.note}</p>
				{/if}
			</div>
			<a
				href="/api/v1/results/export/{data.results.id}"
				class="bt-btn-primary shrink-0 self-start lg:self-auto"
				download
			>
				<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" aria-hidden="true"
					><path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg
				>
				Export xlsx
			</a>
		</header>

		<div
			class="mt-8 flex w-full sm:w-fit rounded-full bg-white/[0.08] p-1.5 gap-1"
			role="tablist"
			aria-label="Result views"
		>
			{#each tabs as tab}
				<button
					type="button"
					role="tab"
					aria-selected={selected_tab === tab.id}
					class="flex-1 sm:flex-none rounded-full px-2 sm:px-5 py-2.5 text-[13px] sm:text-sm font-bold uppercase tracking-[1px] sm:tracking-[2px] whitespace-nowrap transition-colors {selected_tab ===
					tab.id
						? 'bg-[var(--ink)] text-black'
						: 'text-ink-muted hover:text-ink'}"
					onclick={() => (selected_tab = tab.id)}>{tab.label()}</button
				>
			{/each}
		</div>

		<div class="mt-6">
			{#if selected_tab === 'overview'}
				<div in:fade={{ duration: 150 }}>
					<GeneralOverview
						scores={data.results.player_scores ?? {}}
						answers={data.results.answers ?? []}
						questions={data.results.questions ?? []}
					/>
				</div>
			{:else if selected_tab === 'questions'}
				<div in:fade={{ duration: 150 }}>
					<QuestionOverview questions={data.results.questions} answers={data.results.answers} />
				</div>
			{:else if selected_tab === 'players'}
				<div in:fade={{ duration: 150 }}>
					<PlayerOverview
						custom_field={data.results.custom_field_data ?? {}}
						scores={data.results.player_scores ?? {}}
						answers={data.results.answers ?? []}
					/>
				</div>
			{/if}
		</div>
	{/if}
</main>
<Footer />
