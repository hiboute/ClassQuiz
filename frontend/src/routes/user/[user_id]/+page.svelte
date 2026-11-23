<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import type { PageData } from './$types';
	import { getLocalization } from '$lib/i18n';
	import { signedIn } from '$lib/stores';
	import StartGamePopup from '$lib/dashboard/start_game.svelte';

	const { t } = getLocalization();
	let start_game: string | null = $state(null);
	let start_quiz: any = $state(undefined);

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();
</script>

<svelte:head>
	<title>{data.user.username ? `@${data.user.username}` : 'User not found'} - India Tech Hub Live Quiz</title>
</svelte:head>

<main class="min-h-[calc(100dvh-4rem)] w-full max-w-6xl mx-auto px-4 sm:px-6 lg:px-10 pt-8 lg:pt-14 pb-16">
	{#if data.user.username === undefined}
		<section class="bt-glass bt-glass-faint p-8 max-w-2xl">
			<h1 class="bt-headline text-2xl lg:text-3xl">{$t('public_user_page.user_not_found')}</h1>
		</section>
	{:else}
		<header class="flex items-center gap-5 sm:gap-8">
			<img
				src={`/api/v1/users/avatar/${data.user.id}`}
				alt=""
				class="h-20 w-20 sm:h-28 sm:w-28 rounded-full bg-white/10 object-cover shrink-0"
			/>
			<div class="min-w-0">
				<span class="bt-eyebrow text-ink-muted mb-2"
					>{$t('public_user_page.joined_on', {
						date: new Date(data.user.created_at).toLocaleDateString()
					})}</span
				>
				<h1 class="bt-headline text-[30px] lg:text-[48px] break-words">@{data.user.username}</h1>
			</div>
		</header>

		{#if data.quizzes.length === 0}
			<p class="mt-10 text-ink-muted">{$t('public_user_page.no_original_quizzes')}</p>
		{:else}
			<ul class="mt-10 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
				{#each data.quizzes as quiz}
					<li class="bt-glass bt-glass-faint p-5 sm:p-6 flex flex-col gap-3">
						<h2 class="text-xl sm:text-2xl font-black leading-tight break-words line-clamp-2">
							{@html quiz.title}
						</h2>
						{#if quiz.description}
							<p class="text-sm text-ink-muted line-clamp-2">{@html quiz.description}</p>
						{/if}
						<p class="text-sm text-ink-muted mt-auto">
							{quiz.questions?.length ?? 0}
							{(quiz.questions?.length ?? 0) === 1 ? 'question' : 'questions'}
						</p>
						<div class="flex gap-2">
							{#if $signedIn}
								<button
									type="button"
									class="bt-btn-primary flex-1 !px-4"
									onclick={() => {
										start_quiz = quiz;
										start_game = quiz.id;
									}}>{$t('words.start')}</button
								>
							{/if}
							<a href="/view/{quiz.id}" class="bt-btn-ghost !px-5" class:flex-1={!$signedIn}
								>{$t('words.view')}</a
							>
							{#if $signedIn}
								<a href="/api/v1/eximport/{quiz.id}" class="bt-btn-ghost !px-4" aria-label="Download the quiz">
									<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true"
										><path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
										/></svg
									>
								</a>
							{/if}
						</div>
					</li>
				{/each}
			</ul>
		{/if}
	{/if}
</main>
{#if start_game !== null}
	<StartGamePopup
		bind:quiz_id={start_game}
		quiz_title={start_quiz?.title}
		question_count={start_quiz?.questions?.length}
	/>
{/if}
