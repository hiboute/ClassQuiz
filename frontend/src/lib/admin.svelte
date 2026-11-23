<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!--
	The host big screen. Picks the phase from the game state (lobby, intro,
	get ready, question, reveal, leaderboard, podium) and draws it on the
	scaled stage in the right colour world. No socket code here: the admin page
	(and the demo route) fill `game_state` and pass the actions.
-->
<script module lang="ts">
	export interface HostActions {
		start?: () => void;
		kick?: (username: string) => void;
		toggleLock?: () => void;
		toggleGetReady?: () => void;
		pause?: () => void;
		resume?: () => void;
		end?: () => void;
	}
</script>

<script lang="ts">
	import type { Snippet } from 'svelte';
	import { fade } from 'svelte/transition';
	import { QuizQuestionType, type Question } from '$lib/quiz_types';
	import Spinner from '$lib/Spinner.svelte';
	import type { IGameState } from '$lib/play/admin/game_state';
	import HostStage from '$lib/play/host/HostStage.svelte';
	import HostControls from '$lib/play/host/HostControls.svelte';
	import HostLobby from '$lib/play/host/HostLobby.svelte';
	import HostIntro from '$lib/play/host/HostIntro.svelte';
	import HostGetReady from '$lib/play/host/HostGetReady.svelte';
	import HostQuestion from '$lib/play/host/HostQuestion.svelte';
	import HostReveal from '$lib/play/host/HostReveal.svelte';
	import HostLeaderboard from '$lib/play/host/HostLeaderboard.svelte';
	import HostPodium from '$lib/play/host/HostPodium.svelte';
	import HostToasts from '$lib/play/host/HostToasts.svelte';
	import { worldFor, type PodiumData } from '$lib/play/host/worlds';
	import type { World } from '$lib/brand/answers';

	interface Props {
		game_state: IGameState;
		game_pin: string;
		join_url: string;
		cqc_code?: string | null;
		get_ready_on?: boolean;
		primary?: { label: string; action: () => void; disabled?: boolean } | null;
		actions?: HostActions;
		/** export / save buttons under the podium */
		podium_actions?: Snippet;
		/** right answers per player for the podium line */
		rights?: Record<string, number> | null;
		/** demo: freeze animations and countdowns */
		frozen?: boolean;
		/** demo: QR image instead of the API one */
		qr_src?: string;
	}

	let {
		game_state,
		game_pin,
		join_url,
		cqc_code = null,
		get_ready_on = true,
		primary = null,
		actions = {},
		podium_actions,
		rights = null,
		frozen = false,
		qr_src
	}: Props = $props();

	const quiz = $derived(game_state.quiz_data);
	const total = $derived(quiz?.questions?.length ?? 0);
	const quizTitle = $derived(quiz?.title ? quiz.title.replace(/<[^>]*>/g, '') : '');
	const index = $derived(game_state.selected_question);
	const question = $derived<Question | undefined>(quiz?.questions?.[index]);
	const timeLeft = $derived(Math.max(0, parseInt(game_state.timer_res ?? '0') || 0));
	const ended = $derived(
		game_state.podium !== null ||
			JSON.stringify(game_state.final_results) !== JSON.stringify([null])
	);

	type Phase =
		| 'lobby'
		| 'intro'
		| 'get_ready'
		| 'slide'
		| 'question'
		| 'reveal'
		| 'leaderboard'
		| 'podium';

	const phase = $derived.by((): Phase => {
		if (ended) return 'podium';
		if (!game_state.game_started) return 'lobby';
		if (game_state.get_ready) return 'get_ready';
		if (index < 0 || !question) return 'intro';
		if (question.type === QuizQuestionType.SLIDE) return 'slide';
		if (game_state.question_results !== null && question.hide_results !== true) {
			if (game_state.results_view === 'leaderboard' && game_state.leaderboard) return 'leaderboard';
			return 'reveal';
		}
		return 'question';
	});

	const world = $derived.by((): World => {
		switch (phase) {
			case 'lobby':
			case 'intro':
				return 'indigo';
			case 'leaderboard':
				return 'midnight';
			case 'podium':
				return 'ultraviolet';
			case 'get_ready':
				return worldFor(game_state.get_ready?.question_index ?? 0);
			default:
				return worldFor(index);
		}
	});

	const stripIndex = $derived(
		phase === 'get_ready' ? (game_state.get_ready?.question_index ?? index) : index
	);
	const showStrip = $derived(
		phase === 'question' || phase === 'reveal' || phase === 'get_ready' || phase === 'slide'
	);
	const pageText = $derived(
		phase === 'podium'
			? 'Final'
			: phase === 'lobby' || phase === 'intro'
				? ''
				: `${stripIndex + 1} / ${total}`
	);

	const playerCount = $derived(
		game_state.player_count > 0 ? game_state.player_count : game_state.players.length
	);

	// Podium: from the server's `podium`, or from the summed scores as a fallback.
	const podiumData = $derived.by((): PodiumData => {
		if (game_state.podium) return game_state.podium;
		const sorted = Object.entries(game_state.player_scores ?? {}).sort((a, b) => b[1] - a[1]);
		return {
			top: sorted.slice(0, 3).map(([username, score], i) => ({ rank: i + 1, username, score })),
			total_players: sorted.length
		};
	});

	const canPause = $derived(phase === 'question' && (timeLeft > 0 || game_state.paused));
</script>

<HostStage
	{world}
	mesh={phase === 'leaderboard' || phase === 'podium'}
	page={game_state.control_visible ? undefined : pageText || undefined}
	strip={showStrip ? { count: total, current: stripIndex } : null}
>
	{#key phase + ':' + (phase === 'get_ready' ? game_state.get_ready?.question_index : index)}
		<div class="hs-phase" in:fade={{ duration: frozen ? 0 : 350 }}>
			{#if phase === 'lobby'}
				<HostLobby
					pin={game_pin}
					players={game_state.players}
					locked={game_state.locked}
					joinUrl={join_url}
					{quizTitle}
					questionCount={total}
					cqcCode={cqc_code}
					qrSrc={qr_src}
					canControl={game_state.control_visible}
					getReady={get_ready_on}
					onstart={actions.start}
					onkick={actions.kick}
					ontogglelock={actions.toggleLock}
					ontogglegetready={actions.toggleGetReady}
				/>
			{:else if phase === 'intro'}
				<HostIntro
					title={quiz.title}
					description={quiz.description}
					questionCount={total}
					playerCount={game_state.players.length}
				/>
			{:else if phase === 'get_ready' && game_state.get_ready}
				<HostGetReady data={game_state.get_ready} total={game_state.get_ready.question_count ?? total} {frozen} />
			{:else if phase === 'slide' && question}
				<div class="hs-slide">
					{#await import('$lib/play/admin/slide.svelte')}
						<Spinner my_20={false} />
					{:then c}
						<c.default {question} />
					{/await}
				</div>
			{:else if phase === 'question' && question}
				<HostQuestion
					{question}
					{quizTitle}
					{index}
					{total}
					{timeLeft}
					time={parseInt(question.time) || 0}
					answerCount={game_state.answer_count}
					{playerCount}
					paused={game_state.paused}
					words={game_state.words}
				/>
			{:else if phase === 'reveal' && question}
				<HostReveal
					{question}
					{quizTitle}
					{index}
					{total}
					results={game_state.question_results}
					words={game_state.words}
				/>
			{:else if phase === 'leaderboard' && game_state.leaderboard}
				<HostLeaderboard
					data={game_state.leaderboard}
					previous={game_state.previous_ranks}
					{total}
				/>
			{:else if phase === 'podium'}
				<HostPodium
					data={podiumData}
					{quizTitle}
					{rights}
					questionCount={total}
					instant={frozen}
					actions={game_state.control_visible ? podium_actions : undefined}
				/>
			{/if}
		</div>
	{/key}
	<HostToasts items={game_state.toasts} />

	{#snippet overlay()}
		{#if game_state.control_visible && phase !== 'lobby'}
			<HostControls
				page={pageText}
				{primary}
				paused={game_state.paused}
				{canPause}
				onpause={actions.pause}
				onresume={actions.resume}
				canEnd={phase !== 'podium'}
				onend={actions.end}
			/>
		{/if}
	{/snippet}
</HostStage>

<style>
	.hs-phase {
		position: absolute;
		inset: 0;
	}
	.hs-slide {
		position: absolute;
		inset: 60px 84px 120px;
		z-index: 3;
		display: flex;
		align-items: center;
		justify-content: center;
		overflow: hidden;
		border-radius: 25px;
	}
	.hs-slide :global(img) {
		max-width: 100%;
		max-height: 100%;
		object-fit: contain;
	}
</style>
