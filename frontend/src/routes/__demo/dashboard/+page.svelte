<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!--
	Organiser pages with fake data: /__demo/dashboard?view=dashboard|start|login|
	results|result|view|explore|search|user|settings|error.
	API calls made from the browser (settings, search) need mocking (Playwright).
-->
<script lang="ts">
	import { page } from '$app/state';
	import { navbarVisible } from '$lib/stores.svelte';
	import Dashboard from '../../dashboard/+page.svelte';
	import Login from '../../account/login/+page.svelte';
	import Results from '../../results/+page.svelte';
	import Result from '../../results/[result_id]/+page.svelte';
	import View from '../../view/[quiz_id]/+page.svelte';
	import Explore from '../../explore/+page.svelte';
	import Search from '../../search/+page.svelte';
	import User from '../../user/[user_id]/+page.svelte';
	import Settings from '../../account/settings/+page.svelte';
	import ErrorPanel from '$lib/components/organiser/ErrorPanel.svelte';
	import StartGame from '$lib/dashboard/start_game.svelte';

	navbarVisible.visible = true;
	const view = page.url.searchParams.get('view') ?? 'dashboard';

	const q = (question: string, answers: [string, boolean][], time = '20') => ({
		question,
		time,
		type: 'ABCD',
		answers: answers.map(([answer, right]) => ({ answer, right }))
	});
	const questions = [
		q('Which team builds the Beauty Tech data platform?', [
			['Data Office', true],
			['Finance', false],
			['Supply chain', false],
			['Legal', false]
		]),
		q('What does API stand for?', [
			['Application Programming Interface', true],
			['Automated Process Integration', false],
			['Applied Pixel Index', false],
			['Advanced Product Inventory', false]
		]),
		q('Which shade finder uses augmented reality?', [
			['Virtual try-on', true],
			['Barcode scanner', false]
		]),
		{ ...q('Which of these are cloud providers?', [['Azure', true], ['GCP', true], ['Excel', false]]), type: 'CHECK' }
	];
	const quizzes = [
		{
			id: '6a1f6e64-0000-4000-8000-000000000001',
			title: 'Beauty Tech Trivia',
			description: 'Twelve questions on the tech behind our brands, for the India Tech Hub all-hands.',
			public: true,
			questions: [...questions, ...questions, ...questions],
			plays: 4,
			views: 31,
			likes: 3,
			dislikes: 0
		},
		{
			id: '6a1f6e64-0000-4000-8000-000000000002',
			title: 'Cloud and Integration Basics',
			description: '',
			public: false,
			questions: questions.slice(0, 3),
			plays: 0,
			views: 0
		},
		{
			id: '6a1f6e64-0000-4000-8000-000000000003',
			title: 'Welcome week: a very long quiz title that should wrap on two lines at most',
			description: 'Ice breaker for new joiners.',
			public: true,
			questions: [questions[0]],
			plays: 1,
			views: 5
		},
		{
			id: '6a1f6e64-0000-4000-8000-000000000004',
			title: 'Draft quiz',
			description: '',
			public: false,
			questions: [],
			plays: 0
		}
	];
	const names = ['Lipstick Llama', 'Mascara Maverick', 'Priya K', 'Serum Sorcerer', 'API Gateway Guru', 'Kenji', 'Blush Byte', 'Ananya R', 'Kubernetes Kat', 'Glow Getter', 'Matteo B', 'Hair Data Hero'];
	const player_scores = Object.fromEntries(names.map((n, i) => [n, String(9800 - i * 713)]));
	const answers = questions.map((qq) =>
		names.slice(0, 9).map((n, i) => ({
			username: n,
			answer: qq.answers[i % qq.answers.length].answer,
			right: qq.answers[i % qq.answers.length].right,
			time_taken: 1200 + i * 830,
			score: qq.answers[i % qq.answers.length].right ? 1000 - i * 40 : 0
		}))
	);
	const result = {
		id: 'r1',
		quiz: { id: quizzes[0].id },
		title: 'Beauty Tech Trivia',
		timestamp: '2026-11-20T15:42:00',
		note: 'Bangalore all-hands, afternoon session',
		player_scores,
		custom_field_data: {},
		answers,
		questions
	};
	const results = [
		result,
		{ ...result, id: 'r2', timestamp: '2026-11-12T11:05:00', note: null, player_scores: { a: '1', b: '2', c: '3' } },
		{ ...result, id: 'r3', title: 'Cloud and Integration Basics', quiz: { id: quizzes[1].id }, timestamp: '2026-10-30T09:30:00', note: null }
	];
	const hits = quizzes.slice(0, 3).map((qz) => ({ ...qz, user: 'chrobiche' }));

	let start_id: string | null = $state(quizzes[0].id);
</script>

{#if view === 'dashboard'}
	<Dashboard data={{ quizzes, quiztivities: [], email: 'demo@example.com' } as any} />
{:else if view === 'empty'}
	<Dashboard data={{ quizzes: [], quiztivities: [], email: 'demo@example.com' } as any} />
{:else if view === 'start'}
	<Dashboard data={{ quizzes, quiztivities: [], email: 'demo@example.com' } as any} />
	{#if start_id}
		<StartGame bind:quiz_id={start_id} quiz_title={quizzes[0].title} question_count={12} />
	{/if}
{:else if view === 'login'}
	<Login data={{ verified: false } as any} />
{:else if view === 'results'}
	<Results data={{ results } as any} />
{:else if view === 'result'}
	<Result data={{ results: result } as any} />
{:else if view === 'view'}
	<View data={{ quiz: { ...quizzes[0], user_id: { id: 'u1', username: 'chrobiche' } }, logged_in: true } as any} />
{:else if view === 'explore'}
	<Explore data={{ results: { hits } } as any} />
{:else if view === 'search'}
	<Search />
{:else if view === 'user'}
	<User data={{ user: { id: 'u1', username: 'chrobiche', created_at: '2026-01-10T10:00:00' }, quizzes: quizzes.slice(0, 3) } as any} />
{:else if view === 'settings'}
	<Settings />
{:else if view === 'error'}
	<ErrorPanel status={404} headline="Page not found" message="This page does not exist, or it moved. Check the address, or head back to a game." />
{/if}
