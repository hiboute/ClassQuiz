<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!--
	Player phone: one state machine over the game's socket events.
	join -> waiting -> get ready -> answer -> locked in -> result -> ... -> end.
	The state lives here, so a socket reconnect (rejoin_game) keeps the screen
	the player is on; an answer sent while offline is sent again after rejoin.
-->
<script lang="ts">
	import { onDestroy, onMount } from 'svelte';
	import { socket } from '$lib/socket';
	import Cookies from 'js-cookie';
	import type { PlayGamePlayer, ReturnQuestion, SetQuestionNumber } from '$lib/quiz_types';
	import JoinGame from '$lib/play/join.svelte';
	import Waiting from '$lib/play/title.svelte';
	import Question from '$lib/play/question.svelte';
	import EndScreen from '$lib/play/end.svelte';
	import GetReady from '$lib/play/phone/GetReady.svelte';
	import Result from '$lib/play/phone/Result.svelte';
	import PausedOverlay from '$lib/play/phone/PausedOverlay.svelte';
	import Kicked from '$lib/play/phone/Kicked.svelte';
	import ConnectionBanner from '$lib/play/phone/ConnectionBanner.svelte';
	import PhoneShell from '$lib/play/phone/PhoneShell.svelte';
	import { navbarVisible } from '$lib/stores.svelte.ts';
	import {
		haptic,
		type AnswerPayload,
		type GetReadyData,
		type LockedAnswer,
		type OwnResult,
		type PodiumData,
		type RankUpdate
	} from '$lib/play/phone/phone';

	interface Props {
		data: any;
	}

	let { data }: Props = $props();
	// svelte-ignore state_referenced_locally
	let game_pin: string = $state(data.game_pin ?? '');
	let game_mode: any = $state();
	let username = $state('');

	navbarVisible.visible = false;

	type PlayerGame = PlayGamePlayer & { question_count?: number };

	// ---------- state ----------
	let gameData: PlayerGame | undefined = $state();
	let started = $state(false);
	let question_count: number | undefined = $state();
	let connected = $state(true);
	let rejoining = $state(false);
	let kicked = $state(false);
	let game_over = $state(false);
	let podium: PodiumData | null = $state(null);
	let join_notice = $state('');
	let rejoin_token = '';

	let get_ready: GetReadyData | null = $state(null);
	let get_ready_at = $state(0);

	let question: ReturnQuestion | undefined = $state();
	let question_index: number | null = $state(null);
	let deadline = $state(0);
	let paused = $state(false);
	let paused_remaining: number | null = $state(null);
	let time_up = $state(false);
	let locked: LockedAnswer | null = $state(null);
	let last_payload: AnswerPayload | null = null;
	let answer_error = $state('');

	let results_open = $state(false);
	let own_result: OwnResult | null = $state(null);
	let rank: RankUpdate | null = $state(null);
	let prev_rank: number | null = $state(null);
	let last_rank: number | null = $state(null);
	let total_score: number | null = $state(null);
	let total_before: number | null = $state(null);

	const question_type = $derived(String(question?.type ?? 'ABCD').toUpperCase());

	// ---------- small persistence (survives a reload of the page) ----------
	const store_key = () => `live-quiz:${game_pin}:${username}`;
	const save_progress = () => {
		try {
			sessionStorage.setItem(store_key(), JSON.stringify({ last_rank, total_score }));
		} catch {
			/* storage blocked */
		}
	};
	const load_progress = () => {
		try {
			const raw = sessionStorage.getItem(store_key());
			if (!raw) return;
			const v = JSON.parse(raw);
			if (typeof v.last_rank === 'number') last_rank = v.last_rank;
			if (typeof v.total_score === 'number') total_score = v.total_score;
		} catch {
			/* storage blocked */
		}
	};

	type JoinedCookie = { sid: string; username: string; game_pin: string; token?: string };
	const read_cookie = (): JoinedCookie | null => {
		try {
			const raw = Cookies.get('joined_game');
			return raw ? JSON.parse(raw) : null;
		} catch {
			return null;
		}
	};
	const write_cookie = () => {
		const value: JoinedCookie = { sid: socket.id ?? '', username, game_pin };
		if (rejoin_token) value.token = rejoin_token;
		Cookies.set('joined_game', JSON.stringify(value), {
			expires: 1 / 12 // two hours, like the game keys on the server
		});
	};

	const reset_question = () => {
		locked = null;
		last_payload = null;
		answer_error = '';
		time_up = false;
		paused = false;
		paused_remaining = null;
		results_open = false;
		own_result = null;
		rank = null;
	};

	// ---------- answering ----------
	const onanswer = (payload: AnswerPayload, lock: LockedAnswer) => {
		if (locked) return;
		const is_cloud = question_type === 'WORD_CLOUD';
		locked = { ...lock, pending: is_cloud };
		last_payload = payload;
		answer_error = '';
		socket.emit('submit_answer', payload);
		haptic(30);
	};

	// ---------- socket wiring ----------
	const handlers: Array<[string, (...args: any[]) => void]> = [];
	const on = (event: string, fn: (...args: any[]) => void) => {
		socket.on(event, fn);
		handlers.push([event, fn]);
	};

	let rejoin_timer: ReturnType<typeof setTimeout> | undefined;

	const try_rejoin = () => {
		const cookie = read_cookie();
		if (!cookie) {
			rejoining = false;
			return;
		}
		if (!gameData) {
			username = cookie.username;
			game_pin = cookie.game_pin;
			rejoining = true;
		}
		if (cookie.token) rejoin_token = cookie.token;
		socket.emit('rejoin_game', {
			old_sid: cookie.sid,
			username: cookie.username,
			game_pin: cookie.game_pin,
			rejoin_token: cookie.token
		});
		if (rejoin_timer) clearTimeout(rejoin_timer);
		rejoin_timer = setTimeout(() => {
			// No answer at all (old server): show the join form with a hint
			if (!gameData && rejoining) {
				rejoining = false;
				join_notice = 'We could not get you back into the game. Join again.';
			}
		}, 7000);
		fetch(`/api/v1/quiz/play/check_captcha/${cookie.game_pin}`)
			.then((r) => (r.ok ? r.json() : null))
			.then((json) => {
				if (json) game_mode = json.game_mode;
			})
			.catch(() => {});
	};

	on('connect', () => {
		connected = true;
		try_rejoin();
	});
	on('disconnect', () => {
		connected = false;
	});
	on('time_sync', (d) => socket.emit('echo_time_sync', d));

	const take_token = (d: any) => {
		if (d && typeof d.rejoin_token === 'string') rejoin_token = d.rejoin_token;
	};

	on('joined_game', (d: PlayerGame) => {
		take_token(d);
		join_notice = '';
		gameData = d;
		started = Boolean(d?.started);
		question_count = d?.question_count ?? question_count;
		if (d?.game_mode) game_mode = d.game_mode;
		write_cookie();
		load_progress();
		try {
			// eslint-disable-next-line no-undef
			(window as any).plausible?.('Joined Game', { props: { game_id: d?.game_id } });
		} catch {
			/* analytics optional */
		}
	});

	on('rejoined_game', (d: PlayerGame) => {
		if (rejoin_timer) clearTimeout(rejoin_timer);
		rejoining = false;
		join_notice = '';
		take_token(d);
		const first = !gameData;
		gameData = d;
		started = started || Boolean(d?.started);
		question_count = d?.question_count ?? question_count;
		if (d?.game_mode) game_mode = d.game_mode;
		write_cookie(); // the server now knows this socket's sid
		if (first) load_progress();
		// An answer sent while offline never reached the server: send it again.
		// If it did arrive, the server answers already_replied and nothing changes.
		if (locked && last_payload && !results_open && !time_up) {
			socket.emit('submit_answer', last_payload);
		}
	});

	// The server no longer knows this phone's place (expired, or the nickname
	// is held by another session): back to the join form with a clear message.
	on('rejoin_failed', (d: { reason?: string; message?: string }) => {
		if (rejoin_timer) clearTimeout(rejoin_timer);
		Cookies.remove('joined_game');
		rejoin_token = '';
		rejoining = false;
		reset_question();
		question = undefined;
		question_index = null;
		get_ready = null;
		gameData = undefined;
		started = false;
		join_notice =
			d?.message ||
			(d?.reason === 'game_not_found'
				? 'This game is over or no longer exists.'
				: 'We could not get you back into the game. Join again.');
	});

	on('start_game', () => {
		started = true;
	});

	on('get_ready', (d: GetReadyData) => {
		reset_question();
		question = undefined;
		question_index = null;
		get_ready = d;
		get_ready_at = Date.now();
		if (d?.question_count) question_count = d.question_count;
	});

	on('set_question_number', (d: SetQuestionNumber) => {
		if (!d || !d.question) return; // slides only go to the host
		started = true;
		const same = question_index === d.question_index && !results_open;
		if (!same) {
			reset_question();
			total_before = total_score;
		}
		question = d.question;
		question_index = d.question_index;
		get_ready = null;
		const extra = d as SetQuestionNumber & { remaining?: number; already_answered?: boolean };
		if (typeof extra.remaining === 'number') {
			// Sent to a phone that (re)joined mid-question: the time actually left
			deadline = Date.now() + Math.max(0, extra.remaining) * 1000;
		} else if (!same) {
			deadline = Date.now() + (Number(d.question.time) || 0) * 1000;
		}
		if (extra.already_answered && !locked) {
			locked = { label: '' };
		}
	});

	on('everyone_answered', () => {
		time_up = true;
	});
	on('solutions', () => {
		time_up = true;
	});

	on('game_paused', (d: { question_index?: number; remaining?: number }) => {
		paused = true;
		paused_remaining =
			typeof d?.remaining === 'number' ? d.remaining : Math.max(0, (deadline - Date.now()) / 1000);
	});
	on('game_resumed', (d: { question_index?: number; remaining?: number }) => {
		const remaining =
			typeof d?.remaining === 'number' ? d.remaining : (paused_remaining ?? 0);
		deadline = Date.now() + remaining * 1000;
		paused = false;
		paused_remaining = null;
	});

	on('question_results', (d: OwnResult[] | null) => {
		if (question_type === 'WORD_CLOUD' && question) return; // stays on "Sent"
		const list = Array.isArray(d) ? d : [];
		own_result = list.find((r) => r && r.username === username) ?? list[0] ?? null;
		results_open = true;
		paused = false;
		get_ready = null;
		if (own_result && own_result.right) haptic([30, 60, 30]);
		else haptic(90);
	});

	on('rank_update', (d: RankUpdate) => {
		if (question_type === 'WORD_CLOUD' && question) return;
		prev_rank = last_rank;
		rank = d;
		last_rank = d.rank;
		total_score = d.total;
		save_progress();
	});

	on('word_cloud_accepted', (d: { text?: string }) => {
		if (locked) locked = { ...locked, label: d?.text ?? locked.label, pending: false };
	});
	on('word_cloud_refused', (d: { message?: string }) => {
		locked = null;
		last_payload = null;
		answer_error = d?.message || 'This answer was refused. Try another one.';
	});
	on('already_replied', () => {
		if (locked) locked = { ...locked, pending: false };
	});
	on('question_not_active', (d: { reason?: string }) => {
		if (!locked) return;
		if (d?.reason === 'paused' || d?.reason === 'get_ready') {
			// Not open yet: let the player answer again once it is
			locked = null;
			last_payload = null;
			answer_error = 'Not open right now. Answer again when the timer runs.';
		} else {
			locked = null;
			last_payload = null;
			time_up = true;
		}
	});

	on('game_ended', () => {
		game_over = true;
	});
	on('final_results', () => {
		game_over = true;
		Cookies.remove('joined_game');
	});
	on('podium', (d: PodiumData) => {
		podium = d;
		game_over = true;
		Cookies.remove('joined_game');
	});

	on('kick', () => {
		kicked = true;
		Cookies.remove('joined_game');
		if (game_pin) Cookies.set('kicked', game_pin, { expires: 1 });
	});

	on('game_not_found', () => {
		if (read_cookie()) {
			Cookies.remove('joined_game');
			if (rejoining) join_notice = 'This game is over or no longer exists.';
			rejoining = false;
			gameData = undefined;
		}
	});

	onMount(() => {
		if (read_cookie() && !gameData) {
			rejoining = true;
			if (socket.connected) try_rejoin();
		}
	});

	onDestroy(() => {
		for (const [event, fn] of handlers) socket.off(event, fn);
		if (rejoin_timer) clearTimeout(rejoin_timer);
	});

	const confirmUnload = (event: BeforeUnloadEvent) => {
		if (gameData && !game_over && !kicked) {
			event.preventDefault();
			event.returnValue = '';
		}
	};
</script>

<svelte:window onbeforeunload={confirmUnload} />
<svelte:head>
	<title>India Tech Hub Live Quiz - Play</title>
	<meta name="theme-color" content="#170d43" />
</svelte:head>

<ConnectionBanner visible={!connected && Boolean(gameData) && !game_over && !kicked} />

{#if kicked}
	<Kicked />
{:else if game_over}
	<EndScreen {podium} {username} fallback_total={total_score} />
{:else if !gameData}
	{#if rejoining}
		<PhoneShell world="indigo" state="rejoining">
			<div class="pg-center" data-testid="rejoining">
				<span class="bt-eyebrow">One moment</span>
				<span class="bt-headline pg-headline">Getting you back in</span>
			</div>
		</PhoneShell>
	{:else}
		<JoinGame bind:game_pin bind:game_mode bind:username notice={join_notice} />
	{/if}
{:else if results_open}
	<Result
		question_index={question_index ?? 0}
		question_type={question?.type ?? 'ABCD'}
		own={own_result}
		{rank}
		{prev_rank}
		{locked}
		fallback_total={total_before}
	/>
{:else if question && question_index !== null}
	{#key question_index}
		<Question
			{question}
			{question_index}
			{question_count}
			{game_mode}
			{username}
			{total_score}
			{deadline}
			{paused}
			{paused_remaining}
			{time_up}
			{locked}
			{answer_error}
			{onanswer}
		/>
	{/key}
{:else if get_ready}
	{#key get_ready.question_index}
		<GetReady data={get_ready} {question_count} received_at={get_ready_at} />
	{/key}
{:else}
	<Waiting {username} title={gameData.title} {started} />
{/if}

{#if paused && !results_open && !game_over && !kicked && gameData}
	<PausedOverlay remaining={paused_remaining} />
{/if}

<style>
	.pg-center {
		margin: auto 0;
	}
	.pg-headline {
		margin-top: 8px;
		font-size: 40px;
	}
</style>
