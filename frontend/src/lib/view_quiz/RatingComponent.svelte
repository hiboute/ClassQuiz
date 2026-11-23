<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import type { QuizData } from '$lib/quiz_types';
	import { createTippy } from 'svelte-tippy';

	interface Props {
		quiz: QuizData;
	}

	let { quiz = $bindable() }: Props = $props();

	const tippy = createTippy({
		arrow: true,
		animation: 'perspective-subtle',
		placement: 'top'
	});

	const complete_action = async (positive: boolean) => {
		const res = await fetch(`/api/v1/community/rate/${quiz.id}`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({ type: positive ? 'LIKE' : 'DISLIKE' })
		});
		if (res.status === 409) {
			alert('You already rated this quiz.');
			return;
		} else if (!res.ok) {
			return;
		}
		if (positive) {
			quiz.likes += 1;
		} else {
			quiz.dislikes += 1;
		}
	};
</script>

<div class="flex flex-wrap items-center gap-2" aria-label="Quiz rating and stats">
	<button
		type="button"
		class="flex items-center gap-2 rounded-full bg-white/10 hover:bg-white/20 px-4 py-2 text-sm"
		use:tippy={{ content: 'Like this quiz' }}
		onclick={() => complete_action(true)}
	>
		<!-- heroicons/thumb-up -->
		<svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true"
			><path
				stroke-linecap="round"
				stroke-linejoin="round"
				d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5"
			/></svg
		>
		<span class="tabular-nums">{quiz.likes}</span>
		<span class="sr-only">likes</span>
	</button>
	<button
		type="button"
		class="flex items-center gap-2 rounded-full bg-white/10 hover:bg-white/20 px-4 py-2 text-sm"
		use:tippy={{ content: 'Dislike this quiz' }}
		onclick={() => complete_action(false)}
	>
		<!-- heroicons/thumb-down -->
		<svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true"
			><path
				stroke-linecap="round"
				stroke-linejoin="round"
				d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018a2 2 0 01.485.06l3.76.94m-7 10v5a2 2 0 002 2h.096c.5 0 .905-.405.905-.904 0-.715.211-1.413.608-2.008L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5"
			/></svg
		>
		<span class="tabular-nums">{quiz.dislikes}</span>
		<span class="sr-only">dislikes</span>
	</button>
	<span class="rounded-full bg-white/[0.05] px-4 py-2 text-sm text-ink-muted"
		><span class="tabular-nums text-ink">{quiz.plays}</span> games</span
	>
	<span class="rounded-full bg-white/[0.05] px-4 py-2 text-sm text-ink-muted"
		><span class="tabular-nums text-ink">{quiz.views}</span> views</span
	>
</div>
