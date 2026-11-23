<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import DownloadQuiz from '$lib/components/DownloadQuiz.svelte';
	import { getLocalization } from '$lib/i18n';
	import Footer from '$lib/footer.svelte';
	import { signedIn } from '$lib/stores';
	import { navbarVisible } from '$lib/stores.svelte';
	import CommandpaletteNotice from '$lib/components/popover/commandpalettenotice.svelte';
	import Fuse from 'fuse.js';
	import type { PageData } from './$types';
	import StartGamePopup from '$lib/dashboard/start_game.svelte';
	import Analytics from './Analytics.svelte';
	import PageHeader from '$lib/components/organiser/PageHeader.svelte';
	import QuizCard from './QuizCard.svelte';
	import MobileQuizCard from './MobileQuizCard.svelte';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();
	signedIn.set(true);
	navbarVisible.visible = true;
	const { t } = getLocalization();

	type Item = {
		id: string;
		type: 'quiz' | 'quiztivity';
		title: string;
		description?: string;
		questions?: unknown[];
		pages?: unknown[];
		[key: string]: any;
	};

	const all_items: Item[] = $derived([
		...(Array.isArray(data.quizzes) ? data.quizzes : []).map((q) => ({ ...q, type: 'quiz' })),
		...(Array.isArray(data.quiztivities) ? data.quiztivities : []).map((q) => ({
			...q,
			type: 'quiztivity'
		}))
	]);
	const fuse = $derived(
		new Fuse(all_items, {
			keys: ['title', 'description', 'questions.question'],
			threshold: 0.35,
			ignoreLocation: true
		})
	);

	let search_term = $state('');
	const items_to_show = $derived(
		search_term.trim() === '' ? all_items : fuse.search(search_term.trim()).map((r) => r.item)
	);
	const quiz_count = $derived(all_items.filter((i) => i.type === 'quiz').length);

	let start_game: string | null = $state(null);
	let start_item: Item | undefined = $state(undefined);
	let download_id: string | null = $state(null);
	let analytics_quiz_selected: any = $state(undefined);

	const deleteQuiz = async (item: Item) => {
		const name = item.title?.replace(/<[^>]*>/g, '') || 'this quiz';
		if (!confirm(`Delete "${name}"? This cannot be undone.`)) {
			return;
		}
		if (item.type === 'quiz') {
			await fetch(`/api/v1/quiz/delete/${item.id}`, { method: 'DELETE' });
		} else {
			await fetch(`/api/v1/quiztivity/${item.id}`, { method: 'DELETE' });
		}
		window.location.reload();
	};
</script>

<svelte:head>
	<title>Dashboard - India Tech Hub Live Quiz</title>
</svelte:head>
<Analytics bind:quiz={analytics_quiz_selected} />
<CommandpaletteNotice />

<main class="min-h-[calc(100dvh-4rem)] w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-10 pt-8 lg:pt-14 pb-16 max-md:pb-32">
	<PageHeader
		eyebrow="Organiser dashboard"
		kicker="Live Quiz"
		headline="Your quizzes"
	>
		{#snippet actions()}
			<a href="/create" class="bt-btn-primary max-md:hidden">
				<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" aria-hidden="true"
					><path stroke-linecap="round" d="M12 5v14M5 12h14" /></svg
				>
				{$t('dashboard.create_quiz')}
			</a>
			<a href="/import" class="bt-btn-ghost max-md:hidden">{$t('words.import')}</a>
		{/snippet}
		<nav class="mt-5 flex flex-wrap gap-x-5 gap-y-2 text-sm max-md:mt-2 max-md:gap-y-0 max-md:text-[15px]" aria-label="Organiser pages">
			<a href="/results" class="text-ink-muted hover:text-ink underline-offset-4 hover:underline max-md:inline-flex max-md:min-h-11 max-md:items-center"
				>{$t('words.results')}</a
			>
			<a href="/edit/files" class="text-ink-muted hover:text-ink underline-offset-4 hover:underline max-md:inline-flex max-md:min-h-11 max-md:items-center"
				>{$t('words.files_library')}</a
			>
			<a
				href="/account/settings"
				class="text-ink-muted hover:text-ink underline-offset-4 hover:underline max-md:inline-flex max-md:min-h-11 max-md:items-center"
				>{$t('words.settings')}</a
			>
			<a href="/import" class="text-ink-muted hover:text-ink underline-offset-4 hover:underline max-md:inline-flex max-md:min-h-11 max-md:items-center md:hidden"
				>{$t('words.import')}</a
			>
		</nav>
	</PageHeader>

	{#if all_items.length === 0}
		<section class="bt-glass bt-glass-faint mt-10 p-8 lg:p-12 max-w-2xl">
			<span class="bt-eyebrow text-ink-muted mb-3">Nothing here yet</span>
			<p class="bt-headline text-2xl lg:text-3xl">Create your first quiz</p>
			<p class="mt-3 text-ink-muted">
				Write the questions once, then start a live game from here. Players join on their phones
				with the game PIN.
			</p>
			<div class="mt-6 flex flex-wrap gap-3">
				<a href="/create" class="bt-btn-primary">{$t('dashboard.create_quiz')}</a>
				<a href="/import" class="bt-btn-ghost">{$t('words.import')}</a>
			</div>
		</section>
	{:else}
		<div class="mt-10 flex flex-col sm:flex-row sm:items-center gap-4 justify-between max-md:mt-6">
			<div class="relative w-full sm:max-w-md">
				<svg
					class="absolute start-5 top-1/2 -translate-y-1/2 h-5 w-5 text-ink-muted pointer-events-none"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
					aria-hidden="true"
					><circle cx="11" cy="11" r="7" /><path stroke-linecap="round" d="M20 20l-3.5-3.5" /></svg
				>
				<input
					bind:value={search_term}
					type="search"
					class="bt-input !text-base !ps-13 !pe-12"
					placeholder={$t('dashboard.search_for_own_quizzes')}
					aria-label="Search your quizzes"
				/>
				{#if search_term}
					<button
						type="button"
						class="absolute end-3 top-1/2 -translate-y-1/2 h-8 w-8 rounded-full hover:bg-white/10 flex items-center justify-center"
						aria-label="Clear search"
						onclick={() => (search_term = '')}
					>
						<svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"
							><path stroke-linecap="round" d="M6 6l12 12M18 6L6 18" /></svg
						>
					</button>
				{/if}
			</div>
			<p class="bt-eyebrow !text-[11px] !tracking-[3px] text-ink-muted">
				{quiz_count}
				{quiz_count === 1 ? 'quiz' : 'quizzes'}
				{#if all_items.length !== quiz_count}
					<span class="mx-1">/</span>{all_items.length - quiz_count} other
				{/if}
			</p>
		</div>

		{#if items_to_show.length === 0}
			<p class="mt-10 text-ink-muted">No quiz matches "{search_term}".</p>
		{:else}
			<!-- phone: compact cards, the rest of the actions in a sheet -->
			<ul class="mt-5 flex flex-col gap-3 md:hidden">
				{#each items_to_show as item, i (item.type + item.id)}
					<li>
						<MobileQuizCard
							{item}
							index={i}
							onstart={() => {
								start_item = item;
								start_game = item.id;
							}}
							onanalytics={() => (analytics_quiz_selected = item)}
							ondownload={() => (download_id = item.id)}
							ondelete={() => deleteQuiz(item)}
						/>
					</li>
				{/each}
			</ul>
			<ul class="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-3 max-md:hidden">
				{#each items_to_show as item (item.type + item.id)}
					<li>
						<QuizCard
							{item}
							onstart={() => {
								start_item = item;
								start_game = item.id;
							}}
							onanalytics={() => (analytics_quiz_selected = item)}
							ondownload={() => (download_id = item.id)}
							ondelete={() => deleteQuiz(item)}
						/>
					</li>
				{/each}
			</ul>
		{/if}
	{/if}
</main>
<div class="new-bar md:hidden">
	<a href="/create" class="bt-btn-primary bt-btn-block new-btn">
		<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" aria-hidden="true"
			><path stroke-linecap="round" d="M12 5v14M5 12h14" /></svg
		>
		New quiz
	</a>
</div>
<Footer />
{#if start_game !== null}
	<StartGamePopup
		bind:quiz_id={start_game}
		quiz_title={start_item?.title}
		question_count={start_item?.questions?.length}
	/>
{/if}
<DownloadQuiz bind:quiz_id={download_id} />

<style>
	/* phone: the New quiz button stays at the thumb */
	.new-bar {
		position: fixed;
		left: 0;
		right: 0;
		bottom: 0;
		z-index: 20;
		padding: 24px 16px max(14px, env(safe-area-inset-bottom));
		background: linear-gradient(
			to bottom,
			rgba(9, 9, 36, 0) 0,
			rgba(9, 9, 36, 0.86) 34%,
			rgba(9, 9, 36, 0.96)
		);
		pointer-events: none;
	}
	.new-btn {
		min-height: 56px;
		font-size: 17px;
		pointer-events: auto;
	}
</style>
