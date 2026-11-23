<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import Editor from '$lib/editor.svelte';
	import { navbarVisible } from '$lib/stores.svelte.ts';
	import { QuizQuestionType } from '$lib/quiz_types';
	import World from '$lib/brand/World.svelte';
	import Loading from '$lib/editor/Loading.svelte';

	navbarVisible.visible = false;

	interface Data {
		public: boolean;
		title: string;
		description: string;
		questions: Question[];
	}

	interface Question {
		question: string;
		time: string;
		answers: Answer[];
	}

	interface Answer {
		right: boolean;
		answer: string;
	}

	let { data } = $props();
	let { quiz_id } = $state(data);
	let quiz_data: Data = $state();

	const get_quiz = async (): Promise<void> => {
		const response = await fetch(`/api/v1/quiz/get/${quiz_id}`);
		if (response.status === 404) {
			throw new Error('Quiz not found');
		} else if (response.status === 200) {
			let temp_data = await response.json();
			for (let i = 0; i < temp_data.questions.length; i++) {
				let question = temp_data.questions[i];
				if (question.type === undefined) {
					temp_data.questions[i].type = QuizQuestionType.ABCD;
				} else {
					temp_data.questions[i].type =
						QuizQuestionType[question.type] ?? QuizQuestionType.ABCD;
				}
			}
			quiz_data = temp_data;
			return;
		}
	};
</script>

<svelte:head>
	<title>India Tech Hub Live Quiz - Edit</title>
</svelte:head>
{#await get_quiz()}
	<World world="midnight">
		<div class="grid min-h-dvh place-items-center">
			<Loading label="Loading the quiz" />
		</div>
	</World>
{:then _}
	{#if quiz_data !== undefined}
		<Editor bind:data={quiz_data} bind:quiz_id />
	{/if}
{:catch err}
	<World world="midnight">
		<div class="grid min-h-dvh place-items-center p-6">
			<div class="bt-glass bt-glass-faint max-w-lg p-8 text-center">
				<span class="bt-eyebrow text-[11px] text-ink-muted">Quiz editor</span>
				<h1 class="bt-headline mt-2 text-3xl">{err.message}</h1>
				<a href="/dashboard" class="bt-btn-primary mt-6">Back to the dashboard</a>
			</div>
		</div>
	</World>
{/await}
