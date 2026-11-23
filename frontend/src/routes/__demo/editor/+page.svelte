<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!-- Dev-only: the quiz editor with a fake quiz, every question type, mocked fetch. -->
<script lang="ts">
	import Editor from '$lib/editor.svelte';
	import { navbarVisible } from '$lib/stores.svelte.ts';
	import { QuizQuestionType, type EditorData } from '$lib/quiz_types';

	navbarVisible.visible = false;

	const real_fetch = window.fetch.bind(window);
	window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
		const url = typeof input === 'string' ? input : input instanceof URL ? input.href : input.url;
		const json = (body: unknown) =>
			new Response(JSON.stringify(body), { headers: { 'Content-Type': 'application/json' } });
		if (url.includes('/api/v1/editor/start')) return json({ token: 'demo-edit-token' });
		if (url.includes('/api/v1/editor/finish')) return json({ ok: true });
		if (url.includes('/api/v1/storage/info/'))
			return new Response('', { headers: { 'Content-Type': 'image/svg+xml', 'x-thumbhash': 'AAAA', 'X-Alt-Text': '' } });
		if (url.includes('/api/v1/storage/download/'))
			return new Response(
				`<svg xmlns="http://www.w3.org/2000/svg" width="640" height="360"><defs><linearGradient id="g"><stop offset="0" stop-color="#692aac"/><stop offset="1" stop-color="#5db5df"/></linearGradient></defs><rect width="640" height="360" fill="url(#g)"/><circle cx="460" cy="150" r="90" fill="#f982fa" opacity=".6"/></svg>`,
				{ headers: { 'Content-Type': 'image/svg+xml' } }
			);
		if (url.includes('/api/v1/storage/list/last')) return json([]);
		if (url.includes('/api/v1/pixabay/images')) return json({ hits: [] });
		return real_fetch(input, init);
	};

	const params = new URLSearchParams(window.location.search);
	const empty = params.get('empty') === '1';

	let data: EditorData = $state(
		empty
			? { title: '', description: '', public: false, questions: [] }
			: {
					title: 'Beauty Tech trivia',
					description: 'Twelve questions on the tech behind beauty, for the India Tech Hub opening.',
					public: false,
					cover_image: 'demo-cover',
					questions: [
						{
							type: QuizQuestionType.ABCD,
							question: 'Which tech lets shoppers try a lipstick shade through the phone camera?',
							time: '20',
							points: 'standard',
							image: 'demo-image',
							answers: [
								{ answer: 'Augmented reality', right: true },
								{ answer: 'Voice assistant', right: false },
								{ answer: 'Blockchain ledger', right: false },
								{ answer: 'Demand forecasting', right: false, color: '#D6EDC9' }
							]
						},
						{
							type: QuizQuestionType.ABCD,
							question: 'A skin diagnostic app can run fully on the phone, offline.',
							time: '10',
							points: 'double',
							answers: [
								{ answer: 'True', right: true },
								{ answer: 'False', right: false }
							]
						},
						{
							type: QuizQuestionType.WORD_CLOUD,
							question: 'One word for the future of beauty?',
							time: '30',
							points: 'none',
							answers: []
						},
						{
							type: QuizQuestionType.CHECK,
							question: 'Which of these are <b>L’Oréal</b> tech brands?',
							time: '30',
							answers: [
								{ answer: 'Perso', right: true },
								{ answer: 'Modiface', right: true },
								{ answer: 'Photoshop', right: false },
								{ answer: '', right: false }
							]
						},
						{
							type: QuizQuestionType.VOTING,
							question: 'Which demo should we show next?',
							time: '20',
							answers: [
								{ answer: 'Virtual try-on' },
								{ answer: 'Skin genius' },
								{ answer: 'Hair colour AI' }
							]
						},
						{
							type: QuizQuestionType.ORDER,
							question: 'Put these launches in order, oldest first',
							time: '30',
							answers: [
								{ answer: 'Modiface acquisition', id: 0 },
								{ answer: 'Perso unveiled', id: 1 },
								{ answer: 'Brow Magic', id: 2 }
							]
						},
						{
							type: QuizQuestionType.TEXT,
							question: 'Which city hosts the India Tech Hub?',
							time: '20',
							answers: [
								{ answer: 'Bengaluru', case_sensitive: false },
								{ answer: 'Bangalore', case_sensitive: false }
							]
						},
						{
							type: QuizQuestionType.RANGE,
							question: 'How many engineers work at the hub?',
							time: '20',
							points: 'none',
							answers: { min: 0, max: 20, min_correct: 8, max_correct: 12 }
						},
						{
							type: QuizQuestionType.SLIDE,
							question: 'Break',
							time: '60',
							answers: ''
						}
					]
				}
	);
	let quiz_id: string | null = $state(null);
</script>

<Editor bind:data bind:quiz_id />
