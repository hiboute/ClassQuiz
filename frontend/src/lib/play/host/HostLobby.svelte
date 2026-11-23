<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!--
	Lobby on the big screen (indigo world): PIN, QR, join URL, live player
	count and nickname chips. The host kicks a player by clicking a chip.
-->
<script lang="ts">
	import { flip } from 'svelte/animate';
	import { fade, scale } from 'svelte/transition';
	import ControllerCodeDisplay from '$lib/components/controller/code.svelte';
	import { fitText } from './fit';

	interface LobbyPlayer {
		username: string;
		joined_at?: number;
	}

	interface Props {
		pin: string;
		players: LobbyPlayer[];
		locked: boolean;
		joinUrl: string;
		quizTitle?: string;
		questionCount?: number;
		cqcCode?: string | null;
		canControl?: boolean;
		/** QR image url; defaults to the API */
		qrSrc?: string;
		onstart?: () => void;
		onkick?: (username: string) => void;
		ontogglelock?: () => void;
		/** 3-2-1 "get ready" screen before each question */
		getReady?: boolean;
		ontogglegetready?: () => void;
	}

	let {
		pin,
		players,
		locked,
		joinUrl,
		quizTitle = '',
		questionCount = 0,
		cqcCode = null,
		canControl = true,
		qrSrc,
		onstart,
		onkick,
		ontogglelock,
		getReady = true,
		ontogglegetready
	}: Props = $props();

	let qrOpen = $state(false);
	let kickTarget: string | null = $state(null);
	let now = $state(Date.now());

	$effect(() => {
		const id = setInterval(() => (now = Date.now()), 1000);
		return () => clearInterval(id);
	});

	const pinText = $derived.by(() => {
		const p = String(pin ?? '');
		if (p.length === 8) return `${p.slice(0, 4)} ${p.slice(4)}`;
		return p.replace(/(\d{3})(?=\d)/g, '$1 ');
	});

	const urlParts = $derived.by(() => {
		const [host, ...rest] = joinUrl.split('/');
		return { host, path: rest.length ? '/' + rest.join('/') : '' };
	});

	// Newest first. Show as many chips as fit in the panel (estimated widths).
	const ordered = $derived([...players].reverse());
	const visible = $derived.by(() => {
		const width = 752;
		const maxRows = 7;
		let rows = 1;
		let x = 0;
		const out: LobbyPlayer[] = [];
		for (let i = 0; i < ordered.length; i++) {
			const w = Math.min(width, ordered[i].username.length * 12.5 + 56);
			if (x + w > width) {
				rows += 1;
				x = 0;
			}
			if (rows > maxRows) break;
			// keep room for the "and N more" chip on the last row
			if (rows === maxRows && i < ordered.length - 1 && x + w + 190 > width) break;
			out.push(ordered[i]);
			x += w + 12;
		}
		return out;
	});
	const more = $derived(players.length - visible.length);
</script>

<h1 class="h-title" style="width: 900px">
	<span class="h-kicker">
		{quizTitle ? `${quizTitle}, ` : ''}{questionCount}
		{questionCount === 1 ? 'question' : 'questions'}.
	</span>
	<span class="h-headline" style="font-size: 64px">Join from your phone</span>
</h1>

<div class="lb-pin">
	<span class="h-label lb-pin__label">Game PIN</span>
	<!-- Shrinks until the PIN fits its 900px column: never clipped, even with
	     an 8-digit PIN or a wider fallback font before the brand font loads. -->
	<div
		class="lb-pin__num h-num bt-text-display"
		use:fitText={{
			max: pinText.length <= 7 ? 204 : pinText.length <= 9 ? 172 : 150,
			min: 96,
			lines: 1,
			widthOnly: true,
			key: pinText
		}}
	>
		{pinText}
	</div>
</div>

<div class="lb-join">
	<button class="lb-qr" onclick={() => (qrOpen = true)} aria-label="Show the QR code larger">
		<img src={qrSrc ?? `/api/v1/utils/qr/${pin}`} alt="QR code to join the game" />
	</button>
	<div class="lb-join__text">
		<span class="h-label lb-join__label">Scan, or go to</span>
		<div class="lb-join__url" use:fitText={{ max: 40, min: 24, lines: 2, key: joinUrl }}>
			{urlParts.host}<wbr />{urlParts.path}
		</div>
		<div class="lb-join__hint">
			Enter the PIN, pick a nickname, and watch for your name on the right.
		</div>
		{#if cqcCode}
			<div class="lb-cqc">
				<span class="h-label lb-join__label">Controller code</span>
				<ControllerCodeDisplay code={cqcCode} />
			</div>
		{/if}
	</div>
</div>

<section class="lb-panel" aria-label="Players">
	<div class="lb-panel__head">
		<div class="lb-count">
			<div class="lb-count__num h-num">{players.length}</div>
			<span class="h-label lb-count__label"
				>{players.length === 1 ? 'Player in the room' : 'Players in the room'}</span
			>
		</div>
		{#if canControl}
			<div class="lb-actions">
				<button class="lb-start" onclick={() => onstart?.()} disabled={players.length < 1}
					>Start</button
				>
			</div>
		{:else if locked}
			<span class="lb-lock lb-lock--on">Room locked</span>
		{/if}
	</div>

	{#if locked}
		<p class="lb-locked-note" transition:fade>The room is locked: nobody new can join.</p>
	{/if}

	<div class="lb-names">
		{#each visible as player (player.username)}
			<span animate:flip={{ duration: 300 }} in:scale={{ start: 0.6, duration: 300 }}>
				{#if kickTarget === player.username}
					<span class="lb-name lb-name--kick">
						<span>Remove {player.username}?</span>
						<button
							class="lb-mini lb-mini--danger"
							onclick={() => {
								onkick?.(player.username);
								kickTarget = null;
							}}>Remove</button
						>
						<button class="lb-mini" onclick={() => (kickTarget = null)}>Keep</button>
					</span>
				{:else if canControl}
					<button
						class="lb-name"
						class:lb-name--new={player.joined_at && now - player.joined_at < 4000}
						onclick={() => (kickTarget = player.username)}
						title="Click to remove this player">{player.username}</button
					>
				{:else}
					<span
						class="lb-name"
						class:lb-name--new={player.joined_at && now - player.joined_at < 4000}
						>{player.username}</span
					>
				{/if}
			</span>
		{/each}
		{#if more > 0}
			<span class="lb-name lb-more">and {more} more</span>
		{/if}
		{#if players.length === 0}
			<p class="lb-empty">Waiting for the first player.</p>
		{/if}
	</div>
	{#if canControl}
		<div class="lb-foot">
				<div class="lb-toggles">
			<button
				class="lb-lock lb-lock--soft"
				class:lb-lock--set={getReady}
				onclick={() => ontogglegetready?.()}
				aria-pressed={getReady}
				title="A 3 second countdown before each question"
			>
				<span class="lb-dot" aria-hidden="true"></span>
				Get ready 3 s
			</button>
			<button
				class="lb-lock"
				class:lb-lock--on={locked}
				onclick={() => ontogglelock?.()}
				aria-pressed={locked}
			>
				<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true">
					<rect x="4" y="10.5" width="16" height="11" rx="2.5" fill="currentColor" />
					<path
						d={locked ? 'M7.5 10.5V7a4.5 4.5 0 0 1 9 0v3.5' : 'M7.5 10.5V7a4.5 4.5 0 0 1 8.8-1.3'}
						fill="none"
						stroke="currentColor"
						stroke-width="2.4"
						stroke-linecap="round"
					/>
				</svg>
				{locked ? 'Room locked' : 'Lock room'}
			</button>
			</div>
		</div>
	{/if}
</section>

{#if qrOpen}
	<button
		class="lb-qr-full"
		transition:fade={{ duration: 120 }}
		onclick={() => (qrOpen = false)}
		aria-label="Close the QR code"
	>
		<span class="lb-qr-full__card">
			<img src={qrSrc ?? `/api/v1/utils/qr/${pin}`} alt="QR code to join the game" />
		</span>
	</button>
{/if}

<style>
	.lb-pin {
		position: absolute;
		z-index: 3;
		left: 84px;
		top: 300px;
		width: 900px;
	}
	.lb-pin__label {
		font-weight: 700;
		font-size: 28px;
	}
	.lb-pin__num {
		margin-top: 26px;
		font-size: 220px;
		letter-spacing: 2px;
		white-space: nowrap;
		line-height: 1;
		padding-bottom: 6px;
		overflow: hidden;
	}
	.lb-join {
		position: absolute;
		z-index: 3;
		left: 84px;
		top: 610px;
		display: flex;
		gap: 40px;
		align-items: center;
	}
	.lb-qr {
		flex: none;
		width: 300px;
		height: 300px;
		border-radius: 25px;
		background: var(--ground-paper);
		padding: 26px;
		border: 0;
		cursor: zoom-in;
	}
	.lb-qr img {
		display: block;
		width: 100%;
		height: 100%;
	}
	.lb-join__text {
		width: 520px;
	}
	.lb-join__label {
		color: var(--ink-muted);
		font-size: 20px;
	}
	.lb-join__url {
		margin-top: 14px;
		font-size: 40px;
		font-weight: 900;
		text-transform: uppercase;
		line-height: 1.08;
		overflow-wrap: normal;
		word-break: keep-all;
	}
	.lb-join__hint {
		margin-top: 18px;
		font-size: 22px;
		color: var(--ink-muted);
	}
	.lb-cqc {
		margin-top: 18px;
	}
	.lb-panel {
		position: absolute;
		z-index: 3;
		left: 1010px;
		right: 70px;
		top: 64px;
		bottom: 120px;
		border-radius: 25px;
		background: var(--fill-deep);
		padding: 40px 44px;
		display: flex;
		flex-direction: column;
	}
	.lb-panel__head {
		display: flex;
		align-items: flex-end;
		justify-content: space-between;
		gap: 20px;
	}
	.lb-count__num {
		font-size: 150px;
	}
	.lb-count__label {
		white-space: nowrap;
		margin-top: 18px;
		font-size: 20px;
	}
	.lb-actions {
		display: flex;
		flex-direction: column;
		align-items: flex-end;
		gap: 14px;
	}
	.lb-start {
		height: 96px;
		min-width: 340px;
		border: 0;
		border-radius: 9999px;
		font-family: inherit;
		font-size: 36px;
		letter-spacing: 8px;
		font-weight: 900;
		text-transform: uppercase;
		color: var(--ink-dark);
		background: linear-gradient(90deg, var(--accent-sky) 0%, var(--accent-green) 100%);
		cursor: pointer;
	}
	.lb-start:hover {
		filter: brightness(1.08);
	}
	.lb-start:disabled {
		opacity: 0.45;
		cursor: not-allowed;
	}
	.lb-lock {
		display: inline-flex;
		align-items: center;
		gap: 10px;
		height: 48px;
		padding: 0 22px;
		border: 0;
		border-radius: 9999px;
		background: var(--fill-glass-mid);
		color: var(--ink);
		font-family: inherit;
		font-size: 18px;
		font-weight: 700;
		letter-spacing: 3px;
		text-transform: uppercase;
		white-space: nowrap;
		cursor: pointer;
	}
	.lb-lock:hover {
		background: var(--fill-glass-strong);
	}
	.lb-foot {
		margin-top: 20px;
	}
	.lb-toggles {
		display: flex;
		gap: 12px;
	}
	.lb-lock--soft {
		background: var(--fill-glass);
		color: var(--ink-muted);
	}
	.lb-lock--set {
		color: var(--ink);
	}
	.lb-dot {
		width: 14px;
		height: 14px;
		border-radius: 50%;
		background: var(--fill-glass-strong);
	}
	.lb-lock--set .lb-dot {
		background: var(--accent-green);
	}
	.lb-lock--on {
		background: linear-gradient(90deg, var(--accent-purple) 0%, var(--accent-orchid) 100%);
	}
	.lb-locked-note {
		margin: 22px 0 0;
		font-size: 22px;
		color: var(--accent-orchid-tint);
	}
	.lb-names {
		margin-top: 36px;
		display: flex;
		flex-wrap: wrap;
		gap: 14px 12px;
		align-content: flex-start;
		overflow: hidden;
		flex: 1;
	}
	.lb-name {
		height: 56px;
		display: inline-flex;
		align-items: center;
		gap: 12px;
		padding: 0 24px;
		border: 0;
		border-radius: 9999px;
		background: var(--fill-glass-mid);
		color: var(--ink);
		font-family: inherit;
		font-size: 24px;
		font-weight: 700;
		white-space: nowrap;
		max-width: 752px;
		overflow: hidden;
		text-overflow: ellipsis;
		transition: background 600ms ease;
	}
	button.lb-name {
		cursor: pointer;
	}
	button.lb-name:hover {
		background: var(--fill-glass-strong);
		text-decoration: line-through;
	}
	.lb-name--new {
		background: linear-gradient(
			90deg,
			var(--accent-indigo) 0%,
			var(--accent-purple) 50%,
			var(--accent-orchid) 100%
		);
	}
	.lb-name--kick {
		background: #5a1740;
		padding-right: 8px;
	}
	.lb-mini {
		height: 40px;
		padding: 0 16px;
		border: 0;
		border-radius: 9999px;
		background: var(--fill-glass-mid);
		color: var(--ink);
		font-family: inherit;
		font-size: 16px;
		font-weight: 700;
		letter-spacing: 2px;
		text-transform: uppercase;
		cursor: pointer;
	}
	.lb-mini--danger {
		background: #cf2c69;
	}
	.lb-more {
		color: var(--ink-muted);
		background: var(--fill-glass);
		font-weight: 400;
	}
	.lb-empty {
		margin: 8px 0 0;
		font-size: 24px;
		color: var(--ink-muted);
	}
	.lb-qr-full {
		position: absolute;
		inset: 0;
		z-index: 30;
		display: flex;
		align-items: center;
		justify-content: center;
		border: 0;
		background: rgba(10, 5, 31, 0.8);
		cursor: zoom-out;
	}
	.lb-qr-full__card {
		width: 860px;
		height: 860px;
		padding: 50px;
		border-radius: 36px;
		background: var(--ground-paper);
	}
	.lb-qr-full__card img {
		display: block;
		width: 100%;
		height: 100%;
	}
</style>
