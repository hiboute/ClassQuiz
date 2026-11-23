<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { socket } from '$lib/socket';
	import { getLocalization } from '$lib/i18n';
	import { navbarVisible } from '$lib/stores.svelte.ts';
	import HostScreen from '$lib/admin.svelte';
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { SocketGameControls } from '$lib/play/admin/socket_game_controls.ts';
	import type { HostPlayer, IGameState, ResultsView } from '$lib/play/admin/game_state.ts';
	import { QuizQuestionType, type PlayGame } from '$lib/quiz_types';
	import type { PlayerAnswer } from '$lib/admin';
	import { hostSound } from '$lib/play/host/sound.svelte';
	import {
		isGraded,
		type GetReadyData,
		type LeaderboardData,
		type PodiumData,
		type ResultEntry,
		type WordCount
	} from '$lib/play/host/worlds';

	navbarVisible.visible = false;

	const { t } = getLocalization();

	interface Props {
		data: { game_pin: string; game_token: string; auto_connect: boolean };
	}

	class GameState implements IGameState {
		public game_id: string;
		public players: HostPlayer[] = $state([]);
		public player_scores: Record<string, number> = $state({});
		public selected_question = $state(-1);
		public timer_res: string = $state(undefined);
		public question_results: ResultEntry[] | null | undefined = $state(null);
		public answer_count = $state(0);
		public player_count = $state(0);
		public shown_question_now = $state(-1);
		public final_results: Array<null> | Record<string, PlayerAnswer[]> = $state([null]);
		public game_started = $state(false);
		public quiz_data: PlayGame = $state(null);
		public control_visible = $state(true);
		public locked = $state(false);
		public get_ready: GetReadyData | null = $state(null);
		public paused = $state(false);
		public words: WordCount[] = $state([]);
		public leaderboard: LeaderboardData | null = $state(null);
		public previous_ranks: Record<string, number> | null = $state(null);
		public podium: PodiumData | null = $state(null);
		public results_view: ResultsView = $state('reveal');
		public toasts: { id: number; text: string }[] = $state([]);

		constructor(game_id: string) {
			this.game_id = game_id;
		}
	}

	let { data }: Props = $props();
	// the URL parameters do not change while the host screen is open
	const { auto_connect, game_token, game_pin } = (() => data)();
	let errorMessage = $state('');
	let success = $state(false);
	let warnToLeave = true;
	let export_token: string | undefined = $state(undefined);
	let results_saved = $state(false);
	let get_ready_on = $state(true);
	let show_full = $state(false);

	const socket_game_controls: SocketGameControls = new SocketGameControls(socket);
	let game_state: GameState = $state(new GameState(game_token));
	let timer_interval: ReturnType<typeof setInterval> | undefined;
	let toast_id = 0;

	const toast = (text: string) => {
		const id = ++toast_id;
		game_state.toasts = [...game_state.toasts.slice(-2), { id, text }];
		setTimeout(() => {
			game_state.toasts = game_state.toasts.filter((x) => x.id !== id);
		}, 4000);
	};

	const join_url = typeof window !== 'undefined' ? `${window.location.host}/play` : '/play';

	// ---------- timer ----------
	const stop_timer = () => {
		clearInterval(timer_interval);
		timer_interval = undefined;
	};
	const start_timer = (seconds: number) => {
		stop_timer();
		let left = Math.max(0, Math.ceil(seconds));
		game_state.timer_res = left.toString();
		timer_interval = setInterval(() => {
			if (game_state.timer_res === '0') {
				stop_timer();
				return;
			}
			left--;
			game_state.timer_res = Math.max(0, left).toString();
			if (left > 0 && left <= 5) hostSound.tick(left === 1);
			if (left <= 0) {
				hostSound.timeUp();
				stop_timer();
			}
		}, 1000);
	};

	const connect = async () => {
		socket.emit('register_as_admin', {
			game_pin: game_pin,
			game_id: game_token
		});
	};
	onMount(() => {
		if (auto_connect) {
			connect();
		}
		return () => stop_timer();
	});

	const load_players = async () => {
		try {
			const res = await fetch(`/api/v1/live/players?game_pin=${game_pin}&game_id=${game_token}`);
			if (!res.ok) return;
			const list: HostPlayer[] = await res.json();
			const known = new Set(game_state.players.map((p) => p.username));
			game_state.players = [
				...list.filter((p) => !known.has(p.username)),
				...game_state.players
			];
		} catch {
			/* the list fills from player_joined anyway */
		}
	};

	socket.on('registered_as_admin', (d: { game_id: string; game: PlayGame | string }) => {
		game_state.quiz_data = typeof d.game === 'string' ? JSON.parse(d.game) : d.game;
		success = true;
		load_players();
	});
	socket.on('already_registered_as_admin', () => {
		// eslint-disable-next-line @typescript-eslint/ban-ts-comment
		// @ts-ignore
		errorMessage = $t('admin_page.already_registered_as_admin');
	});
	socket.on('player_joined', (p: HostPlayer) => {
		if (game_state.players.some((x) => x.username === p.username)) return;
		game_state.players = [...game_state.players, { ...p, joined_at: Date.now() }];
		if (game_state.game_started) {
			toast(`${p.username} joined late`);
		} else {
			hostSound.blip();
		}
	});
	socket.on('game_lock_state', (d: { locked: boolean }) => {
		game_state.locked = !!d?.locked;
	});
	socket.on('start_game', () => {
		game_state.game_started = true;
	});
	socket.on('control_visibility', (d: { visible: boolean }) => {
		game_state.control_visible = d.visible;
	});

	socket.on('get_ready', (d: GetReadyData) => {
		stop_timer();
		game_state.get_ready = d;
		game_state.question_results = null;
		game_state.results_view = 'reveal';
		game_state.paused = false;
		game_state.words = [];
	});
	socket.on('set_question_number', (d: { question_index: number }) => {
		const i = Number(d.question_index);
		game_state.get_ready = null;
		game_state.question_results = null;
		game_state.results_view = 'reveal';
		game_state.paused = false;
		game_state.words = [];
		game_state.shown_question_now = i;
		game_state.selected_question = i;
		game_state.answer_count = 0;
		const q = game_state.quiz_data.questions[i];
		if (q?.type === QuizQuestionType.SLIDE) {
			stop_timer();
			game_state.timer_res = '0';
			return;
		}
		start_timer(Number(q?.time ?? 0));
	});
	socket.on('player_answer', (d: { answer_count?: number; player_count?: number }) => {
		if (typeof d?.answer_count === 'number') game_state.answer_count = d.answer_count;
		else game_state.answer_count += 1;
		if (typeof d?.player_count === 'number') game_state.player_count = d.player_count;
	});
	socket.on('everyone_answered', () => {
		stop_timer();
		game_state.timer_res = '0';
	});
	socket.on('solutions', () => {
		stop_timer();
		game_state.timer_res = '0';
	});
	socket.on('game_paused', (d: { remaining: number }) => {
		stop_timer();
		game_state.paused = true;
		game_state.timer_res = Math.ceil(d?.remaining ?? 0).toString();
	});
	socket.on('game_resumed', (d: { remaining: number }) => {
		game_state.paused = false;
		start_timer(d?.remaining ?? 0);
	});
	socket.on('pause_refused', (d: { reason: string }) => {
		const why: Record<string, string> = {
			get_ready: 'Wait for the question to open',
			no_open_question: 'No question is open',
			already_paused: 'Already paused',
			not_paused: 'Not paused'
		};
		toast(why[d?.reason] ?? 'Pause refused');
	});
	socket.on('word_cloud_update', (d: { question_index: number; words: WordCount[] }) => {
		if (Number(d?.question_index) === game_state.selected_question) {
			game_state.words = d.words ?? [];
		}
	});
	socket.on('question_results', (d: ResultEntry[] | string) => {
		let list: ResultEntry[] = [];
		try {
			list = typeof d === 'string' ? JSON.parse(d) : (d ?? []);
		} catch {
			list = [];
		}
		stop_timer();
		game_state.paused = false;
		game_state.timer_res = '0';
		game_state.question_results = list;
		game_state.results_view = 'reveal';
		const scores = { ...game_state.player_scores };
		for (const r of list) scores[r.username] = (scores[r.username] ?? 0) + (Number(r.score) || 0);
		game_state.player_scores = scores;
		const q = game_state.quiz_data.questions[game_state.selected_question];
		if (q?.hide_results !== true) hostSound.reveal();
		// With a remote in charge, nobody clicks here: move on to the leaderboard by itself.
		if (!game_state.control_visible && isGraded(q)) {
			const at = game_state.selected_question;
			setTimeout(() => {
				if (game_state.selected_question === at && game_state.question_results !== null) {
					game_state.results_view = 'leaderboard';
				}
			}, 7000);
		}
	});
	socket.on('leaderboard', (d: LeaderboardData) => {
		if (game_state.leaderboard && game_state.leaderboard.question_index !== d.question_index) {
			const ranks: Record<string, number> = {};
			game_state.leaderboard.top.forEach((e, i) => (ranks[e.username] = i + 1));
			game_state.previous_ranks = ranks;
		}
		game_state.leaderboard = d;
	});
	socket.on('game_ended', () => {
		stop_timer();
		game_state.get_ready = null;
		game_state.paused = false;
	});
	socket.on('final_results', (d) => {
		stop_timer();
		game_state.timer_res = '0';
		game_state.get_ready = null;
		game_state.final_results = d && typeof d === 'object' && !Array.isArray(d) ? d : [];
	});
	socket.on('podium', (d: PodiumData) => {
		game_state.podium = d;
	});
	socket.on('export_token', (token: string) => {
		warnToLeave = false;
		export_token = token;
		setTimeout(() => {
			warnToLeave = true;
		}, 200);
	});
	socket.on('results_saved_successfully', () => {
		results_saved = true;
	});

	const confirmUnload = (event: BeforeUnloadEvent) => {
		if (warnToLeave && game_state.game_started) {
			event.preventDefault();
			event.returnValue = '';
		}
	};

	const request_answer_export = (e: Event) => {
		e.preventDefault();
		socket.emit('get_export_token');
	};
	const save_quiz = () => {
		socket.emit('save_quiz');
	};

	// ---------- flow ----------
	const questions = $derived(game_state.quiz_data?.questions ?? []);
	const current = $derived(questions[game_state.selected_question]);
	const is_last = $derived(game_state.selected_question + 1 >= questions.length);
	const finished = $derived(
		game_state.podium !== null ||
			JSON.stringify(game_state.final_results) !== JSON.stringify([null])
	);

	const next_question = () =>
		socket_game_controls.set_question_number(game_state.selected_question + 1);
	const to_next = () => (is_last ? socket_game_controls.get_final_results() : next_question());
	const show_results = () =>
		socket_game_controls.get_question_results(game_token, game_state.shown_question_now);

	const primary = $derived.by((): { label: string; action: () => void } | null => {
		if (!game_state.game_started || finished || game_state.get_ready) return null;
		const nextLabel = is_last ? 'Final results' : `Question ${game_state.selected_question + 2}`;
		if (game_state.selected_question === -1) return { label: 'Question 1', action: next_question };
		if (!current) return null;
		if (current.type === QuizQuestionType.SLIDE) return { label: nextLabel, action: to_next };
		if (game_state.question_results !== null) {
			if (
				game_state.results_view === 'reveal' &&
				current.hide_results !== true &&
				isGraded(current) &&
				game_state.leaderboard
			) {
				return { label: 'Leaderboard', action: () => (game_state.results_view = 'leaderboard') };
			}
			return { label: nextLabel, action: to_next };
		}
		if (game_state.timer_res !== '0') {
			return {
				label: 'Skip timer',
				action: () => {
					socket_game_controls.show_solutions();
					stop_timer();
					game_state.timer_res = '0';
				}
			};
		}
		if (current.hide_results === true) {
			return {
				label: nextLabel,
				action: () => {
					show_results();
					setTimeout(to_next, 200);
				}
			};
		}
		return { label: 'Show results', action: show_results };
	});

	const toggle_pause = () => {
		if (game_state.paused) socket_game_controls.resume_game();
		else socket_game_controls.pause_game();
	};

	const on_key = (e: KeyboardEvent) => {
		const el = e.target as HTMLElement | null;
		if (el?.closest('input, textarea, select, button, a, [contenteditable="true"]')) return;
		if (e.key === ' ' || e.key === 'Enter') {
			if (primary) {
				e.preventDefault();
				primary.action();
			}
		} else if ((e.key === 'p' || e.key === 'P') && game_state.game_started && !finished) {
			if (current && current.type !== QuizQuestionType.SLIDE && game_state.question_results === null) {
				toggle_pause();
			}
		}
	};

	// right answers per player, for the podium line
	const rights = $derived.by(() => {
		const fr = game_state.final_results;
		if (!fr || Array.isArray(fr)) return null;
		const out: Record<string, number> = {};
		for (const list of Object.values(fr)) {
			for (const a of list ?? []) {
				if (String(a.right) === 'true') out[a.username] = (out[a.username] ?? 0) + 1;
			}
		}
		return out;
	});
	const full_ranking = $derived(
		Object.entries(game_state.player_scores).sort((a, b) => b[1] - a[1])
	);
</script>

<svelte:window onbeforeunload={confirmUnload} onkeydown={on_key} />
<svelte:head>
	<title>India Tech Hub Live Quiz - Host</title>
</svelte:head>

{#if !success}
	<div class="host-wait" data-world="indigo">
		{#if errorMessage !== ''}
			<p class="host-error">{errorMessage}</p>
		{:else if !auto_connect}
			<p>Open the host screen from your dashboard to start a game.</p>
		{:else}
			<p>Connecting to the game</p>
		{/if}
	</div>
{:else}
	<HostScreen
		{game_state}
		{game_pin}
		{join_url}
		cqc_code={page.url.searchParams.get('cqc_code') === 'null'
			? null
			: page.url.searchParams.get('cqc_code')}
		{get_ready_on}
		{primary}
		{rights}
		actions={{
			start: () => socket_game_controls.start_game(get_ready_on ? 3 : 0),
			kick: (username) => {
				game_state.players = socket_game_controls.kick_player(username, game_state.players);
			},
			toggleLock: () =>
				game_state.locked ? socket_game_controls.unlock_game() : socket_game_controls.lock_game(),
			toggleGetReady: () => (get_ready_on = !get_ready_on),
			pause: () => socket_game_controls.pause_game(),
			resume: () => socket_game_controls.resume_game(),
			end: () => socket_game_controls.end_game_now()
		}}
	>
		{#snippet podium_actions()}
			<button class="bt-btn-ghost host-act" onclick={() => (show_full = !show_full)}
				>{show_full ? 'Hide full results' : 'Full results'}</button
			>
			{#if export_token === undefined}
				<button class="bt-btn-ghost host-act" onclick={request_answer_export}
					>{$t('admin_page.request_export_results')}</button
				>
			{:else}
				<a
					class="bt-btn-primary host-act"
					target="_blank"
					href="/api/v1/quiz/export_data/{export_token}?ts={new Date().getTime()}&game_pin={game_pin}"
					>{$t('admin_page.download_export_results')}</a
				>
			{/if}
			<button class="bt-btn-ghost host-act" onclick={save_quiz} disabled={results_saved}>
				{results_saved ? 'Results saved' : $t('admin_page.save_results')}
			</button>
		{/snippet}
	</HostScreen>
	{#if show_full}
		<div class="host-full" role="dialog" aria-label="Full results">
			<div class="host-full__card bt-glass-deep">
				<div class="host-full__head">
					<span class="bt-eyebrow">Full results, {full_ranking.length} players</span>
					<button class="bt-btn-ghost" onclick={() => (show_full = false)}>Close</button>
				</div>
				<ol class="host-full__list">
					{#each full_ranking as [name, score], i}
						<li>
							<span class="bt-num host-full__rank">{i + 1}</span>
							<span class="host-full__name">{name}</span>
							<span class="bt-num">{Math.round(score)}</span>
						</li>
					{/each}
				</ol>
			</div>
		</div>
	{/if}
{/if}

<style>
	.host-wait {
		min-height: 100dvh;
		display: grid;
		place-items: center;
		background: var(--ground);
		color: var(--ink);
		font-size: 22px;
		padding: 16px;
		text-align: center;
	}
	.host-error {
		color: var(--accent-orchid-tint);
	}
	:global(.host-act) {
		min-height: 48px;
		font-size: 15px;
		letter-spacing: 2px;
	}
	.host-full {
		position: fixed;
		inset: 0;
		z-index: 50;
		display: grid;
		place-items: center;
		background: rgba(10, 5, 31, 0.7);
		padding: 16px;
	}
	.host-full__card {
		width: min(760px, 100%);
		max-height: 86dvh;
		display: flex;
		flex-direction: column;
		border-radius: 25px;
		padding: 24px 28px;
		color: var(--ink);
	}
	.host-full__head {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 12px;
		margin-bottom: 12px;
	}
	.host-full__list {
		list-style: none;
		margin: 0;
		padding: 0;
		overflow-y: auto;
	}
	.host-full__list li {
		display: grid;
		grid-template-columns: 56px 1fr auto;
		align-items: center;
		gap: 12px;
		padding: 10px 4px;
		font-size: 20px;
	}
	.host-full__list li + li {
		box-shadow: 0 -1px 0 var(--fill-glass);
	}
	.host-full__rank {
		font-size: 26px;
		text-align: center;
	}
	.host-full__name {
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
</style>
