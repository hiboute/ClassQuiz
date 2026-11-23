<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!--
	Dev-only harness: every player phone state with fake data, for screenshots.
	/__demo/phone?s=join|waiting|getready|abcd|shapes|check|text|wordcloud|range|
	order|voting|slide|locked|timeup|paused|result|result-wrong|result-first|
	result-pending|end|end-top|end-wait|kicked|rejoining
-->
<script lang="ts">
	import { page } from '$app/state';
	import { navbarVisible } from '$lib/stores.svelte.ts';
	import JoinGame from '$lib/play/join.svelte';
	import Waiting from '$lib/play/title.svelte';
	import Question from '$lib/play/question.svelte';
	import EndScreen from '$lib/play/end.svelte';
	import GetReady from '$lib/play/phone/GetReady.svelte';
	import Result from '$lib/play/phone/Result.svelte';
	import PausedOverlay from '$lib/play/phone/PausedOverlay.svelte';
	import Kicked from '$lib/play/phone/Kicked.svelte';
	import ConnectionBanner from '$lib/play/phone/ConnectionBanner.svelte';
	import type { LockedAnswer } from '$lib/play/phone/phone';

	navbarVisible.visible = false;

	const s = $derived(page.url.searchParams.get('s') ?? 'join');

	let pin = $state('482913');
	let mode = $state('normal');
	let name = $state('Lipstick Llama');

	const abcd: any = {
		question: 'Which tech lets shoppers try a lipstick shade through the phone camera?',
		time: '20',
		type: 'ABCD',
		points: 'standard',
		answers: [
			{ answer: 'Augmented reality' },
			{ answer: 'Voice assistant' },
			{ answer: 'Blockchain ledger' },
			{ answer: 'Demand forecasting' }
		]
	};
	const q = (over: Record<string, unknown>): any => ({ ...abcd, ...over });
	const deadline = Date.now() + 17000;
	let locked: LockedAnswer | null = $state(null);
	const onanswer = (_p: unknown, l: LockedAnswer) => (locked = l);

	const own = {
		username: 'Lipstick Llama',
		answer: 'Augmented reality',
		right: true,
		time_taken: 3200,
		score: 840,
		streak: 3,
		streak_bonus: 200
	};
	const rank = {
		question_index: 7,
		rank: 12,
		total_players: 240,
		total: 6960,
		gained: 840,
		streak: 3,
		behind_username: 'Serum Sparrow',
		behind_gap: 60
	};
	const podium = {
		top: [
			{ rank: 1, username: 'Swift Otter', score: 9100 },
			{ rank: 2, username: 'Lipstick Llama', score: 8800 },
			{ rank: 3, username: 'Mascara Moth', score: 8650 }
		],
		total_players: 240,
		rank: 57,
		total: 5120
	};
</script>

{#if s === 'join'}
	<JoinGame bind:game_pin={pin} bind:game_mode={mode} bind:username={name} />
{:else if s === 'join-empty'}
	<JoinGame game_pin="" game_mode="normal" username="" />
{:else if s === 'waiting'}
	<Waiting username="Lipstick Llama" title="Beauty Tech trivia" />
{:else if s === 'getready'}
	<GetReady
		data={{ question_index: 7, title: abcd.question, type: 'ABCD', points: 'double', seconds: 3 }}
		question_count={12}
	/>
{:else if s === 'abcd' || s === 'shapes' || s === 'voting'}
	<Question
		question={q({ type: s === 'voting' ? 'VOTING' : 'ABCD' })}
		question_index={7}
		question_count={12}
		game_mode={s === 'shapes' ? 'shapes' : 'normal'}
		username="Lipstick Llama"
		total_score={6120}
		{deadline}
		{locked}
		{onanswer}
	/>
{:else if s === 'check'}
	<Question
		question={q({ type: 'CHECK', question: 'Which of these are L’Oréal Groupe brands?' })}
		question_index={2}
		question_count={12}
		username="Lipstick Llama"
		total_score={1840}
		{deadline}
		{locked}
		{onanswer}
	/>
{:else if s === 'text'}
	<Question
		question={q({ type: 'TEXT', question: 'Name the city where L’Oréal was founded.', answers: [] })}
		question_index={4}
		question_count={12}
		username="Lipstick Llama"
		total_score={3200}
		{deadline}
		{locked}
		{onanswer}
	/>
{:else if s === 'wordcloud'}
	<Question
		question={q({ type: 'WORD_CLOUD', question: 'One word for your first week at the hub?', answers: [] })}
		question_index={5}
		question_count={12}
		username="Lipstick Llama"
		total_score={3200}
		{deadline}
		{locked}
		answer_error={page.url.searchParams.get('err') ? 'Your answer must be at most 30 characters.' : ''}
		{onanswer}
	/>
{:else if s === 'range'}
	<Question
		question={q({
			type: 'RANGE',
			question: 'In which year did L’Oréal open its first research lab?',
			answers: { min: 1900, max: 2000 }
		})}
		question_index={1}
		question_count={12}
		username="Lipstick Llama"
		total_score={980}
		{deadline}
		{locked}
		{onanswer}
	/>
{:else if s === 'order'}
	<Question
		question={q({
			type: 'ORDER',
			question: 'Put these launches in order, oldest first.',
			answers: [
				{ answer: 'Hair dye' },
				{ answer: 'Sunscreen' },
				{ answer: 'Virtual try-on' },
				{ answer: 'Skin diagnosis app' }
			]
		})}
		question_index={3}
		question_count={12}
		username="Lipstick Llama"
		total_score={2450}
		{deadline}
		{locked}
		{onanswer}
	/>
{:else if s === 'slide'}
	<Question question={q({ type: 'SLIDE' })} question_index={6} question_count={12} username="Lipstick Llama" {deadline} {onanswer} />
{:else if s === 'locked'}
	<Question
		question={abcd}
		question_index={7}
		question_count={12}
		username="Lipstick Llama"
		total_score={6120}
		{deadline}
		locked={{ label: 'Augmented reality', index: 0 }}
		{onanswer}
	/>
{:else if s === 'timeup'}
	<Question question={abcd} question_index={7} question_count={12} username="Lipstick Llama" total_score={6120} deadline={Date.now() - 1000} {onanswer} />
{:else if s === 'paused'}
	<Question question={abcd} question_index={7} question_count={12} username="Lipstick Llama" total_score={6120} {deadline} paused paused_remaining={14.6} {onanswer} />
	<PausedOverlay remaining={14.6} />
{:else if s === 'reconnecting'}
	<Question question={abcd} question_index={7} question_count={12} username="Lipstick Llama" total_score={6120} {deadline} {onanswer} />
	<ConnectionBanner visible />
{:else if s === 'result'}
	<Result question_index={7} {own} {rank} prev_rank={17} locked={{ label: 'Augmented reality', index: 0 }} />
{:else if s === 'result-wrong'}
	<Result
		question_index={7}
		own={{ ...own, right: false, score: 0, answer: 'Voice assistant', streak: 0, streak_bonus: 0 }}
		rank={{ ...rank, rank: 19, gained: 0, streak: 0, total: 6120, behind_gap: 140 }}
		prev_rank={12}
		locked={{ label: 'Voice assistant', index: 1 }}
	/>
{:else if s === 'result-none'}
	<Result question_index={2} own={null} rank={{ ...rank, rank: 40, gained: 0, streak: 0 }} prev_rank={40} />
{:else if s === 'result-first'}
	<Result question_index={4} {own} rank={{ ...rank, rank: 1, behind_username: null, behind_gap: null }} prev_rank={3} locked={{ label: 'Paris', index: undefined }} />
{:else if s === 'result-pending'}
	<Result question_index={7} {own} rank={null} locked={{ label: 'Augmented reality', index: 0 }} fallback_total={6120} />
{:else if s === 'end'}
	<EndScreen {podium} username="Lipstick Llama" />
{:else if s === 'end-top'}
	<EndScreen podium={{ ...podium, rank: 2, total: 8800 }} username="Lipstick Llama" />
{:else if s === 'end-wait'}
	<EndScreen podium={null} username="Lipstick Llama" />
{:else if s === 'kicked'}
	<Kicked />
{/if}
