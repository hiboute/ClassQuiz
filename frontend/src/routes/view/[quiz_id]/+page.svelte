<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import DownloadQuiz from '$lib/components/DownloadQuiz.svelte';
	import { getLocalization } from '$lib/i18n';
	import { QuizQuestionType } from '$lib/quiz_types.js';
	import StartGamePopup from '$lib/dashboard/start_game.svelte';
	import Spinner from '$lib/Spinner.svelte';
	import ShapeMark from '$lib/brand/ShapeMark.svelte';
	import { answerStyle } from '$lib/brand/answers';
	import MediaComponent from '$lib/editor/MediaComponent.svelte';
	import RatingComponent from '$lib/view_quiz/RatingComponent.svelte';
	import { page } from '$app/state';
	import ModComponent from './ModComponent.svelte';


	let start_game = $state(null);
	let download_id: string | null = $state(null);
	const urlparams = page.url.searchParams;
	const mod_view = Boolean(urlparams.get('mod'));
	const auto_expand = Boolean(urlparams.get('autoExpand'));
	const auto_return = Boolean(urlparams.get('autoReturn'));

	const { t } = getLocalization();
	let { data } = $props();
	let { quiz, logged_in }: { quiz: any; logged_in: boolean } = $state(data);

	interface Question {
		time: string;
		question: string;
		image?: string;
		answers: Answer[];
	}

	interface Answer {
		right: boolean;
		answer: string;
	}

	interface QuizData {
		id: string;
		public: boolean;
		title: string;
		description: string;
		created_at: string;
		updated_at: string;
		user_id: string;
		questions: Question[];
		mod_rating?: number;
	}
</script>

<svelte:head>
	<title>{quiz.title.replace(/<[^>]*>/g, '')} - India Tech Hub Live Quiz</title>
</svelte:head>

<main class="w-full max-w-5xl mx-auto px-4 sm:px-6 lg:px-10 pt-8 lg:pt-14 pb-16">
	<header class="grid gap-8 lg:grid-cols-[1fr_auto] lg:items-end">
		<div class="min-w-0">
			<span class="bt-eyebrow text-ink-muted mb-4">
				{quiz.questions.length}
				{quiz.questions.length === 1 ? 'question' : 'questions'}
			</span>
			<h1 class="bt-headline text-[32px] lg:text-[52px] break-words">{@html quiz.title}</h1>
			{#if quiz.description}
				<div class="mt-3 text-ink-muted max-w-2xl">{@html quiz.description}</div>
			{/if}
			<p class="mt-3 text-sm text-ink-muted">
				{$t('view_quiz_page.made_by')}
				<a href="/user/{quiz.user_id.id}" class="text-ink hover:underline underline-offset-4"
					>@{quiz.user_id.username}</a
				>
			</p>
		</div>
		<div class="flex flex-wrap gap-3">
			<span title={logged_in ? undefined : 'Sign in to start a live game'}>
				<button
					type="button"
					class="bt-btn-primary"
					disabled={!logged_in}
					onclick={() => (start_game = quiz.id)}
				>
					<svg class="h-4 w-4" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"
						><path d="M7 4.5v15l13-7.5z" /></svg
					>
					Start
				</button>
			</span>
			<a href="/practice?quiz_id={quiz.id}" class="bt-btn-ghost">{$t('words.practice')}</a>
			{#if logged_in}
				<button type="button" class="bt-btn-ghost" onclick={() => (download_id = quiz.id)}
					>{$t('words.download')}</button
				>
			{/if}
		</div>
	</header>

	<div class="mt-8 flex flex-wrap gap-3 items-start">
		<RatingComponent bind:quiz />
		{#if mod_view}
			<ModComponent autoReturn={auto_return} quiz_id={quiz.id} />
		{/if}
	</div>

	<ol class="mt-10 flex flex-col gap-3">
		{#each quiz.questions as question, index_question}
			<li>
				<details class="bt-glass bt-glass-faint group overflow-hidden" open={auto_expand}>
					<summary
						class="flex items-center gap-4 p-5 sm:px-7 cursor-pointer list-none hover:bg-white/[0.05] [&::-webkit-details-marker]:hidden"
					>
						<span class="bt-num text-2xl text-ink-muted w-10 shrink-0">{index_question + 1}</span>
						<span class="flex-1 min-w-0 font-bold text-lg leading-snug break-words"
							>{@html question.question}</span
						>
						<span class="text-sm text-ink-muted shrink-0 tabular-nums">{question.time} s</span>
						<svg
							class="h-5 w-5 shrink-0 transition-transform group-open:rotate-180"
							viewBox="0 0 24 24"
							fill="none"
							stroke="currentColor"
							stroke-width="2.4"
							aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M6 9l6 6 6-6" /></svg
						>
					</summary>
					<div class="px-5 pb-6 sm:px-7 flex flex-col gap-4">
						{#if question.image}
							<MediaComponent css_classes="max-h-64 w-auto rounded-[18px] mx-auto" src={question.image} muted={true} />
						{/if}
						{#if question.type === QuizQuestionType.ABCD || question.type === undefined || question.type === QuizQuestionType.CHECK || question.type === QuizQuestionType.VOTING}
							<div class="grid sm:grid-cols-2 gap-3">
								{#each question.answers as answer, index_answer}
									{@const st = answerStyle(index_answer)}
									{@const graded = question.type !== QuizQuestionType.VOTING}
									<div
										class="{st.className} min-h-16 px-3 py-3 text-base"
										class:bt-tile-dim={graded && !answer.right}
									>
										<span class="bt-tile-mark h-10 w-10">
											<ShapeMark shape={st.shape} size={18} />
										</span>
										<span class="flex-1 min-w-0 break-words normal-case font-bold">{answer.answer}</span>
										{#if graded && answer.right}
											<span class="text-[11px] tracking-[2px] pe-1">RIGHT</span>
										{/if}
									</div>
								{/each}
							</div>
						{:else if question.type === QuizQuestionType.RANGE}
							<p class="text-ink-muted">
								Any number from {question.answers.min_correct} to {question.answers.max_correct} is right.
								Players pick between {question.answers.min} and {question.answers.max}.
							</p>
						{:else if question.type === QuizQuestionType.ORDER}
							<ol class="flex flex-col gap-2">
								{#each question.answers as answer, i}
									<li class="flex items-center gap-3 rounded-[14px] bg-white/[0.06] px-4 py-3">
										<span class="bt-num text-xl text-ink-muted w-6">{i + 1}</span>
										<span class="font-bold">{answer.answer}</span>
									</li>
								{/each}
							</ol>
						{:else if question.type === QuizQuestionType.TEXT}
							<p class="text-sm text-ink-muted">Accepted answers</p>
							<ul class="flex flex-wrap gap-2">
								{#each question.answers as answer}
									<li class="rounded-full bg-white/10 px-4 py-2 font-bold">{answer.answer}</li>
								{/each}
							</ul>
						{:else if question.type === QuizQuestionType.WORD_CLOUD}
							<p class="text-sm text-ink-muted">
								Word cloud: players send one word or a short phrase (30 characters at most).
								No right answer and no points; the big screen shows the words as they arrive.
							</p>
						{:else if question.type === QuizQuestionType.SLIDE}
							{#await import('$lib/play/admin/slide.svelte')}
								<Spinner my_20={false} />
							{:then c}
								<div class="max-h-[90%] max-w-[90%]">
									<c.default question={quiz.questions[index_question]} />
								</div>
							{/await}
						{:else}
							<p class="text-sm text-ink-muted">Players type a short free answer.</p>
						{/if}
					</div>
				</details>
			</li>
		{/each}
	</ol>

	<p class="mt-10 text-sm text-ink-muted">
		To report this quiz, contact the event organisers and quote quiz {quiz.id}.
	</p>
</main>

{#if start_game !== null}
	<StartGamePopup
		bind:quiz_id={start_game}
		quiz_title={quiz.title}
		question_count={quiz.questions.length}
	/>
{/if}

<DownloadQuiz bind:quiz_id={download_id} />
