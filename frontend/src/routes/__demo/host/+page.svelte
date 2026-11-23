<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!--
	Dev-only: every host screen state with fake data, for screenshots.
	/__demo/host?s=lobby | intro | getready | question | question-image | paused |
	cloud | text | range | order | reveal | reveal-check | poll | reveal-text |
	reveal-range | reveal-order | reveal-cloud | leaderboard | podium
	Add &live=1 to keep animations and countdowns running.
-->
<script lang="ts">
	import { page } from '$app/state';
	import QRCode from 'qrcode';
	import HostScreen from '$lib/admin.svelte';
	import { navbarVisible } from '$lib/stores.svelte.ts';
	import type { IGameState } from '$lib/play/admin/game_state';
	import type { PlayGame, Question } from '$lib/quiz_types';
	import { QuizQuestionType } from '$lib/quiz_types';
	import type { ResultEntry, WordCount } from '$lib/play/host/worlds';

	navbarVisible.visible = false;

	const s = page.url.searchParams.get('s') ?? 'lobby';
	const live = page.url.searchParams.get('live') === '1';

	const NAMES = [
		'Lipstick Llama', 'Mascara Maverick', 'Priya K', 'Serum Sorcerer', 'API Gateway Guru', 'Kenji',
		'Blush Byte', 'Ananya R', 'Kubernetes Kat', 'Glow Getter', 'Matteo B', 'Hair Data Hero',
		'Fatima Z', 'Velvet Vector', 'Lucas', 'Shade Matcher', 'Rohan 42', 'Event Stream Emma',
		'Chloé D', 'Foundation Finder', 'Aarav', 'Cloud Contour', 'Sofia M', 'Pixel Primer', 'Wei L'
	];
	const players = [
		...Array.from({ length: 123 }, (_, i) => ({ username: `Player ${i + 1}`, sid: `x${i}` })),
		...[...NAMES].reverse().map((username, i) => ({
			username,
			sid: `s${i}`,
			joined_at: i === NAMES.length - 1 ? Date.now() + 60_000 : 0
		}))
	];

	const abcd = (q: string, answers: [string, boolean][], extra: Partial<Question> = {}): Question => ({
		question: q,
		time: '20',
		type: QuizQuestionType.ABCD,
		answers: answers.map(([answer, right]) => ({ answer, right })),
		...extra
	});

	const questions: Question[] = [
		abcd('Which colour world opens the quiz?', [['Indigo', true], ['Teal', false], ['Violet', false], ['Cobalt', false]]),
		{ question: 'One word for Monday morning?', time: '30', type: 'WORD_CLOUD' as QuizQuestionType, answers: [] },
		abcd('Which of these are cloud providers?', [['Azure', true], ['Kafka', false], ['Google Cloud', true], ['Figma', false]], { type: QuizQuestionType.CHECK }),
		{ question: 'How many brands are in the group portfolio, roughly?', time: '20', type: QuizQuestionType.RANGE, answers: { min: 0, max: 100, min_correct: 35, max_correct: 40 } },
		{ question: 'Name the language most of our APIs are written in', time: '30', type: QuizQuestionType.TEXT, answers: [{ answer: 'Java', case_sensitive: false }, { answer: 'Kotlin', case_sensitive: false }] },
		{ question: 'Put these steps of a release in order', time: '30', type: QuizQuestionType.ORDER, answers: [{ answer: 'Commit' }, { answer: 'Build' }, { answer: 'Test' }, { answer: 'Deploy' }] },
		abcd('Which event streaming platform powers our real-time pipelines?', [['Apache Kafka', true], ['RabbitMQ', false], ['Amazon SQS', false], ['Redis Streams', false]], { image: 'demo' }),
		abcd('Which tech lets shoppers try a lipstick shade through the phone camera?', [['Augmented reality', true], ['Voice assistant', false], ['Blockchain ledger', false], ['Demand forecasting', false]]),
		{ question: 'Which session did you enjoy most today?', time: '20', type: QuizQuestionType.VOTING, answers: [{ answer: 'Keynote' }, { answer: 'API workshop' }, { answer: 'Data mesh panel' }, { answer: 'Hackathon demos' }] },
		abcd('True or false: the PIN changes for every game', [['True', true], ['False', false]]),
		abcd('What does EAI stand for?', [['Enterprise Architecture and Integration', true], ['Every API Integrated', false], ['Event And Insight', false], ['Edge AI', false]]),
		abcd('Last one: which city hosts the India Tech Hub?', [['Bengaluru', false], ['Pune', true], ['Mumbai', false], ['Chennai', false]])
	];

	const quiz = {
		quiz_id: 'demo',
		title: 'Beauty Tech trivia',
		description: 'Twelve questions on beauty, tech and the people who build it.',
		questions,
		game_id: 'demo',
		game_pin: '482913',
		started: true,
		user_id: 'demo',
		captcha_enabled: false,
		current_question: 0,
		question_show: false
	} as unknown as PlayGame;

	const answersFor = (qi: number, n: number): ResultEntry[] => {
		const q = questions[qi];
		const out: ResultEntry[] = [];
		const list = Array.isArray(q.answers) ? (q.answers as { answer: string; right?: boolean }[]) : [];
		for (let i = 0; i < n; i++) {
			const r = (i * 7919) % 100;
			let answer = '';
			let right = false;
			if ((q.type as string) === 'WORD_CLOUD') {
				answer = ['Coffee', 'Sleepy', 'Meetings', 'Chai', 'Deploy'][r % 5];
			} else if (q.type === QuizQuestionType.CHECK) {
				answer = r < 55 ? '02' : r < 75 ? '0' : r < 90 ? '012' : '3';
				right = answer === '02';
			} else if (q.type === QuizQuestionType.RANGE) {
				const v = Math.round(20 + ((r * 37) % 45));
				answer = String(v);
				right = v >= 35 && v <= 40;
			} else if (q.type === QuizQuestionType.TEXT) {
				answer = ['Java', 'java', 'Kotlin', 'Python', 'TypeScript', 'Go', 'Java', 'Scala'][r % 8];
				right = /^(java|kotlin)$/i.test(answer);
			} else if (q.type === QuizQuestionType.ORDER) {
				right = r < 46;
				answer = right ? 'Commit, Build, Test, Deploy' : 'Build, Commit, Test, Deploy';
			} else {
				const idx = r < 62 ? 0 : r < 78 ? 1 : r < 90 ? 2 : 3;
				const a = list[Math.min(idx, list.length - 1)];
				answer = a.answer;
				right = !!a.right;
			}
			out.push({ username: NAMES[i % NAMES.length] + (i >= NAMES.length ? ` ${i}` : ''), answer, right, time_taken: 800 + ((i * 433) % 15000), score: right ? 900 : 0 });
		}
		return out;
	};

	const cloud: WordCount[] = [
		['Coffee', 41], ['Sleepy', 28], ['Meetings', 22], ['Fresh start', 17], ['Traffic', 14],
		['Deploy', 12], ['Standup', 11], ['Emails', 10], ['Energy', 9], ['Chai', 9], ['Focus', 8],
		['Slow', 7], ['Rain', 6], ['Gym', 6], ['Music', 5], ['Hungry', 5], ['Plans', 4], ['Bugs', 4],
		['Sprint', 4], ['Calm', 3], ['Busy', 3], ['Motivated', 3], ['Snooze', 2], ['Podcast', 2],
		['Commute', 2], ['Pancakes', 2], ['Yoga', 1], ['Weekend recap', 1], ['Mango', 1], ['Excited', 1]
	].map(([text, count]) => ({ text: text as string, count: count as number }));

	let qr = $state('');
	QRCode.toDataURL('https://quiz.indiatechhub.xyz/play?pin=482913', { margin: 0, width: 600 }).then(
		(u: string) => (qr = u)
	);

	const qIndex: Record<string, number> = {
		question: 7, 'question-image': 6, paused: 7, cloud: 1, text: 4, range: 3, order: 5,
		reveal: 7, 'reveal-check': 2, poll: 8, 'reveal-text': 4, 'reveal-range': 3, 'reveal-order': 5,
		'reveal-cloud': 1, leaderboard: 7, getready: 7, tf: 9
	};
	const qi = qIndex[s] ?? 0;
	const isReveal = s.startsWith('reveal') || s === 'poll' || s === 'leaderboard';

	const game_state: IGameState = $state({
		game_id: 'demo',
		players: players,
		player_scores: { 'Mascara Maverick': 11460, 'Kubernetes Kat': 10920, 'Priya K': 10385 },
		selected_question: ['lobby', 'intro'].includes(s) ? -1 : qi,
		timer_res: isReveal ? '0' : s === 'paused' ? '9' : '17',
		question_results: isReveal ? answersFor(qi, 184) : null,
		answer_count: 184,
		player_count: 240,
		shown_question_now: qi,
		final_results: [null],
		game_started: s !== 'lobby',
		quiz_data: quiz,
		control_visible: page.url.searchParams.get('controls') !== '0',
		locked: page.url.searchParams.get('locked') === '1',
		get_ready:
			s === 'getready'
				? { question_index: 7, question_count: 12, title: questions[7].question, type: 'ABCD', points: 'double', seconds: 3 }
				: null,
		paused: s === 'paused',
		words: s === 'cloud' ? cloud.slice(0, 18) : s === 'reveal-cloud' ? cloud : [],
		leaderboard:
			s === 'leaderboard'
				? {
						question_index: 7,
						total_players: 240,
						top: [
							{ username: 'Mascara Maverick', score: 7480, gained: 1100 },
							{ username: 'Kubernetes Kat', score: 7310, gained: 850 },
							{ username: 'Priya K', score: 7105, gained: 1200 },
							{ username: 'Serum Sorcerer', score: 6890, gained: 0 },
							{ username: 'Velvet Vector', score: 6655, gained: 700 }
						]
					}
				: null,
		previous_ranks:
			s === 'leaderboard'
				? { 'Kubernetes Kat': 1, 'Mascara Maverick': 3, 'Serum Sorcerer': 2, 'Velvet Vector': 5 }
				: null,
		podium:
			s === 'podium'
				? {
						top: [
							{ rank: 1, username: 'Mascara Maverick', score: 11460 },
							{ rank: 2, username: 'Kubernetes Kat', score: 10920 },
							{ rank: 3, username: 'Priya K', score: 10385 }
						],
						total_players: 240
					}
				: null,
		results_view: s === 'leaderboard' ? 'leaderboard' : 'reveal',
		toasts: s === 'question' ? [{ id: 1, text: 'Wei L joined late' }] : []
	});

	// question image: a generated placeholder (no photo)
	if (s === 'question-image') {
		const c = document.createElement('canvas');
		c.width = 640;
		c.height = 360;
		const g = c.getContext('2d')!;
		const grad = g.createLinearGradient(0, 0, 640, 360);
		grad.addColorStop(0, '#0d458a');
		grad.addColorStop(1, '#5db5df');
		g.fillStyle = grad;
		g.fillRect(0, 0, 640, 360);
		g.fillStyle = '#feffff';
		g.font = '900 48px sans-serif';
		g.fillText('DIAGRAM', 220, 196);
		(questions[6] as Question).image = c.toDataURL();
	}

	const primary = $derived(
		s === 'lobby'
			? null
			: { label: isReveal ? (s === 'leaderboard' ? 'Question 9' : 'Leaderboard') : 'Skip timer', action: () => {} }
	);
</script>

{#if s !== 'lobby' || qr}
	<HostScreen
		{game_state}
		game_pin="482913"
		join_url="quiz.indiatechhub.xyz/play"
		{primary}
		frozen={!live}
		rights={{ 'Mascara Maverick': 11, 'Kubernetes Kat': 10, 'Priya K': 10 }}
		actions={{
			kick: (u) => (game_state.players = game_state.players.filter((p) => p.username !== u)),
			toggleLock: () => (game_state.locked = !game_state.locked),
			pause: () => (game_state.paused = true),
			resume: () => (game_state.paused = false)
		}}
		qr_src={qr}
	>
		{#snippet podium_actions()}
			<button class="bt-btn-ghost" style="min-height:48px">Full results</button>
			<button class="bt-btn-ghost" style="min-height:48px">Export results</button>
			<button class="bt-btn-ghost" style="min-height:48px">Save results</button>
		{/snippet}
	</HostScreen>
{/if}
