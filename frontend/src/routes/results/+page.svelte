<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import type { PageData } from './$types';
	import { page } from '$app/state';
	import { getLocalization } from '$lib/i18n';
	import PageHeader from '$lib/components/organiser/PageHeader.svelte';
	import Footer from '$lib/footer.svelte';

	const { t } = getLocalization();

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	const quiz_id_of = (r: any): string | undefined =>
		typeof r.quiz === 'string' ? r.quiz : r.quiz?.id;

	const quiz_filter = $derived(page.url.searchParams.get('quiz'));
	const results = $derived(
		(Array.isArray(data.results) ? data.results : []).filter(
			(r) => !quiz_filter || quiz_id_of(r) === quiz_filter
		)
	);
	const filter_title = $derived(quiz_filter && results.length ? results[0].title : undefined);

	const player_count = (r: any): number =>
		r.player_scores ? Object.keys(r.player_scores).length : (r.player_count ?? 0);
	const fmt_date = (ts: string) =>
		new Date(ts).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' });
	const fmt_time = (ts: string) =>
		new Date(ts).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
</script>

<svelte:head>
	<title>Results - India Tech Hub Live Quiz</title>
</svelte:head>

<main class="min-h-[calc(100dvh-4rem)] w-full max-w-6xl mx-auto px-4 sm:px-6 lg:px-10 pt-8 lg:pt-14 pb-16">
	<PageHeader eyebrow="Organiser" kicker="Past games" headline={$t('words.results')}>
		{#snippet actions()}
			<a href="/dashboard" class="bt-btn-ghost">Dashboard</a>
		{/snippet}
		{#if quiz_filter}
			<p class="mt-4 flex flex-wrap items-center gap-3 text-sm">
				<span class="rounded-full bg-white/10 px-3 py-1">
					Quiz: <strong>{@html filter_title ?? 'this quiz'}</strong>
				</span>
				<a href="/results" class="text-ink-muted hover:text-ink hover:underline underline-offset-4"
					>Show all games</a
				>
			</p>
		{/if}
	</PageHeader>

	{#if results.length === 0}
		<section class="bt-glass bt-glass-faint mt-10 p-8 lg:p-12 max-w-2xl">
			<span class="bt-eyebrow text-ink-muted mb-3">No games yet</span>
			<p class="bt-headline text-2xl lg:text-3xl">{$t('results_page.no_results_so_far')}</p>
			<p class="mt-3 text-ink-muted">
				Results appear here once a live game ends and you save them from the host screen.
			</p>
		</section>
	{:else}
		<ul class="mt-10 flex flex-col gap-3">
			{#each results as result (result.id)}
				<li>
					<a
						href="/results/{result.id}"
						class="bt-glass bt-glass-faint group flex flex-col sm:flex-row sm:items-center gap-4 p-5 sm:px-7 hover:bg-white/[0.12] transition-colors"
					>
						<div class="min-w-0 flex-1">
							<span class="bt-eyebrow !text-[11px] !tracking-[3px] text-ink-muted">
								{fmt_date(result.timestamp)}, {fmt_time(result.timestamp)}
							</span>
							<p class="mt-1.5 text-xl font-black leading-tight break-words">
								{@html result.title}
							</p>
							{#if result.note}
								<p class="mt-1 text-sm text-ink-muted line-clamp-1">{result.note}</p>
							{/if}
						</div>
						<div class="flex items-center justify-between gap-6 shrink-0">
							<p class="sm:text-end">
								<span class="bt-num text-[34px]">{player_count(result)}</span>
								<span class="block text-xs text-ink-muted mt-1"
									>{player_count(result) === 1 ? 'player' : 'players'}</span
								>
							</p>
							<span
								class="h-10 w-10 rounded-full bg-white/10 group-hover:bg-white/20 flex items-center justify-center"
								aria-hidden="true"
							>
								<svg class="h-5 w-5 rtl:rotate-180" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"
									><path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" /></svg
								>
							</span>
						</div>
					</a>
				</li>
			{/each}
		</ul>
	{/if}
</main>
<Footer />
